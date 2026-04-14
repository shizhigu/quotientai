# CreatorOS (QuotientAI)

## 1. One-Liner

An AI-powered multi-agent platform that gives independent content creators the same caliber of brand-deal intelligence, pricing strategy, and negotiation firepower that talent agencies charge tens of thousands of dollars for -- all from a single API call.

## 2. The Problem

The creator economy is worth over $250 billion, yet the vast majority of its participants -- independent YouTubers, influencers, and podcasters -- negotiate brand partnerships at a severe information disadvantage. When a brand's marketing team reaches out with a sponsorship offer, the creator is typically facing a professional negotiation squad armed with internal rate cards, industry benchmarks, and legal teams. The creator, on the other hand, is armed with nothing but a gut feeling and maybe a cursory Google search.

This asymmetry produces measurable damage. Studies suggest that creators routinely leave 25-40% of deal value on the table. They accept lowball flat fees when their audience demographics justify premium CPMs. They sign away perpetual, worldwide content usage rights without understanding the licensing value they are forfeiting. They agree to exclusivity windows that block competing deals without charging an appropriate premium.

The existing tools in the market attack only slices of this problem. Influencer pricing calculators give a single static number with no strategic context. Media kit generators produce pretty PDFs but do not actually analyze the specific brand sitting across the table. CRM tools track deal pipelines but offer zero intelligence about what the deal should be worth. No product on the market combines real-time brand intelligence, creator valuation, dynamic pricing, negotiation strategy, proposal generation, and contact discovery into a single coherent workflow.

Creators who can afford talent management agencies get all of this -- but those agencies take 15-20% commission and typically will not represent creators below 500K subscribers. CreatorOS was built to close that gap.

## 3. The Solution

CreatorOS is a multi-agent AI system built on Google's Agent Development Kit (ADK) that orchestrates seven specialized agents in a sequential pipeline. A creator provides their YouTube profile data, the name of a brand they want to pitch, and optionally some deal deliverables. The system returns a complete deal intelligence package: brand research, creator valuation score, dynamic pricing with floor/target/opening-quote figures, a full negotiation playbook with scripted responses to common brand tactics, a ready-to-send HTML proposal email, and verified email contacts at the brand's marketing department.

The platform also includes a video content processing pipeline. Creators paste a YouTube URL and the system downloads the audio, transcribes it with word-level timestamps via Deepgram, and then uses an LLM agent to select the most compelling segments for repurposing into short-form marketing content, meeting notes, tutorials, or highlight reels.

Everything is exposed through a FastAPI backend with custom endpoints for chat, deal analysis, email template modification, session state management, and video segment selection. The system uses PostgreSQL-backed session persistence so creators can return to previous analyses and continue conversations with the chat agent, which acts as a warm, creator-advocate advisor named Quokka.

## 4. Architecture Overview

The system follows a coordinator-delegate pattern with two primary execution paths:

**Path 1: Deal Intelligence Pipeline (Sequential Agent)**

A `SequentialAgent` chains seven sub-agents that each read from and write to a shared session state. The state is organized into four tiers:

1. **Input State** -- brand name, project title, deliverables, creator profile, inquiry email
2. **Intelligence Gathering State** -- brand intelligence summary, negotiation intelligence
3. **Core Analysis State** -- contract risk analysis, creator value assessment, pricing model calculation
4. **Final Decision State** -- recommended pricing strategy, negotiation tactics, generated proposal email

The seven agents execute in strict order:

```
BrandIntelligenceAgent
    --> CreatorValueAssessmentAgent
        --> PricingStrategyAgent
            --> NegotiationIntelligenceAgent
                --> ProposalEmailAgent
                    --> EmailFinderAgent
                        --> FormatOutputAgent
```

Each agent reads the cumulative state produced by its predecessors and writes its own output to a designated state key. This creates a clean data dependency graph with no circular references.

**Path 2: Chat Agent**

An `LlmAgent` named Quokka handles free-form conversation. It has access to the full session state (including all deal intelligence outputs) and acts as a creator-friendly interpreter of the technical analysis, channeling communication styles inspired by figures like Oprah Winfrey and Simon Sinek.

**Path 3: Video Content Pipeline**

A three-stage pipeline exposed at `/custom/video/select-segments`:
1. **Audio Download** -- yt-dlp extracts audio from YouTube
2. **Transcription** -- Deepgram Nova-2 produces word-level timestamped segments
3. **Segment Selection** -- A `VideoSegmentSelectionAgent` uses pure LLM intelligence to pick 3-5 segments optimized for the requested content mode

