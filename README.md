# CreatorOS (QuotientAI)

> AI-powered deal intelligence that gives independent creators the negotiation firepower of a top talent agency -- from a single API call.

## What is this?

CreatorOS is a multi-agent AI platform that analyzes brand partnerships for content creators. It takes a creator's YouTube profile and a brand name, then returns a complete deal intelligence package: brand research, creator valuation, dynamic pricing (floor/target/opening quote), a negotiation playbook with scripted responses, a ready-to-send HTML proposal, and verified marketing contacts at the brand. It also includes a video content pipeline that transcribes YouTube videos and selects the best segments for short-form repurposing.

## Why?

I was frustrated that independent creators routinely leave 25-40% of deal value on the table because they negotiate against professional brand teams with nothing but a gut feeling. Talent agencies solve this but charge 15-20% commission and ignore creators under 500K subscribers -- so I built a system to close that gap.

## How it works

The core is a **sequential agent pipeline** built on Google's Agent Development Kit (ADK). Seven specialized agents execute in strict order, each reading from and writing to a shared session state:

1. **BrandIntelligenceAgent** -- researches the brand via real-time web search (Perplexity)
2. **CreatorValueAssessmentAgent** -- scores the creator's audience and engagement
3. **PricingStrategyAgent** -- calculates floor/target/opening-quote pricing with live market data
4. **NegotiationIntelligenceAgent** -- generates a tactical playbook (Chris Voss + BATNA frameworks)
5. **ProposalEmailAgent** -- writes a persuasive, ready-to-send HTML proposal
6. **EmailFinderAgent** -- discovers verified marketing contacts via Hunter.io + Tavily
7. **FormatOutputAgent** -- validates and structures the final JSON for the frontend

A **CoordinatorAgent** routes requests to either the deal pipeline or a conversational chat agent (Quokka). Results are dispatched to Supabase via webhook for frontend sync.

## Key Technical Highlights

- **Per-agent model selection**: Each agent uses the cheapest LLM that reliably performs its task (Gemini Flash for extraction, Perplexity Sonar for live search, Gemini Pro for deep reasoning), reducing cost ~60% vs. uniform premium models.
- **Four-tier state architecture**: Input, Intelligence, Analysis, and Output state tiers create a clean data dependency graph with no circular references -- downstream agents read upstream keys via f-string interpolation in prompts.
- **RAG knowledge base**: Pinecone-backed retrieval system with parent-child chunking (3000/300 char) over 30+ curated negotiation articles, using multilingual-e5-large embeddings.

## Tech Stack

| Layer | Technology |
|---|---|
| Agent Framework | Google ADK v1.5.0 |
| Primary LLMs | Gemini 2.5 Pro/Flash, Perplexity Sonar |
| LLM Routing | OpenRouter + LiteLLM |
| Web Framework | FastAPI + Uvicorn |
| Database | PostgreSQL (Render) |
| Search APIs | Perplexity API, Tavily API |
| Email Intel | Hunter.io |
| Speech-to-Text | Deepgram Nova-2 |
| Video Processing | yt-dlp, FFmpeg |
| Vector DB | Pinecone (Serverless) |
| RAG Framework | LangChain |
| Containerization | Docker, Python 3.11 |

## Quick Start

```bash
git clone https://github.com/shizhigu/quotientai.git
cd quotientai
cp .env.example .env  # fill in API keys
docker build -t creatoros .
docker run -p 8000:8000 creatoros
```

## License

MIT
