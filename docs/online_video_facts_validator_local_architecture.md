# Online Video Facts Validator — Local-First Architecture Proposal

## 1. Initial Summary

The goal is not simply an LLM that watches a video. It is an **evidence-driven investigation system**:

**URL → video/transcript → claims → independent research → evidence comparison → verification → confidence → final report**

For a local-first MVP, there are five viable architectures:

| Approach | Core idea | Difficulty | Quality | Recommendation |
|---|---|---:|---:|---|
| **A. LLM + deterministic pipeline** | Python pipeline + LLM + web search | 5/10 | 8/10 | ⭐ Best starting point |
| **B. Agentic ReAct** | LLM autonomously chooses tools/actions | 7/10 | 8–9/10 | Add after A works |
| **C. Multi-agent system** | Separate agents for claims, research, statistics, review | 8.5/10 | 9/10 potential | Later |
| **D. Fully local LLM** | Local LLM + local Whisper + local DB | 8/10 | 6–8/10 | Great experiment, harder research |
| **E. Hybrid local AI + external research** | Local video/LLM processing + web/API evidence | 6/10 | 9/10 potential | ⭐ Long-term architecture |

The recommended evolution is:

**A → E → B/C**, rather than jumping directly into a complicated autonomous multi-agent system.

---

# 2. What We Are Actually Building

The system should not treat the LLM itself as the fact-checker.

> **The LLM should be the investigator/orchestrator.**

The system should combine deterministic processing, AI reasoning, external evidence retrieval, source evaluation, contradiction checking, and structured reporting.

```text
                 VIDEO URL
                    │
                    ▼
          ┌───────────────────┐
          │ Video Ingestion   │
          │ URL / metadata    │
          │ audio / frames    │
          └─────────┬─────────┘
                    │
                    ▼
          ┌───────────────────┐
          │ Understanding     │
          │ Transcript        │
          │ timestamps        │
          │ visual information│
          └─────────┬─────────┘
                    │
                    ▼
          ┌───────────────────┐
          │ Claim Extraction  │
          │ C1,C2,C3...       │
          └─────────┬─────────┘
                    │
             ┌──────┴───────┐
             ▼              ▼
       Research Engine   Local Analysis
             │              │
             ▼              ▼
       Web / APIs       Statistics
       Documents        calculations
       databases        context
             │              │
             └──────┬───────┘
                    ▼
          ┌───────────────────┐
          │ Evidence Engine   │
          │ support/contradict│
          │ source quality    │
          └─────────┬─────────┘
                    ▼
          ┌───────────────────┐
          │ Reasoning / Judge │
          └─────────┬─────────┘
                    ▼
          ┌───────────────────┐
          │ Report Generator  │
          └───────────────────┘
```

---

# 3. Approach A — Deterministic Pipeline + LLM

## Architecture

This is the recommended first implementation.

```text
URL
 ↓
Downloader
 ↓
Whisper
 ↓
Transcript
 ↓
LLM
 ↓
Claims JSON
 ↓
Search engine
 ↓
Evidence
 ↓
LLM
 ↓
Verdict
 ↓
Report
```

The workflow is controlled primarily by your code rather than allowing the LLM to decide everything.

Example:

```python
video = ingest(url)

transcript = transcribe(video)

claims = extract_claims(transcript)

for claim in claims:
    queries = generate_queries(claim)
    evidence = search(queries)
    verdict = evaluate(claim, evidence)

report = generate_report(claims)
```

## Why this is powerful

Every stage can be debugged independently.

If the final answer is wrong, you can investigate whether:

- transcription failed
- claim extraction failed
- search retrieved poor sources
- evidence evaluation failed
- report generation distorted the evidence

## Components

### Video

- yt-dlp
- FFmpeg
- OpenCV

### Speech

- Whisper / faster-whisper
- Whisper.cpp if maximum local efficiency is desired

### LLM

Initially:

- API-based LLM, or
- local Ollama model

### Search

- Web search API
- Search providers
- Specialized APIs later

### Storage

Initially:

```text
SQLite
```

No need for PostgreSQL, Redis, or a vector database on day one.

## Pros

- Simple
- Highly debuggable
- Fast to build
- Cheap
- Easy to test
- Easy to replace components
- Good control over hallucinations

