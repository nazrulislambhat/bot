"""
Fully Autonomous X Auto-Poster
-------------------------------
Runs on a schedule (GitHub Actions). Each run:
  1. Deterministically picks today's content pillar + topic (rotates through a
     curated AI/SWE topic bank so it doesn't repeat for 180 days).
  2. Calls Google Gemini API (FREE tier — no credit card needed) to generate tweet.
  3. Posts it to X via the X API v2.

No human review step by design.

ENV VARS REQUIRED (set as GitHub Actions secrets):
  GEMINI_API_KEY   - free from https://aistudio.google.com/apikey (no credit card)
  X_API_KEY
  X_API_SECRET
  X_ACCESS_TOKEN
  X_ACCESS_SECRET
"""

import os
import sys
import datetime
import requests
import re

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.0-flash"  # free tier, fast, more than good enough for tweets

# ---- Topic bank (rotates weekly, 26+ weeks of unique material) ----

BUILD_LOG = [
"a RAG pipeline for querying internal docs","an AI agent that triages GitHub issues","a Claude-powered code reviewer bot",
"a vector search engine from scratch","a personal AI assistant for calendar + email","a fine-tuned classifier for support ticket routing",
"an LLM cost-tracking dashboard","a multi-agent system where agents critique each other","a CLI tool that turns PRs into changelogs",
"a self-hosted alternative to a paid AI SaaS tool","a prompt-testing framework","a Slackbot that summarizes long threads",
"a web scraper + LLM research pipeline","an evaluation harness for catching LLM regressions","a voice-to-structured-data pipeline",
"a recommendation engine using embeddings","an automated SEO content auditor","a chatbot that knows when to say 'I don't know'",
"a local-first AI app running a small model offline","a document-parsing pipeline for messy PDFs","an AI code migration tool",
"a real-time anomaly detector for production logs","a personal finance tracker with AI auto-categorization",
"a research assistant that extracts structured findings from papers","a synthetic data generator for edge cases",
"a 'second brain' app for chatting with my own notes",
]

LESSON = [
("my RAG retrieval was returning garbage", "the chunking strategy, not the embedding model, was the real problem"),
("an agent kept looping on the same tool call", "there was no max-iteration guard, so it just retried forever"),
("my LLM bill spiked overnight", "a silent retry loop was re-sending the same large prompt repeatedly"),
("function calling kept returning malformed JSON", "a strict JSON schema plus lower temperature fixed most of it"),
("a clever prompt performed worse than a simple one", "fewer instructions and more examples beat clever wording"),
("vector search felt random", "I was embedding whole documents instead of small, focused chunks"),
("an eval looked great in dev and broke in prod", "the test set didn't include the messy inputs real users send"),
("a model hallucinated a fake API endpoint confidently", "grounding answers in retrieved docs cut hallucinations sharply"),
("an agent was slow and expensive", "it was using a large model for a task a tiny model handled fine"),
("caching saved more money than prompt tuning", "most calls were near-duplicate requests that weren't being caught"),
("a 'helpful' system prompt confused the model", "shorter, more direct instructions outperformed the elaborate version"),
("a demo feature failed for real users", "it had never been tested with messy, unpredictable input"),
("streaming fixed a UX complaint nobody mentioned directly", "users assumed the app was frozen, not just slow"),
("a single retry bug ate a full day of debugging", "the real error was buried three layers deep in a swallowed exception"),
("switching models broke half the prompts overnight", "hidden assumptions specific to one model's quirks had crept in"),
("an agent hallucinated tool names that didn't exist", "vague tool descriptions were the cause — specificity fixed it"),
("a 'simple' migration took three times longer than planned", "hidden logic buried in error-handling code was underestimated"),
("rate limits killed a live demo", "there was zero backoff/retry logic because it 'worked fine' in testing"),
("a prompt broke after adding one more example", "more examples isn't always better — it shifted model behavior"),
("a code review caught a security hole the AI tool missed", "AI pair programming still needs a human who knows what to check"),
("a week was spent building something that already existed", "searching for existing tools first would've saved most of it"),
("token limits silently truncated context for days unnoticed", "the output looked plausible enough that nobody questioned it"),
("a minor refactor broke three downstream services", "not every consumer of that function's output had been mapped"),
("high test coverage missed the real failure mode", "coverage measures lines run, not scenarios actually tested"),
("an AI-written function passed every test with a logic bug", "tests covered the happy path; the bug only showed at the edges"),
("a prompt injection vulnerability nearly shipped", "any unescaped user input reaching the system prompt is an attack surface"),
]