**Coordination**

A `CoordinatorAgent` routes user requests to either the deal intelligence pipeline or the chat agent. The `RootAgent` handles specialized document formatting tasks. The FastAPI application creates dedicated `Runner` instances for each execution path, all sharing a unified `DatabaseSessionService`.

After deal analysis completes, results are automatically dispatched to a Supabase webhook for frontend synchronization.

## 5. Technical Deep Dive

### Multi-Model Orchestration

CreatorOS does not rely on a single LLM. Each agent is assigned a model optimized for its specific task, all routed through OpenRouter:

- **Brand Intelligence**: Perplexity `sonar-reasoning-pro` -- chosen for its real-time web search capabilities, essential for up-to-date brand research
- **Creator Value Assessment**: Gemini 2.5 Flash -- fast structured analysis with low temperature (0.1) for consistent scoring
- **Pricing Strategy**: Perplexity `sonar-reasoning-pro` -- market rate research requires live data
- **Negotiation Intelligence**: Gemini 2.5 Pro -- the most capable model handles the most complex reasoning task, with access to Perplexity search tools for live market validation
- **Proposal Email**: Gemini 2.5 Flash at temperature 0.6 -- creative enough for persuasive copywriting, controlled enough for professional output
- **Email Finder**: Gemini 2.5 Flash -- lightweight orchestration of Hunter.io API calls and Tavily web search
- **Format Output**: Gemini 2.0 Flash Lite -- simple data extraction task, smallest model sufficient
- **Chat (Quokka)**: Gemini 2.5 Flash at temperature 1.4 -- high creativity for warm, engaging conversation
- **Video Segment Selection**: Gemini 2.0 Flash -- fast inference for transcript analysis

This per-agent model selection is a deliberate cost-performance optimization. The system uses the cheapest model that can reliably perform each task, reserving expensive reasoning models for tasks that genuinely require deep analysis.

### State Management Architecture

The state system uses a four-tier architecture defined in `state_keys.py`:

```
Tier 1 (Input):        brand_name, project_title, deal_deliverables, 
                        youtube_creator_profile, inquiry_email
Tier 2 (Intelligence): brand_intelligence_summary, negotiation_intelligence
Tier 3 (Analysis):     contract_risk_analysis, creator_value_assessment, 
                        pricing_model_calculation
Tier 4 (Output):       recommended_pricing_strategy, negotiation_tactic_summary,
                        generated_proposal_email, session_status
```

Each agent declares its `output_key` at construction time. The ADK framework automatically serializes the agent's response into the session state under that key. Downstream agents reference upstream keys using Python f-string interpolation in their instruction prompts: `{{{STATE_BRAND_INTELLIGENCE_SUMMARY}}}`. This means the full context flows forward without any manual data passing.

### Real-Time Search Integration

Two search tools are implemented as native async functions wrapped in `LongRunningFunctionTool`:

- **Perplexity Search** (`perplexity_search`): Calls the Perplexity chat completions API with `sonar-reasoning-pro` for deep research queries. Used by the Negotiation Intelligence Agent to validate strategies against current market conditions.
- **Tavily Search** (`tavily_search`): Advanced web search via the Tavily API. Used by the Email Finder Agent for domain discovery.

Both tools were originally implemented as MCP (Model Context Protocol) toolsets but were refactored to native async implementations for better performance and reliability.

### Email Contact Discovery Pipeline

The `EmailFinderAgent` executes a two-tool workflow:

1. **Domain Discovery**: Uses Tavily search to find the brand's official website domain, preferring global `.com` domains over regional variants
2. **Contact Search**: Calls the Hunter.io domain search API with a smart two-phase strategy -- first searches the marketing department, and if fewer than 3 contacts are found, broadens to all departments and merges results with deduplication
3. **Contact Scoring**: The LLM ranks contacts on a 10-point scale weighted by relevance (40%), accessibility (30%), contact quality (20%), and department fit (10%)

### Video Processing Pipeline

The video pipeline at `/custom/video/select-segments` implements a clean three-stage architecture:

1. **yt-dlp Audio Extraction**: Downloads best-quality audio, post-processes to WAV format
2. **Deepgram Transcription**: Uses the Nova-2 enhanced model with paragraph-level segmentation, utterance detection, and smart formatting. Produces segments with precise start/end timestamps.
3. **LLM Segment Selection**: The `VideoSegmentSelectionAgent` receives the full transcript and selects 3-5 segments optimized for the requested mode (marketing, meeting notes, tutorial, or highlights). Each selected segment includes timing, transcript text, selection reasoning, and an engagement score.

### Contract Analysis

The `ContractAnalysisAgent` handles PDF contract review through a `before_agent_callback` that intercepts uploaded files, saves them as ADK artifacts, and injects the document into the agent's context. The agent then classifies each clause by risk level (High/Medium/Low/Standard) and generates specific counter-proposal language for unfavorable terms.

### RAG Knowledge Base

A Retrieval-Augmented Generation system built on Pinecone and LangChain provides negotiation domain expertise. It uses a parent-child chunking strategy:
- **Parent chunks**: 3000 characters with 400-character overlap, split on markdown headers
- **Child chunks**: 300 characters with 50-character overlap, split on sentences
- **Embeddings**: Pinecone's `multilingual-e5-large` model (1024 dimensions)
- **Retrieval**: Searches child chunks for precision, returns parent chunks for context

The knowledge base is populated from 30+ curated articles on influencer negotiation, pricing strategies, and contract best practices.

## 6. Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Agent Framework** | Google ADK v1.5.0 | Agent orchestration, session management, state propagation |
| **Primary LLMs** | Gemini 2.5 Pro/Flash, Perplexity Sonar | Reasoning, analysis, real-time search |
| **Secondary LLMs** | Gemini 2.0 Flash/Lite, DeepSeek R1 | Lightweight tasks, alternative reasoning |
| **LLM Routing** | OpenRouter + LiteLLM | Unified API for multi-provider model access |
| **Web Framework** | FastAPI + Uvicorn | REST API with async support |
| **Database** | PostgreSQL (Render) | Session persistence via ADK DatabaseSessionService |
| **Backend Services** | Supabase | Deal data storage, webhook-based frontend sync |
| **Search APIs** | Perplexity API, Tavily API | Real-time web research and domain discovery |
| **Email Intelligence** | Hunter.io API | Brand contact discovery and verification |
| **Speech-to-Text** | Deepgram Nova-2 | Word-level audio transcription |
| **Video Processing** | yt-dlp, FFmpeg | YouTube audio extraction |
| **Vector Database** | Pinecone (Serverless) | RAG knowledge retrieval |
| **Embeddings** | multilingual-e5-large | Document embedding for semantic search |
| **RAG Framework** | LangChain | Document splitting, retrieval pipeline |
| **Email Integration** | Gmail API, Google OAuth | Inbox monitoring for brand inquiries |
| **MCP Tools** | Supabase MCP Server | Database operations via Model Context Protocol |
| **Containerization** | Docker, Python 3.11-slim | Deployment packaging |
| **Data Validation** | Pydantic v2 | Request/response schema enforcement |
| **Deployment** | Render (Cloud) | Container hosting with health checks |

## 7. Challenges & Solutions

### Challenge 1: Agent Output Consistency

**Problem**: LLMs are inherently non-deterministic. When seven agents are chained sequentially and each depends on structured JSON from its predecessor, a single malformed output can cascade into total pipeline failure.

**Solution**: Every agent's instruction includes explicit JSON schema definitions with example outputs. Critical agents use low temperature settings (0.1-0.2) for consistency. The `FormatOutputAgent` at the end of the pipeline uses Pydantic `output_schema` enforcement to guarantee the final output matches the exact structure the frontend expects. Error handling at the API layer provides sensible defaults when individual agents produce unexpected output.

### Challenge 2: Model Selection Economics

**Problem**: Using the most capable model for every agent would produce excellent results but at prohibitive cost and latency. A full deal analysis pipeline touching seven agents could easily cost $2-5 per run with premium models.

**Solution**: Implemented per-agent model selection based on task complexity. Simple extraction tasks use Gemini 2.0 Flash Lite (cheapest). Mid-range analysis uses Gemini 2.5 Flash. Only the negotiation intelligence agent -- which requires the deepest reasoning about psychological tactics, game theory, and multi-dimensional strategy -- gets Gemini 2.5 Pro. Real-time search tasks use Perplexity's specialized models. This tiered approach reduces cost by roughly 60% compared to uniform premium model usage.