## Cons

- Less autonomous
- Workflow must be defined manually
- Less dynamic investigation

## Difficulty

**5/10**

## MVP rating

**9/10**

---

# 4. Approach B — ReAct Agent

This is closer to a traditional AI-agent architecture.

Instead of:

```text
Code → Search → Code → Evaluate
```

the LLM receives tools such as:

```text
download_video()
transcribe()
search_web()
search_academic()
search_government()
calculate()
compare_sources()
extract_context()
```

The agent can then decide:

```text
I need more evidence.

→ Search government source

Still insufficient.

→ Search academic source

Two sources disagree.

→ Search another independent source

Now evidence is sufficient.

→ Evaluate claim
```

Conceptually:

```text
                ┌──────────────┐
                │     LLM      │
                │   Agent      │
                └──────┬───────┘
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
   Web Search      Calculator      Documents
       │               │               │
       └───────────────┼───────────────┘
                       ▼
                    Evidence
                       │
                       ▼
                     LLM
                       │
                 Need more?
                  /       \
                YES        NO
                 │          │
                 └──────────┘
                            ▼
                          Verdict
```

## Pros

- Flexible
- Can investigate unexpected claims
- Handles complex videos better
- Can decide when additional research is required

## Cons

Agents can wander.

Example:

```text
Claim
 ↓
Search
 ↓
Search another thing
 ↓
Search something unrelated
 ↓
Change interpretation
 ↓
Search again
 ↓
Large token/API cost
```

An agent can also make an incorrect early assumption and then build subsequent research around it.

## Difficulty

**7/10**

## Quality potential

**8–9/10**

## Recommendation

Add this after the deterministic pipeline is reliable.

---

# 5. Approach C — Multi-Agent System

This architecture separates responsibilities across specialized agents.

```text
             SUPERVISOR
                 │
      ┌──────────┼───────────┐
      ▼          ▼           ▼
  Claim       Research    Statistics
  Agent       Agent       Agent
      │          │           │
      └──────────┼───────────┘
                 ▼
           Evidence Agent
                 │
                 ▼
            Review Agent
                 │
                 ▼
          Report Generator
```

## Example

Suppose a video claims:

> "India's unemployment increased from 6% to 10% because of policy X."

### Claim Agent

Breaks it into:

```text
C1: unemployment = 6%
C2: unemployment = 10%
C3: unemployment increased
C4: policy X caused the increase
```

### Statistics Agent

Checks:

- numerator
- denominator
- dates
- methodology
- calculations

### Research Agent

Searches:

- government statistics
- research papers
- reputable reporting

### Causality Agent

Investigates:

> Does evidence establish that X caused Y?

### Contradiction Agent

Actively searches for evidence against the current conclusion.

### Judge Agent

Combines the findings.

## Pros

- Separation of responsibilities
- Better handling of complex investigations
- Specialized reasoning
- Independent challenge of conclusions
- Strong long-term architecture

## Cons

- Much more complicated
- Higher token/API cost
- More latency
- Agent coordination problems
- Harder debugging
- More opportunities for inconsistent conclusions

## Difficulty

**8.5/10**

## Recommendation

**Do not start here. Build toward it.**

---

# 6. Approach D — 100% Local AI

Architecture:

```text
Video
 ↓
yt-dlp
 ↓
Local Whisper
 ↓
Local LLM
 ↓
Local embeddings
 ↓
Local vector DB
 ↓
Local reasoning
 ↓
Report
```

Possible stack:

```text
Python
Ollama
Llama / Qwen / Mistral family
faster-whisper
FAISS
SQLite
sentence-transformers
```

## Major advantage

Your processing and data can stay on your machine.

## Fundamental problem

Fact checking requires current external evidence.

For example:

> "The RBI changed X yesterday."

A completely offline model cannot know what happened yesterday unless that information has already been provided locally.

Therefore:

```text
LOCAL AI ≠ LOCAL KNOWLEDGE
```

You can run the intelligence locally, while current evidence still needs external information.

## Additional issue

Local LLM quality varies significantly based on:

- model
- quantization
- GPU
- RAM
- context length
- reasoning capability

## Difficulty

**8/10**

## Good for