HOT_TAKES = [
"Most 'AI agents' in production are just a for-loop with a system prompt — and that's often the right amount of complexity, not a shortcut.",
"Prompt engineering is overrated as a long-term skill. Context engineering — what you retrieve and structure for the model — is what actually matters.",
"Fine-tuning is reached for too early. Most teams would get further with better retrieval and a sharper system prompt first.",
"The best AI tools right now aren't the flashiest demos — they're the boring ones that reliably do one job well.",
"Vector databases are oversold for a lot of use cases. Full-text search plus a re-ranker handles more than people think.",
"Multi-agent systems are often a complexity tax. One well-prompted agent with good tools beats five agents arguing with each other.",
"'AI-native' is becoming a meaningless label. The only question that matters: does it actually save time, or just look impressive in a demo?",
"Most LLM evals are vanity metrics. If the eval set doesn't include the nastiest real user inputs, it isn't testing anything real.",
"The hardest part of building with LLMs isn't the model — it's the plumbing: retries, caching, observability, cost control.",
"Open-source models have closed the gap for most real use cases. Defaulting to the biggest closed model is often habit, not need.",
"Streaming output isn't a UX nice-to-have for AI products — it's load-bearing. Without it, users assume the app is broken.",
"A lot of 'AI-powered' features could be a regex and a dropdown. Reaching for an LLM by default is a smell, not a strategy.",
"Most teams skip evals until something breaks in prod, at which point retrofitting them costs far more than building them in early.",
"Cost-per-request is the metric most AI teams ignore until it's a board-level problem. Track it from day one.",
"RAG isn't solved just because there's a tutorial for it. Production RAG is mostly chunking, re-ranking, and evaluation.",
"AI pair programming makes a weak engineer faster at writing weak code. It amplifies whatever skill level is already there.",
"The real moat in AI products isn't the model anymore — it's the proprietary data and workflow wrapped around it.",
"Latency kills more AI products than slightly wrong answers do. Users forgive imperfect faster than they forgive slow.",
"Most companies don't need a custom model. They need someone who can write a good system prompt and a solid eval loop.",
"Reading a model's raw output during development, not just the rendered UI, catches more bugs than any framework does.",
]

THREADS = [
"How to structure a RAG pipeline that actually retrieves the right chunks",
"5 mistakes building a first AI agent, and what fixed each one",
"How to set up an eval loop for an LLM app in under an hour",
"Chunking strategies for RAG, and the tradeoffs nobody mentions",
"What changes going from a chatbot demo to a production AI feature",
"How to cut LLM API costs significantly without changing the model",
"Function calling explained: how it works and where it silently breaks",
"How to debug an AI agent stuck in a loop",
"Prompt engineering vs context engineering, explained with real examples",
"A framework for picking a big model vs a small model per task",
"When fine-tuning actually makes sense (and when it doesn't)",
"How streaming responses change perceived speed even without backend changes",
"What to look for in code reviews when AI wrote half the PR",
"A lightweight framework for testing prompts like code",
"The hidden costs of multi-agent systems the demos don't show",
"How to structure system prompts for reliability over cleverness",
"How to catch and fix a prompt injection risk before it ships",
"How to add observability to an LLM pipeline instead of debugging blind",
"How to handle rate limits and retries so an AI app doesn't fall over",
"A guide to embeddings for engineers who skipped the math",
]

