# Agentic AI Video Fact-Checker: Creation Guide & Prerequisites

This document outlines the specific steps, components, and prerequisites for building an agentic AI model designed for video fact-checking and claims validation, based on the detailed specification provided.

## Overview

The goal is to create an autonomous agent that can:
1. Accept public video URLs from multiple platforms
2. Extract and analyze claims made in the video
3. Independently fact-check each claim using reliable evidence
4. Provide a structured, evidence-based assessment with confidence scores
5. Identify context manipulation, statistical errors, and debatable points
6. Generate a comprehensive report following the specified 12-step format

This agent operates as a **tool-using, reasoning, and planning system** – not just a classifier, but an active investigator that gathers evidence, evaluates sources, and draws conclusions through an iterative process.

---

## Prerequisites

### Technical Stack
- **Programming Language**: Python 3.9+ (recommended for ML/NLP ecosystem)
- **Core Frameworks**:
  - [LangChain](https://www.langchain.com/) or [LlamaIndex](https://www.llamaindex.ai/) for agent orchestration
  - [Transformers](https://huggingface.co/docs/transformers/index) (Hugging Face) for NLP models
  - [FastAPI](https://fastapi.tiangolo.com/) or [Flask] for API endpoints (if serving as a service)
- **Video Processing**:
  - [yt-dlp](https://github.com/yt-dlp/yt-dlp) (for YouTube, Instagram, Facebook, Twitter video downloading)
  - [OpenCV](https://opencv.org/) or [MoviePy](https://zulko.github.io/moviepy/) for video frame extraction (if needed for visual claims)
  - Speech-to-text: [Whisper](https://github.com/openai/whisper) (OpenAI) or [Whisper.cpp](https://ggerganov.com/whisper.cpp/) for efficient transcription
- **Knowledge & Retrieval**:
  - Vector database: [FAISS](https://github.com/facebookresearch/faiss), [Pinecone](https://www.pinecone.io/), or [Weaviate](https://weaviate.io/)
  - Embedding models: Sentence-BERT variants (e.g., `all-MiniLM-L6-v2`) or domain-specific fact-checking embeddings
- **Fact-Checking Sources Integration**:
  - APIs: Google Fact Check Tools API, ClaimBuster, Snopes API (if available), Reuters Fact Check
  - Web scraping capabilities (with respect to robots.txt and terms of service): [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/), [Scrapy](https://scrapy.org/)
  - Academic databases: Semantic Scholar API, arXiv API, PubMed API (for scientific claims)
  - Government data: Data.gov, Eurostat, UN Data, World Bank APIs
  - News APIs: NewsAPI.org, GDELT Project
- **Infrastructure**:
  - GPU access (recommended for Whisper transcription and embedding generation)
  - Sufficient storage for video caching and knowledge base
  - Rate handling for API requests (exponential backoff, caching)

### Knowledge Base Requirements
The agent needs access to reliable, verifiable information sources:
1. **Primary Sources** (highest priority):
   - Government publications (.gov, .eu, .int domains)
   - Official statistics bureaus (BLS, Eurostat, OECD)
   - Legislative documents (Congress.gov, official gazettes)
   - Court judgments (Justia, PACER, BAILII)
   - Regulatory filings (SEC EDGAR, FDA databases)
   - Original research papers (via DOI resolution)
   - Official company statements (investor relations, press releases)
   - Raw datasets (data.gov, Kaggle, UCI ML Repository)

2. **Secondary Sources** (when primary unavailable or for context):
   - Reputable news outlets (AP, Reuters, BBC, Associated Press)
   - Academic institutions (university press releases, .edu domains)
   - Established research organizations (Pew Research, RAND, Brookings)
   - Industry-recognized standards bodies (ISO, IEEE, NIST)

3. **Specialized Fact-Checking Repositories**:
   - Duke Reporters' Lab Fact-Checking Database
   - International Fact-Checking Network (IFCN) signatories
   - Media Bias/Fact Check (for source reliability assessment)

### Agent-Specific Components
To implement the 12-step process, the agent requires these modular capabilities:

#### A. Video Ingestion & Understanding Module
- URL validation and platform detection (YouTube, Instagram, Facebook, Twitter/X)
- Metadata extraction (title, creator, date, description)
- Robust transcription with speaker diarization (if multiple speakers)
- Keyframe extraction for visual claim verification (optional but useful)

#### B. Claim Extraction & Classification Engine
- Natural language processing for:
  - Named entity recognition (people, organizations, locations, dates)
  - Numerical expression detection (statistics, percentages, quantities)
  - Claim boundary identification (separating facts from opinions)
  - Claim type classification (historical, scientific, causal, predictive, etc.)
  - Confidence scoring for claim extraction accuracy

#### C. Evidence Retrieval & Verification System
- Query generation from claims (transforming natural language to search queries)
- Multi-source search orchestration (simultaneous querying of multiple APIs/databases)
- Source credibility assessment (automated scoring based on domain, authority, bias indicators)
- Evidence relevance scoring (semantic similarity between claim and retrieved evidence)
- Contradiction detection (identifying when evidence directly opposes a claim)
- Supporting evidence aggregation (collecting multiple pieces that corroborate a claim)

#### D. Reasoning & Decision-Making Core
- Implementation of the ReAct (Reasoning + Acting) pattern or similar agent architecture
- Memory system for tracking:
  - Current claim under investigation
  - Evidence gathered for each claim
  - Intermediate assessments and uncertainties
  - Context manipulation checks performed
- Planning capabilities for:
  - Prioritizing which claims to check first (based on impact on video's conclusion)
  - Deciding when sufficient evidence has been gathered
  - Determining when to pursue additional sources vs. accept uncertainty

#### E. Reporting & Output Generation
- Template-based report generation following the specified 12-step format
- Confidence matrix calculation (weighted aggregation of evidence quality factors)
- Debatable claim identification (when evidence falls in gray area)
- Argument synthesis for both sides of controversial topics
- Source citation formatting with direct links where possible

---

## Steps of Creation

Follow this phased approach to build the agentic fact-checker:

### Phase 1: Foundation & Environment Setup (Days 1-3)
1. **Set up development environment**:
   - Create virtual environment: `python -m venv factcheck-agent`
   - Install core dependencies: `pip install langchain openai whisper yt-dlp transformers sentence-transformers faiss-cpu`
   - Configure API keys for required services (YouTube Data API, Google Fact Check Tools, NewsAPI, etc.)

2. **Build video ingestion prototype**:
   - Create module that accepts URL and returns:
     - Platform-agnostic metadata
     - Full transcript with timestamps
     - List of key frames (at regular intervals or scene changes)
   - Test with sample videos from each supported platform

3. **Establish knowledge base connectors**:
   - Build adapters for at least 3 primary source types (e.g., government stats, academic papers, news)
   - Implement caching mechanism to avoid repeated API calls
   - Create source credibility scoring system (based on domain authority, transparency, etc.)

### Phase 2: Claim Processing Core (Days 4-7)
1. **Develop claim extraction pipeline**:
   - Implement sentence segmentation and filtering (remove filler, focus on declarative statements)
   - Build named entity recognition (using spaCy or transformer-based NER)
   - Add numerical expression detection (regex + context understanding)
   - Create claim type classifier (fine-tune a model or use rule-based system for categories)

2. **Create claim ID management system**:
   - Assign unique IDs (C1, C2, C3...) to each verifiable claim
   - Maintain mapping between claim ID and:
     - Original quote/timestamp
     - Claim type classification
     - Priority level (based on potential impact on video's conclusion)

### Phase 3: Fact-Checking Engine (Days 8-12)
1. **Build evidence retrieval system**:
   - Design query generation templates for different claim types:
     - Statistics: "official [statistic] [year] [country] source"
     - Historical claims: "[event] date official record"
     - Quotes: "[exact phrase] speaker context"
     - Causal claims: "[effect] cause study research"
   - Implement parallel searching across multiple sources
   - Add deduplication and relevance ranking

2. **Implement evidence evaluation logic**:
   - Create rubric for assessing evidence quality (HIGH/MEDIUM/LOW based on source type, date, directness)
   - Build confidence scoring algorithm (0-100%) considering:
     - Number of independent sources confirming
     - Source quality and recency
     - Directness of evidence (direct measurement vs. inference)
     - Consistency across sources
   - Develop status assignment logic (TRUE/MOSTLY TRUE/etc.) based on evidence strength and alignment with claim

### Phase 4: Context & Statistical Verification (Days 13-15)
1. **Implement context manipulation detector**:
   - Build checklists for common manipulation techniques:
     - Cherry-picking: compare presented timeframe vs. full available data
     - Missing context: check if baseline/proper denominator was used
     - Misleading statistics: verify calculations, units, percentages vs. percentage points
     - Outdated data: check timestamp of statistics vs. claim context
     - Selective quotation: verify full context of quoted material
   - Create temporal inconsistency checker (for timelines, sequencing claims)

2. **Develop statistical verification module**:
   - Build independent recalculation engine for common stats:
     - Growth rates, percentages, ratios
     - Averages, medians, statistical significance
     - Economic indicators (inflation, unemployment, GDP)
   - Implement unit conversion and verification
   - Add plausibility checking (e.g., "Can X really be Y% of Z given known totals?")

### Phase 5: Reasoning Loop & Agent Orchestration (Days 16-18)
1. **Implement the core agentic loop**:
   - Define action space: 
     - `EXTRACT_CLAIMS(video)`
     - `GET_EVIDENCE(claim_id, query)`
     - `EVALUATE_EVIDENCE(claim_id, evidence_list)`
     - `CHECK_CONTEXT(claim_id, video_context)`
     - `VERIFY_STATISTICS(claim_id, numbers)`
     - `CROSS_CHECK_SOURCES(claim_id, min_sources=2)`
     - `GENERATE_REPORT_SECTION(section_type)`
   - Implement observation processing for each action
   - Create memory system to track:
     - Current investigation state
     - Evidence gathered per claim
     - Pending verification tasks
     - Identified issues (context problems, statistical errors)

2. **Add planning and prioritization**:
   - Implement claim prioritization based on:
     - Potential to change video's overall conclusion
     - Ease of verification (some claims may be quick wins/losses)
     - Controversiality or debate potential
   - Build loop termination conditions:
     - All high-priority claims verified
     - Diminishing returns on additional evidence
     - Time/resource constraints reached

### Phase 6: Reporting & Output Generation (Days 19-21)
1. **Build report generator following the 12-step format**:
   - Create templates for each section:
     - Executive Summary
     - What the Video Claims
     - Claim-by-Claim Fact Check (table format)
     - Detailed Evidence
     - Missing Context / Manipulation
     - Confidence Matrix
     - What Is Definitely True
     - What Is False or Misleading
     - What Is Still Uncertain
     - Debatable Points
     - Debate Toolkit
     - Sources
   - Implement automatic section population based on investigation results

2. **Develop confidence matrix calculator**:
   - Implement scoring for each factor (0-100):
     - Factual accuracy: % of verifiable claims with sufficient evidence
     - Evidence quality: average source quality score
     - Source reliability: % of evidence from HIGH quality sources
     - Statistical accuracy: % of statistics verified correctly
     - Context completeness: # of context issues found / total claims
     - Logical reasoning: consistency of arguments throughout video
     - Claim verifiability: % of claims that could be reasonably checked
     - Transparency: clarity of reasoning and source attribution
   - Add explanations for each score based on investigation findings

3. **Create debatable claim handler**:
   - Identify claims where evidence is insufficient for clear verdict
   - For each, generate:
     - Position A (strongest supporting evidence)
     - Position B (strongest contradicting evidence)
     - Established facts (common ground)
     - Remaining uncertainty
     - Evidence that would resolve the dispute

### Phase 7: Testing, Validation & Refinement (Days 22-25)
1. **Create test suite**:
   - Build a library of test videos with known fact-check outcomes
   - Include edge cases: deepfakes, satire, highly technical content, breaking news
   - Test across different political spectra to ensure neutrality

2. **Implement evaluation metrics**:
   - Primary: Claim-level accuracy (vs. expert fact-checks)
   - Secondary: 
     - Report completeness (all required sections generated)
     - Confidence calibration (do high-confidence claims correlate with correctness?)
     - Bias detection (systematic favoring of any ideology?)
     - Processing time per video length
     - Source diversity in evidence

3. **Refine based on testing**:
   - Adjust claim extraction precision/recall balance
   - Tune evidence weighting algorithms
   - Improve context manipulation detection rules
   - Enhance debatable claim identification criteria

### Phase 8: Deployment & Monitoring (Ongoing)
1. **Set up production deployment**:
   - Containerize with Docker for consistency
   - Implement API endpoint (REST or GraphQL) for video URL input
   - Add async processing for longer videos (webhook or polling for results)
   - Build rate limiting and quota management for external APIs

2. **Establish monitoring and logging**:
   - Track key metrics: success rate, average processing time, API costs
   - Log all agent actions (thoughts, actions, observations) for auditability
   - Implement feedback mechanism for users to report errors
   - Create dashboard for system health and performance

3. **Plan for continual improvement**:
   - Schedule regular updates to knowledge base connectors
   - Retrain claim extraction models on new data
   - Update context manipulation detection based on emerging tactics
   - Maintain list of unreliable sources to deprioritize

---

## Critical Design Considerations

### Neutrality & Bias Mitigation
- **Source diversity**: Actively seek evidence from across the spectrum
- **Confidence calibration**: Avoid overconfidence in uncertain areas
- **Explicit uncertainty reporting**: When evidence is lacking, say so clearly
- **Methodology transparency**: Show your work so users can verify reasoning
- **Ideological agnosticism**: Treat all claims equally regardless of political alignment

### Handling Limitations
- **Inaccessible videos**: Clearly state what could not be verified
- **Language barriers**: Note when translation might affect accuracy
- **Visual-only claims**: Acknowledge limits when critical evidence is non-verbal
- **Breaking news**: Flag when evidence is still emerging and conclusions may change
- **Complex technical domains**: Defer to expert consensus when available

### Safety & Ethics
- **No hallucination**: Strict prohibition on inventing facts, quotes, or sources
- **Attribution**: Always credit original sources when possible
- **Context preservation**: When quoting, provide sufficient surrounding context
- **Correction protocol**: Clear process for when errors are found in agent output
- **Transparency about uncertainty**: Never overstate what evidence shows

---

## Getting Started Checklist

[ ] Set up Python environment with required packages
[ ] Obtain API keys for: YouTube, Google Fact Check Tools, NewsAPI, Semantic Scholar
[ ] Build video ingestion module (URL → transcript + metadata)
[ ] Develop basic claim extraction (identify declarative statements with numbers/entities)
[ ] Create simple evidence retriever (Google Custom Search + Wikipedia API)
[ ] Implement ReAct loop with 2-3 core actions (EXTRACT, SEARCH, EVALUATE)
[ ] Generate first complete report following the 12-step format
[ ] Test with 3-5 known fact-check examples
[ ] Refine based on test results
[ ] Add advanced features: context checking, statistical verification, confidence matrix
[ ] Conduct bias testing across political spectrum
[ ] Deploy as API service with documentation
[ ] Establish monitoring and user feedback loop

---

## Recommended Learning Resources

### Foundational Concepts
- [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)
- [Toolformer: Language Models Can Teach Themselves to Use Tools](https://arxiv.org/abs/2302.04761)
- [SayCan: Grounding Language in Robotic Affordances](https://arxiv.org/abs/2204.05086)
- [Reflexion: Language Agents with Verbal Reinforcement Learning](https://arxiv.org/abs/2303.11366)

### Fact-Checking Specifics
- [Duke Reporters' Lab: Classification of Fact-Checking](https://reporterslab.org/fact-checking/)
- [International Fact-Checking Network (IFCN) Code of Principles](https://ifcncodeofprinciples.poynter.org/)
- [MIT Media Lab: Contextual Analysis of Misinformation](https://www.media.mit.edu/projects/misinformation/overview/)
- [Stanford Internet Observatory: Election Integrity Partnership](https://io.stanford.edu/eip/)

### Technical Implementation
- [LangChain Documentation: Agents](https://python.langchain.com/docs/modules/agents/)
- [LlamaIndex: Agents](https://docs.llamaindex.ai/en/stable/module_guides/deploying/agents/)
- [Whisper.cpp: Efficient Speech-to-Text](https://ggerganov.com/whisper.cpp/)
- [FAISS: Similarity Search Library](https://github.com/facebookresearch/faiss)
- [Hugging Face Transformers: NER and QA](https://huggingface.co/docs/transformers/task_summary)

### Data Sources
- [Google Fact Check Tools API](https://developers.google.com/fact-check/tools/api)
- [Data.gov: U.S. Government Open Data](https://www.data.gov/)
- [Eurostat: European Statistics](https://ec.europa.eu/eurostat)
- [World Bank Open Data](https://data.worldbank.org/)
- [Pew Research Center Datasets](https://www.pewresearch.org/download-datasets/)
- [Semantic Scholar API](https://www.semanticscholar.org/product/api)
- [arXiv API](https://arxiv.org/help/api/index)

---

## Important Notes

1. **Iterative Development**: Start with a narrow scope (e.g., only YouTube videos, only statistical claims) before expanding to full specification.

2. **Evidence Over Speed**: Prioritize accuracy and thoroughness over rapid processing. A careful fact-check is more valuable than a quick but superficial one.

3. **Transparency is Key**: The agent's value lies not just in its conclusions, but in showing *how* it reached them. Always include reasoning steps, evidence sources, and confidence justifications.

4. **Human Oversight Recommended**: For high-stakes claims (medical, legal, safety-critical), consider having human experts review agent outputs before publication.

5. **Legal Considerations**: Respect platform terms of service, copyright laws (fair use for transcription/analysis), and data usage policies when accessing external sources.

6. **Continuous Learning**: The fact-checking landscape evolves rapidly. Schedule regular updates to:
   - Knowledge base connectors
   - Source reliability assessments
   - Manipulation detection techniques
   - Domain-specific verification rules (especially for fast-changing fields like public health)

This agent represents a complex but achievable application of agentic AI principles. By following this guide and maintaining a commitment to evidence-based, transparent analysis, you can build a system that significantly aids in navigating the complex information landscape of online video content.

*Remember: The goal is not to replace human judgment, but to augment it with systematic, scalable, and transparent fact-checking capabilities that help users make more informed decisions based on the best available evidence.*

graph TD
    A[Input Video URL] --> B[Transcription Module]
    B -->|yt-dlp download audio| C[Audio File]
    C -->|whisper.cpp| D[Timestamped Transcript]
    D --> E[Claim Extraction]
    E --> F[Evidence Retrieval System]
    F --> G[Evidence Evaluation & Status Assignment]
    G --> H[Context Manipulation & Statistical Verification]
    H --> I[Reasoning Loop ReAct]
    I --> J[Memory System]
    J --> K[Report Generation]
    K --> L[12-Step Fact-Check Report]
    style A fill:#f9f,stroke:#333
    style L fill:#9f9,stroke:#333