### Challenge 3: Real-Time Data Freshness

**Problem**: Brand information, market rates, and partnership trends change constantly. Static training data produces stale pricing recommendations and outdated brand intelligence.

**Solution**: Integrated Perplexity's `sonar-reasoning-pro` model for agents that need current data (Brand Intelligence, Pricing Strategy). Added Tavily web search as a secondary real-time source. The search tools were initially implemented as MCP (Model Context Protocol) servers but were refactored to native async Python functions for better reliability and lower latency. The native implementation eliminated the overhead of spawning Node.js subprocess servers for each search request.

### Challenge 4: Creator-Centric Prompt Engineering

**Problem**: LLMs have a natural tendency toward balanced, diplomatic output. When analyzing a brand deal, they default to presenting both sides equally. But CreatorOS exists to advocate for the creator -- it needs to identify leverage, expose unfavorable terms, and maximize the creator's position without being dishonest.

**Solution**: Every agent prompt is explicitly framed from the creator's perspective. The Negotiation Intelligence Agent channels Chris Voss (FBI negotiation), Harvard's BATNA framework, and Robert Cialdini's influence principles -- all oriented toward maximizing creator outcomes. The Proposal Email Agent is instructed to never write from an external consultant's perspective and always advocate for the creator. The Chat Agent (Quokka) is explicitly told "Your user is ALWAYS the creator, NOT agency or brand" as a foundational directive.

### Challenge 5: Multimodal Input Processing

**Problem**: Creators often want to share screenshots of their social media analytics, past collaboration results, or brand inquiry emails. Processing these alongside text data required careful memory management and format handling.

**Solution**: Built an async image processing pipeline in `process_profileImages()` that downloads images with size validation (10MB per image, 6 images max), converts them to Google GenAI `Part` objects with proper MIME type detection, and includes them in the agent's content alongside text. The pipeline includes explicit memory cleanup with `del` statements and temporary file removal to prevent memory leaks during high-concurrency usage.

### Challenge 6: Webhook-Based Frontend Synchronization

**Problem**: The deal intelligence pipeline takes significant time to complete (processing through seven agents sequentially). The frontend cannot block on a synchronous HTTP response for that duration without degrading user experience.

**Solution**: Implemented an async webhook dispatch pattern. When the deal analysis completes, the API endpoint automatically POSTs the full structured result to a Supabase Edge Function (`update-deal-status`). The frontend subscribes to Supabase real-time updates and receives the analysis as soon as it is ready. This decouples the analysis execution from the user-facing response cycle. The webhook dispatch is wrapped in a try/except block so that failures in the notification layer never affect the primary analysis pipeline -- if the webhook fails, the result is still returned directly in the HTTP response.

### Challenge 7: Session Continuity Across Agent Types

**Problem**: The system has multiple independent `Runner` instances (chat, deal analysis, proposal email, video segment selection), each potentially needing access to the same session data. A creator might run a deal analysis and then want to ask Quokka questions about the results.

**Solution**: All runners share a unified `DatabaseSessionService` backed by the same PostgreSQL connection. The `APP_NAME` constant ensures all runners operate in the same namespace. Session state is accessible across runner boundaries, so the chat agent can read deal intelligence outputs written by the deal analysis pipeline. The `/custom/session/state` endpoint provides a clean API for the frontend to inspect session state and auto-create sessions when they do not exist.

## 8. What I Learned

**Multi-agent systems are not just prompt engineering at scale.** The most valuable lesson from building CreatorOS was that orchestrating multiple AI agents is fundamentally a systems architecture problem, not a natural language problem. Getting each individual agent to produce good output was the easy part. The hard part was designing the state management architecture so that information flowed cleanly between agents, error states propagated gracefully, and the cumulative output remained coherent after passing through seven independent reasoning steps.

**Model selection is an engineering decision, not a "use the best one" decision.** I started with Gemini 2.5 Pro for every agent and gradually learned that most tasks do not need that level of capability. The process of downgrading each agent to the cheapest model that still produced acceptable output taught me to think about LLM costs the way backend engineers think about database query optimization -- you do not use a full table scan when an index lookup will do.

**Temperature is not just a creativity dial.** Different agents need different temperature profiles, and the optimal value is not always intuitive. The Proposal Email Agent needed moderate temperature (0.6) -- too low produced robotic emails, too high produced incoherent prose. The Chat Agent needed high temperature (1.4) to feel warm and human. The analytical agents needed near-zero temperature (0.1) for consistent structured output. I tuned these values through dozens of iterations, not theoretical reasoning.