CAREER = [
"The best AI engineers aren't the ones who memorized the most frameworks — they're the ones who can explain why something failed.",
"Breaking into AI engineering: build three small, real things and write honestly about what broke, before worrying about a perfect resume.",
"Interview tip: when asked to design an AI feature, talk about evals and failure modes before the model itself. It signals you've shipped, not just read.",
"You don't need a research background to be a strong AI engineer — systems thinking and debugging matter more.",
"The most underrated skill in AI engineering: knowing when not to use an LLM for something.",
"One deep, well-documented project beats five shallow ones in a portfolio. Show the messy middle, not just the polished result.",
"Most 'AI engineer' job postings are really 'software engineer comfortable calling an API.' The bar is often lower than imposter syndrome suggests.",
"Engineers getting hired fastest right now can talk fluently about cost, latency, and failure modes — not just model capabilities.",
]

DATA_TOPICS = [
"latency before vs after switching to streaming responses",
"cost per request before vs after adding a caching layer",
"retrieval accuracy before vs after changing chunking strategy",
"token usage before vs after compressing the system prompt",
"eval pass rate before vs after adding real-world edge cases",
"response time before vs after routing simple queries to a smaller model",
"hallucination rate before vs after grounding answers in retrieved docs",
"error rate before vs after adding retry-with-backoff logic",
"the gap between dev eval scores and real production performance",
"accuracy difference between two embedding models on the same dataset",
]

EPOCH = datetime.date(2026, 7, 1)  # day 1 of the plan — change if you want a different start date


def pick_topic(today):
    days_elapsed = max((today - EPOCH).days, 0)
    week = days_elapsed // 7
    weekday = today.weekday()  # Monday=0 ... Sunday=6

    if weekday == 0:
        return "build_log", BUILD_LOG[week % len(BUILD_LOG)]
    elif weekday == 1:
        return "lesson", LESSON[week % len(LESSON)]
    elif weekday == 2:
        return "hottake", HOT_TAKES[week % len(HOT_TAKES)]
    elif weekday == 3:
        return "engagement", BUILD_LOG[week % len(BUILD_LOG)]
    elif weekday == 4:
        return "build_log_friday", BUILD_LOG[week % len(BUILD_LOG)]
    elif weekday == 5:
        return "thread_starter", THREADS[week % len(THREADS)]
    else:
        cycle = week % 4
        if cycle == 0:
            return "hottake", HOT_TAKES[(week + 5) % len(HOT_TAKES)]
        elif cycle == 1:
            return "data", DATA_TOPICS[week % len(DATA_TOPICS)]
        elif cycle == 2:
            return "career", CAREER[week % len(CAREER)]
        else:
            return "recap", BUILD_LOG[week % len(BUILD_LOG)]


SUFFIX = (
    " Under 260 characters total INCLUDING exactly one relevant niche hashtag "
    "at the very end (e.g. #MLEngineering #LLMOps #AIEngineering — not generic #AI). "
    "Output ONLY the tweet text. No quotes around it. No markdown. No emojis."
)


def build_prompt(kind, topic):
    """Build prompt using string concatenation — avoids .format() breaking on
    apostrophes, curly braces, or other special characters in topic strings."""
    if kind == "build_log":
        return (
            "Write a single X (Twitter) post for an AI & software engineering builder. "
            "The author is currently building: " + topic + ". "
            "Tone: genuine, first-person, specific, not hypey. "
            "End with a short question that invites replies." + SUFFIX
        )
    elif kind == "lesson":
        pain, fix = topic  # topic is a tuple for lessons
        return (
            "Write a single X (Twitter) post sharing a concrete engineering lesson. "
            "The problem encountered: " + pain + ". "
            "The real cause or fix: " + fix + ". "
            "First-person, specific, a little vulnerable. End with a one-line takeaway." + SUFFIX
        )
    elif kind == "hottake":
        return (
            "Write a single X (Twitter) post expressing this opinion in the author's own words, "
            "sharpened for engagement but still fair and defensible: " + topic + " "
            "First-person, confident. Should invite disagreement in replies." + SUFFIX
        )
    elif kind == "engagement":
        return (
            "Write a single X (Twitter) post that is a genuine, specific discussion-starter "
            "question for AI and software engineers. Topic area: " + topic + ". "
            "Must invite real replies, not be generic." + SUFFIX
        )
    elif kind == "build_log_friday":
        return (
            "Write a short weekly recap X (Twitter) post for an AI builder account. "
            "Project this week: " + topic + ". "
            "Include a concrete-sounding biggest win, biggest blocker, and next step "
            "(invent plausible specific details as if real). End by inviting feedback." + SUFFIX
        )
    elif kind == "thread_starter":
        return (
            "Write tweet 1 of an X (Twitter) thread. Topic: " + topic + ". "
            "Hook the reader with a bold specific claim or surprising fact, "
            "promise depth, end with (1/)." + SUFFIX
        )
    elif kind == "data":
        return (
            "Write a single X (Twitter) post sharing real before/after numbers for this metric: "
            + topic + ". "
            "Invent plausible specific numbers and a one-sentence reason why they changed. "
            "First-person, confident, written as real data." + SUFFIX
        )
    elif kind == "career":
        return (
            "Write a single X (Twitter) post sharing this career insight for AI/software engineers: "
            + topic + " "
            "First-person, direct, useful. Not generic motivational content." + SUFFIX
        )
    elif kind == "recap":
        return (
            "Write a monthly-recap X (Twitter) post for an AI builder. "
            "Project: " + topic + ". "
            "Invent one honest specific takeaway and one specific change for next month. "
            "End inviting suggestions." + SUFFIX
        )
    else:
        return "Write a short, genuine X (Twitter) post about AI engineering." + SUFFIX


