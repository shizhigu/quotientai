<div align="center">

# CreatorOS

**A multi-agent backend that turns a creator's YouTube profile and a brand name into a full brand-deal analysis.**

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Google ADK](https://img.shields.io/badge/Google%20ADK-1.5.0-4285F4?logo=google&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)

</div>

---

## What it is

CreatorOS (repo name `quotientai`) is a FastAPI service that runs a pipeline of specialized AI agents to help independent creators price and negotiate brand deals. You give it a brand name and a creator's YouTube profile, and it returns brand research, a creator valuation score, floor/target/opening-quote pricing, a negotiation playbook, a ready-to-send HTML proposal email, and marketing contacts at the brand.

A separate video endpoint pulls audio from a YouTube URL, transcribes it with Deepgram, and asks an LLM to pick the best segments for short-form clips.

The idea behind it: creators usually negotiate against brand teams that have rate cards and benchmarks while the creator has none of that. This packages the research and pricing work into one API call.

## Agent design

The system is built on Google's Agent Development Kit (ADK). It is a real multi-agent setup, not a single prompt behind an endpoint.

The core deal flow is a `SequentialAgent` that chains seven `LlmAgent`s in a fixed order. Each agent writes its result to a shared session-state key (via ADK `output_key`), and later agents read the accumulated state through their prompts:

```
BrandIntelligence -> CreatorValueAssessment -> PricingStrategy ->
NegotiationIntelligence -> ProposalEmail -> EmailFinder -> FormatOutput
```

Models are picked per agent and all route through OpenRouter via LiteLLM: Gemini 2.0 Flash Lite for cheap extraction (format output), Gemini 2.5 Flash for the mid-weight steps (creator value, proposal email, email finder), Gemini 2.5 Pro for the negotiation reasoning, and Perplexity `sonar-reasoning-pro` for the two search-heavy steps (brand intelligence and pricing). The Perplexity steps get live web results from the model itself, not from a tool call. The idea is that each step gets the smallest model that still does the job.

Three agents call tools inside their own loop:

- The negotiation agent calls a native async Perplexity search function to check strategies against current market data. (The search tools were originally MCP subprocesses and were rewritten as plain async functions wrapped in ADK `LongRunningFunctionTool`.)
- The email finder calls Tavily to find the brand's domain, then Hunter.io to pull contacts. It searches the marketing department first and broadens to all departments if it finds fewer than three.
- The proposal email agent calls a small date tool so the generated email is dated correctly.

The final agent enforces a Pydantic `output_schema`, so the JSON handed to the frontend has a fixed shape.

Separate from the pipeline, a chat agent named Quokka answers follow-up questions in plain language. It runs on the same shared session, so it can reference a completed analysis. There is also a coordinator agent that uses the LLM to route between the chat agent and the pipeline, though the HTTP endpoints below call each path directly. All runners share one `DatabaseSessionService`, so state persists across the chat, deal, email, and video endpoints. When a deal analysis finishes, the result is also POSTed to a Supabase webhook for the frontend.

The autonomy here lives inside the tool-calling agents (negotiation, email finder, proposal email) and in the router. The top-level deal flow itself is a fixed sequence, not an open-ended planner.

## Endpoints

- `POST /custom/deal-analysis` runs the seven-agent pipeline.
- `POST /custom/chat` talks to Quokka over an existing session.
- `POST /custom/modify-email-template` re-saves an edited proposal email.
- `POST /custom/video/select-segments` runs the YouTube to Deepgram to segment-selection pipeline.
- `GET /custom/session/state` reads or creates session state.
- `GET /health` health check.

## Quick start

The service needs API keys for the models and tools it calls. Create a `.env` in the repo root:

```bash
OPENROUTER_API_KEY=...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
PERPLEXITY_API_KEY=...
TAVILY_API_KEY=...
HUNTER_IO_API_KEY=...
DEEPGRAM_API_KEY=...     # only for the video endpoint
SESSION_DB_URL=...       # database URL for session persistence (Postgres in the deployed setup)
SUPABASE_URL=...         # Supabase client is created at import, so both are read on startup
SUPABASE_KEY=...
```

Run it locally:

```bash
pip install -r requirements.txt
uvicorn creatoros.main:app --host 0.0.0.0 --port 8000
```

Or with Docker:

```bash
docker build -t creatoros .
docker run -p 8000:8000 --env-file .env creatoros
```

## Status

This is a working prototype and portfolio backend, not a hardened product. There is no test suite, no CI, and no frontend in this repo. Some agents (for example the PDF contract analyzer) exist in the code but are not wired into any endpoint yet. A few API keys are currently hardcoded in the source and should be moved to environment variables before any real deployment.

## License

No license file is included, so no usage rights are granted by default. Add a LICENSE if you want others to use it.
