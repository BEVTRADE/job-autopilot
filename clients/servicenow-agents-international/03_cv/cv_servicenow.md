% HAKIM AREZKI, PhD
% AI CONSULTANT & DEVELOPER — GENAI AGENTS, PYTHON, AZURE, AI GOVERNANCE

Paris / Île-de-France · Freelance · 100% remote · +33 6 33 66 12 48 · harezki@kiras.fr · Available immediately

Hands-on AI consultant and developer with 12 years of experience in Data and Artificial Intelligence (15 including doctoral research), including long-running Generative AI projects in production since 2020 in regulated banking (BIL) and large industrial groups (TotalEnergies). PhD from CentraleSupélec.

Builds GenAI agents from scratch, from concept and technical design to Python code in production: tool calling, state management, memory, guardrails, human-in-the-loop validation, and integration with enterprise systems through REST APIs. Recent agent work targets IT and operational processes: AI agents for IT teams (coding, compliance, application architecture) at BIL, and agents analysing operational incident reports at TotalEnergies.

Strong Azure track record: Azure OpenAI, Azure AI Studio, Azure Document Intelligence, Azure Data Lake, Data Factory, Functions, Key Vault, Azure DevOps.

Designs and runs AI governance frameworks that teams actually use: intake and classification of new AI requests by risk level, model selection and approval, access policies, evaluation gates before go-live, audit trails and usage registers — aligned with GDPR, DORA and the EU AI Act.

## Relevance to this assignment

- **GenAI agent conception and development**: agents with orchestration, tool selection, memory, guardrails and bounded execution (iteration caps, token budgets, timeouts), delivered in Python and documented for handover.
- **Incident analysis agents**: at TotalEnergies, MCP servers and AI agents automatically analysing daily operational reports and operational incidents; at RATP, real-time supervision and incident management platform with incident-duration prediction and log anomaly detection.
- **Agents for IT processes**: at BIL, AI agents supporting IT teams on coding, compliance and application architecture, integrated with internal APIs and data sources.
- **API integration**: REST API design and integration (FastAPI), MCP servers exposing enterprise data and internal APIs to agents, event-driven integration (Kafka, Redis Streams).
- **Governance framework for new service requests**: BIL AI governance framework — request intake, risk classification, model approval, usage rules, human validation, evaluation gates, traceability.
- **Best-practice AI advice**: model selection by quality, confidentiality, latency and cost; prompt versioning; evaluation frameworks; LLM-specific risks (hallucination, prompt injection, data leakage).

## GenAI delivery

- **BIL, Banque Internationale à Luxembourg** (since January 2026): enterprise GenAI platform (GENIA), multi-LLM architecture, AI agents for IT teams, RAG and Document AI, MCP servers, LLMOps, AI governance framework, RBAC, GDPR, DORA.
- **TotalEnergies** (2020-2025): group-scale industrialisation of GenAI and ML use cases on Azure and Databricks: AI agents, RAG pipelines, multimodal Document AI, MCP servers for incident and daily-report analysis, MLOps and LLMOps.

## Core skills

### GenAI agents — design and development
- Agent design from scratch: orchestration, state management, tool selection and tool calling, memory
- Structured outputs and consistency checks, suitable for generating structured artefacts (tickets, summaries, classifications)
- Human-in-the-loop validation on sensitive actions, explicit interruption points
- Bounded execution: iteration caps, token budgets, timeouts, stop on failure
- Agent observability: traces, cost, latency, failure rate (Langfuse, OpenTelemetry)
- Frameworks: LangChain, LlamaIndex, Semantic Kernel, Model Context Protocol

### Python development and API integration
- Production Python: clean architecture, testing, packaging, CI/CD
- REST API design and integration with FastAPI; authentication, error handling, retries, rate limiting
- MCP servers exposing enterprise data and internal APIs to agents
- Event-driven integration: Kafka, Redis Streams; microservices architectures
- Data processing: SQL, Spark, PySpark, Airflow, dbt

### Incident and operational data analysis
- Automated analysis of incident reports and operational logs with LLMs and agents
- Classification, summarisation and root-cause-oriented extraction from unstructured text
- Incident-duration prediction and anomaly detection on logs (ML)
- RAG over knowledge bases and past incidents: hybrid search, reranking, metadata filtering, document-level access control

### Azure platform
- Azure OpenAI, Azure AI Studio, Microsoft Copilot and Copilot Studio
- Azure Document Intelligence, Cognitive Search
- Azure Data Lake, Data Factory, Synapse, Event Hub, Functions, Key Vault
- Azure DevOps, Terraform, Docker, Kubernetes

### AI governance framework and best practices
- Governance framework design and maintenance: intake of new requests, risk classification, ownership, approval workflow, usage register
- Model selection and approval, access policies, usage rules
- Evaluation gates before go-live: RAGAS, faithfulness, hallucination rate, latency p50/p95, unit cost
- LLM risks: hallucination, prompt injection, data leakage, tool exfiltration; least privilege on tools and sources
- Auditability and traceability of AI outputs; GDPR, DORA, EU AI Act risk classification translated into verifiable controls
- Documentation, reusable templates and team enablement

## Technology environment