- Learning
- Privacy
- Experimentation
- Offline transcription
- Document analysis

## Limitation

Not ideal as the first high-quality fact-checking system.

---

# 7. Approach E — Hybrid Local AI + External Evidence

This is the recommended long-term architecture.

Keep AI-heavy processing local:

```text
                YOUR PC
─────────────────────────────────

Video
 ↓
Whisper
 ↓
Claim extraction
 ↓
Claim classification
 ↓
Evidence orchestration
 ↓
Evidence evaluation
 ↓
Report generation

                │
                │ Internet
                ▼

       External Evidence
       ├── Search
       ├── Government
       ├── Research
       ├── News
       ├── Fact-check databases
       └── Public documents
```

## Local responsibilities

- Video processing
- Transcription
- Claim database
- Investigation state
- Embeddings
- Intermediate results
- Report construction

## External responsibilities

- Current information
- Web search
- Government data
- Academic research
- News
- Original documents

## Key advantage

It solves the fundamental conflict:

> **AI reasoning can be local, while knowledge can remain current.**

---

# 8. Approach F — Evidence Graph

A future architecture can represent evidence as a graph rather than only storing text.

```text
VIDEO
 │
 ├── CLAIM C1
 │      │
 │      ├── SUPPORTS → Source A
 │      ├── SUPPORTS → Source B
 │      └── CONTRADICTS → Source C
 │
 ├── CLAIM C2
 │      │
 │      ├── SUPPORTS → Source D
 │      └── CONTEXT → Source E
 │
 └── CLAIM C3
        │
        └── UNVERIFIED
```

Each claim can maintain:

```text
Claim
 ├── evidence
 ├── counter-evidence
 ├── source quality
 ├── publication date
 ├── evidence date
 ├── confidence
 └── dependencies
```

This becomes particularly useful when analyzing thousands of videos.

Potential future capabilities:

- Detecting repeated claims
- Finding recurring sources
- Tracking claims across videos
- Identifying source patterns
- Building a reusable evidence database

---

# 9. Architecture Comparison

| Factor | A Pipeline | B ReAct | C Multi-Agent | D Fully Local | E Hybrid | F Evidence Graph |
|---|---:|---:|---:|---:|---:|---:|
| Development | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| Debugging | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Accuracy potential | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Autonomy | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Current information | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Privacy | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Cost | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Complexity | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Scalability | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

# 10. Recommended Evolution

Do not build six separate systems.

Build one architecture that evolves:

```text
                VERSION 1
                    │
        Deterministic Pipeline
                    │
                    ▼
             Reliable MVP
                    │
                    ▼
                VERSION 2
                    │
             Add Agent Layer
                    │
                    ▼
          Semi-autonomous Agent
                    │
                    ▼
                VERSION 3
                    │
          Specialized Agents
                    │
                    ▼
            Multi-Agent System
                    │
                    ▼
                VERSION 4
                    │
            Evidence Graph
                    │
                    ▼
       Large-scale Fact Database
```

The V1 interfaces should be designed so the system can later evolve into the hybrid, agentic, multi-agent, and evidence-graph architectures.

---

# 11. What to Build Locally First

The first version should be surprisingly small.

## V0.1

```text
YouTube URL
     ↓
Download audio
     ↓
Whisper
     ↓
Transcript
     ↓
LLM
     ↓
Extract claims
     ↓
Web search
     ↓
Evidence
     ↓
LLM evaluation
     ↓
Markdown report
```

Avoid initially:

- LangGraph
- Vector database
- Multi-agent architecture
- Kubernetes
- Docker
- Frontend
- Redis
- PostgreSQL
- Complicated memory

---

# 12. Recommended V0.1 Technology Stack

```text
Python 3.12+
│
├── yt-dlp
├── FFmpeg
├── faster-whisper
│
├── Pydantic
├── SQLAlchemy
├── SQLite
│
├── LLM
│   ├── API initially
│   └── Ollama/local model later
│
├── Search
│   └── Web search API
│
├── BeautifulSoup
│
└── FastAPI
```

Avoid LangChain initially.

The goal is to understand the underlying architecture first. An orchestration framework can be introduced later when it solves a specific problem.

---

# 13. Major Challenges