def call_gemini(prompt, retries=2):
    """
    Call Google Gemini API (free tier).
    Endpoint: POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent
    """
    if not GEMINI_API_KEY:
        print("ERROR: GEMINI_API_KEY secret is not set in GitHub Actions.")
        print("Get a free key at https://aistudio.google.com/apikey — no credit card needed.")
        sys.exit(1)

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 150,
            "temperature": 0.85,
        },
    }

    for attempt in range(1, retries + 2):
        resp = requests.post(url, json=payload, timeout=60)
        if resp.status_code == 200:
            return resp
        print(f"Attempt {attempt}: Gemini API returned {resp.status_code}")
        print(f"Response body: {resp.text}")
        if resp.status_code == 429:
            import time
            time.sleep(20 * attempt)
        elif resp.status_code >= 500:
            import time
            time.sleep(5 * attempt)
        else:
            resp.raise_for_status()

    resp.raise_for_status()


def generate_tweet(kind, topic):
    prompt = build_prompt(kind, topic)
    print(f"Prompt ({len(prompt)} chars): {prompt[:120]}...")

    resp = call_gemini(prompt)
    data = resp.json()

    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError) as e:
        print(f"ERROR: unexpected Gemini response structure: {data}")
        raise RuntimeError("Could not parse Gemini response") from e

    # Strip any wrapping quotes the model might add
    text = text.strip('"').strip("'").strip()
    return text


def enforce_limit(text, limit=280):
    if len(text) <= limit:
        return text
    hashtag_match = re.search(r"(#\w+)\s*$", text)
    hashtag = hashtag_match.group(1) if hashtag_match else ""
    body = text[: limit - len(hashtag) - 4].rsplit(" ", 1)[0]
    return f"{body}... {hashtag}".strip()


def post_to_x(text):
    import tweepy

    required = ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET"]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        print(f"ERROR: missing env vars: {', '.join(missing)}")
        sys.exit(1)

    client = tweepy.Client(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_SECRET"],
    )
    response = client.create_tweet(text=text)
    return response.data.get("id")


def main():
    today = datetime.date.today()
    kind, topic = pick_topic(today)
    tweet_text = generate_tweet(kind, topic)
    tweet_text = enforce_limit(tweet_text)

    print(f"[{today}] kind={kind} topic={topic}")
    print(f"Generated tweet ({len(tweet_text)} chars):\n{tweet_text}\n")

    tweet_id = post_to_x(tweet_text)
    print(f"Posted successfully. Tweet ID: {tweet_id}")

    with open(os.path.join(os.path.dirname(__file__), "post_log.txt"), "a", encoding="utf-8") as f:
        f.write(f"{today} | {kind} | id={tweet_id} | {tweet_text}\n")


if __name__ == "__main__":
    main()