**Real-time search integration changes what AI applications can do.** Before integrating Perplexity and Tavily, the system was fundamentally limited to what the models already knew. After integration, the Brand Intelligence Agent could analyze companies that launched last month, and the Pricing Strategy Agent could cite 2025 market rates. The gap between "trained on data up to date X" and "can search the web right now" is enormous for any application that deals with current market conditions.

**Prompt engineering is software engineering.** The prompts in this system are not casual instructions -- they are specification documents. The Brand Intelligence Agent's prompt is over 350 lines of structured requirements, JSON schemas, decision trees, and validation criteria. Treating prompts as code artifacts (version-controlled, reviewed, iterated) was essential for maintaining quality as the system grew.

**The MCP-to-native refactor taught me about abstraction boundaries.** The search tools were initially implemented as MCP (Model Context Protocol) toolsets, spawning Node.js subprocesses to run Perplexity and Tavily servers. This was architecturally elegant but operationally fragile -- subprocess management, timeout handling, and startup latency made the system unreliable under load. Refactoring to native async Python functions with `aiohttp` eliminated an entire layer of complexity. The lesson: choose the abstraction that matches your operational needs, not the one that looks most impressive in a system diagram.

**Agent callbacks are more powerful than they appear.** The ADK framework's `before_agent_callback` and `after_agent_callback` hooks turned out to be the right mechanism for cross-cutting concerns. The contract analysis agent uses a before-callback to intercept PDF uploads and save them as artifacts. The proposal email agent uses an after-callback to automatically sync generated emails to Supabase. These callbacks keep the agent prompts focused on their core task while handling infrastructure concerns at the framework level.

## 9. Motivation & Context

I built CreatorOS because I experienced the creator-brand negotiation problem firsthand. As someone who follows the creator economy closely, I watched talented creators with engaged audiences consistently undervalue themselves in brand deals -- not because they lacked talent, but because they lacked information.

The information asymmetry in creator partnerships is structural. Brands have procurement teams, historical rate data, and legal departments. Creators have their content and their audience. The market needed a tool that could give any creator -- from a 10K-subscriber YouTuber to a 500K-follower Instagram creator -- access to the same quality of deal intelligence that top talent agencies provide to their exclusive rosters.

I chose Google's Agent Development Kit as the foundation because multi-agent orchestration was the right abstraction for this problem. Each stage of deal analysis (brand research, creator valuation, pricing, negotiation strategy, proposal writing, contact discovery) is a distinct cognitive task that benefits from specialized prompting and model selection. A single monolithic prompt could not achieve the depth of analysis that seven specialized agents produce.

The video content processing feature emerged from a related creator need: repurposing long-form content into short-form clips for social media. The YouTube-to-segments pipeline demonstrates how the same agent infrastructure can extend beyond deal intelligence into content operations.

This project represents my deep dive into production AI agent systems -- from prompt engineering and multi-model orchestration to real-time tool integration and deployment infrastructure.

## 10. Status

**Current State**: Functional backend with all core agents operational. The deal intelligence pipeline successfully produces end-to-end analysis from brand name to formatted output. The video segment selection pipeline is integrated and working. The system is containerized and deployable.

**What Works**:
- Full seven-agent deal intelligence pipeline producing structured JSON output
- Chat agent (Quokka) with warm, creator-advocate personality and session continuity
- Video content processing: YouTube URL to timestamped segment selection
- Contract analysis with PDF ingestion and risk classification
- Email contact discovery via Hunter.io with smart department prioritization
- Multimodal input support for creator profile screenshots
- Supabase webhook integration for frontend data synchronization
- PostgreSQL-backed session persistence across all agent runners
- Docker containerization with health checks and Render deployment

**Active Development**:
- Model performance tuning across the agent pipeline
- Prompt optimization for edge cases (small creators with minimal data, obscure brands)
- Error recovery hardening for cascading agent failures
- RAG knowledge base expansion with additional negotiation and pricing resources

**Repository**: [github.com/shizhigu/quotientai](https://github.com/shizhigu/quotientai)

---

*Built with Google ADK, Gemini, Perplexity, Deepgram, and the conviction that every creator deserves institutional-grade deal intelligence.*