## 13.1 Video Acquisition

A URL does not necessarily mean the video can be reliably obtained.

Different platforms can have:

- Access restrictions
- Login requirements
- Rate limits
- Regional restrictions
- Content availability differences

Design:

```text
URL
 ↓
Platform detector
 ↓
Can access?
 ├── YES → process
 └── NO → alternative ingestion / explain limitation
```

---

## 13.2 Claim Extraction

A 10-minute video could contain:

```text
50 statements
↓
20 opinions
↓
15 factual claims
↓
5 important claims
↓
2 claims that determine the conclusion
```

The system must identify which claims matter.

---

## 13.3 Evidence Quality

Finding 20 web pages is not necessarily better than finding two excellent primary sources.

Evidence should consider:

```text
Source Quality
+
Evidence Relevance
+
Evidence Directness
+
Independence
+
Recency
```

---

## 13.4 Causality

Example:

> "X happened after Y, therefore Y caused X."

The system must distinguish:

```text
Correlation
       ≠
Temporal sequence
       ≠
Causation
```

---

## 13.5 Confidence Calibration

If the system says:

> TRUE — 98% confidence

that 98% needs to have a meaningful relationship with actual correctness.

Confidence should therefore be evaluated and calibrated against a test dataset rather than being treated as a decorative number.

---

# 14. Recommended Development Roadmap

```text
PHASE 0
Architecture + environment
        ↓
PHASE 1
YouTube → Transcript
        ↓
PHASE 2
Transcript → Claims
        ↓
PHASE 3
Claims → Search queries
        ↓
PHASE 4
Search → Evidence database
        ↓
PHASE 5
Evidence → Claim verdict
        ↓
PHASE 6
Verdict → 12-section report
        ↓
PHASE 7
Add contradiction research
        ↓
PHASE 8
Add statistics verification
        ↓
PHASE 9
Add agentic decision-making
        ↓
PHASE 10
Add visual verification
        ↓
PHASE 11
Multi-agent architecture
        ↓
PHASE 12
Evidence graph
```

---

# 15. Recommended First Scope

Do not start with "any video."

## V1 Scope

- YouTube only
- English + Hindi
- 5–15 minute videos
- Text/verbal claims first
- No complex visual fact checking initially

## V2

Add:

- Instagram
- Facebook
- Longer videos
- Hindi/English mixed speech
- Screenshots
- Charts
- Statistics

## V3

Add visual claims:

```text
"This image is from event X."
"This person is Y."
"This graph shows Z."
"This footage is from 2024."
```

This is where computer vision becomes important.

---

# 16. Critical Architectural Improvement

Instead of:

```text
Claim → Evidence → Evaluate → Verdict
```

use:

```text
Claim
   │
   ▼
Claim Decomposition
   │
   ▼
Research Plan
   │
   ├─────────────┐
   ▼             ▼
Supporting    Contradicting
Evidence      Evidence
   │             │
   └──────┬──────┘
          ▼
     Source Audit
          │
          ▼
    Context Check
          │
          ▼
   Statistical Check
          │
          ▼
    Evidence Judge
          │
          ▼
      Verdict
```

The **active contradiction search** is particularly important.

Without it, the system can easily fall into:

```text
Search
 ↓
Find supporting source
 ↓
TRUE
```

A robust fact-checker should actively search for evidence that could disprove its current conclusion.

---

# 17. Final Recommendation

The best development strategy is:

> **Start with Approach A, but design its interfaces so it can evolve into Approach E/B/C/F.**

Do not build an "AI agent" first.

Build a **reliable fact-checking engine first, then give the engine agency.**

This keeps the initial project:

- Understandable
- Testable
- Debuggable
- Affordable
- Locally runnable

while preserving a path toward:

- Agentic research
- Multi-agent verification
- Visual fact checking
- Evidence graphs
- Large-scale fact databases

## Next Step

The next implementation stage should be a detailed **V0.1 architecture design**, covering:

1. Exact local architecture
2. Folder/project structure
3. Python modules
4. Data models
5. Local vs API LLM choice
6. Web-search mechanism
7. Video ingestion flow
8. Claim schema
9. Evidence schema
10. Verdict logic
11. Report schema
12. First end-to-end workflow