GenAI: Azure OpenAI, OpenAI, Claude, Mistral, LLaMA, Hugging Face, Copilot Studio · Frameworks: LangChain, LlamaIndex, Semantic Kernel, MCP, MLflow, PyTorch, scikit-learn · RAG: FAISS, PGVector, Azure Cognitive Search, OpenSearch, BM25, reranking, RAGAS · Azure: OpenAI, AI Studio, Document Intelligence, Data Lake, Data Factory, Functions, Key Vault, DevOps · Python & APIs: FastAPI, REST, Kafka, Redis Streams, microservices · Data: Snowflake, Databricks, SQL, PySpark, Airflow, dbt · DevOps & observability: Docker, Kubernetes, Terraform, GitHub Actions, GitLab CI/CD, Langfuse, OpenTelemetry, Prometheus, Grafana · Delivery: Agile, Scrum, Kanban, SAFe, Jira, Confluence

## Professional experience

### AI Architect & Technical Lead — BIL, Banque Internationale à Luxembourg
*January 2026 to present*

Design, development and operation of GENIA, the bank's enterprise Data & AI platform, delivering governed Generative AI capabilities in a regulated banking environment (ECB SREP scope). Use cases focus on AI agents for IT: coding, compliance, application architecture and information systems.

- Developed AI agents in Python querying models, document bases and internal APIs, with state management, tool selection, guardrails and human validation on sensitive actions.
- Designed and built MCP servers exposing client metadata from Snowflake to the platform's agents.
- Built the multi-LLM layer with routing, caching and fallback to control latency, quality and cost, monitored through p50/p95, error rate, consumption and unit cost.
- Built RAG and Document AI pipelines: ingestion, parsing, chunking, embeddings, hybrid search, reranking, metadata filtering and document-level access control.
- Designed shared, versioned system prompts and templates with structured outputs and consistency checks.
- Contributed to the AI governance framework: intake of new use cases, risk classification, model selection and approval, access policies, usage rules, alignment with Data and Digital governance bodies.
- Set up the evaluation framework and go-live gates: retrieval and RAG metrics, factuality, hallucination rate, latency and cost.
- LLMOps industrialisation: containerisation, continuous delivery of models and prompts, observability.
- Compliance: RBAC, Row-Level Security, encryption, GDPR, DORA, auditability of AI outputs.

### Lead Data & AI Platform — TotalEnergies
*December 2020 to December 2025*

Group-scale industrialisation of Machine Learning and Generative AI use cases on an enterprise Data Platform (Azure, Databricks, Snowflake) serving industrial operations, retail and HR.

- Moved around fifteen Data, ML and GenAI use cases from experimentation to production.
- Designed and developed MCP servers exposing drilling data, enabling AI agents to automatically analyse daily reports and operational incidents.
- Built Document AI, OCR and RAG pipelines for technical and operational document corpora, and multimodal agents combining OCR, vision and LLMs.
- Built training, evaluation and deployment pipelines with MLflow, CI/CD, monitoring and versioning.
- Built data pipelines on Databricks, PySpark, Airflow and dbt, and Kafka event-driven architectures.
- Industrialised infrastructure with Terraform, Docker and CI/CD, with observability and performance tuning.
- Defined group architecture standards, ADRs and MLOps practices; led a multi-disciplinary team of around 20 people.
- Enabled business teams on AI services: hands-on workshops, shared prompt templates, operating guides and handover to internal teams.

### Data & AI Technical Lead, MSM programme — RATP, with Alstom, Renault and IRT SystemX
*August 2018 to December 2020*

- Designed microservices architectures for real-time supervision and incident management.
- Built a multi-layer Data Lake on Azure for scalable ingestion, processing and analytics, with secured Kafka streams.
- Developed predictive models for passenger flows, incident duration and operational planning.
- Implemented anomaly detection and log analysis for data quality and compliance.
- Delivered an operational smart-mobility supervision demonstrator at Paris-La Défense; IEEE publication (DSD 2020).

### Lead Data Science & Governance — BPCE, Banking & Insurance
*January 2017 to August 2018*

- Built an end-to-end AI-driven fraud detection engine and automated alert, sanctions and embargo workflows.
- Developed exact, fuzzy and phonetic matching between suspect entities and clients; reduced false positives with TF-IDF and hashing vectorisation.
- Deployed the enterprise data dictionary and lineage on Apache Atlas and ELK; GDPR compliance of processing chains.

### Lead Data Scientist — Luxury Retail
*September 2015 to January 2017*

- Customer intelligence engine: profile classification, churn modelling, collaborative-filtering recommendation; Kafka stream capture; model code industrialisation.

### Data Scientist — Beamlabs / Française des Jeux
*November 2014 to September 2015*

- Real-time marketing Big Data foundation (streaming ingestion, ElasticSearch) and real-time recommendation engine.

### R&D Engineer, PhD — CentraleSupélec, Université Paris-Saclay
*February 2010 to October 2014*

- Machine Learning applied to photovoltaic cell optimisation and transistor modelling; simulation and data analysis algorithms.

## Education

- PhD, CentraleSupélec, Université Paris-Saclay (2011-2014)
- Master of Sciences, Université Pierre et Marie Curie, Paris VI (2010-2011)
- Master's degree in Engineering Sciences, Université Paris Diderot, Paris VII (2009-2010)

## Languages

French: native · English: fluent professional proficiency

## Publications and speaking

18 peer-reviewed publications, 7 conference talks · *Architecture of a Public Transport Supervision System Using Hybridization Models Based on Real and Predictive Data*, IEEE DSD 2020 · Speaker, Big Data Paris 2018
