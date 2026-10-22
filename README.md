# 🎫 Customer Ticket Automation System

An enterprise-ready, AI-driven **Customer Support & IT Incident Resolution Platform** with Human-in-the-Loop (HITL) review, powered by **FastAPI**, **LangGraph**, **Streamlit**, and a **Distributed Multi-Tier LLM Fallback System** on OpenRouter.

Made with ❤️ by [Hamed](https://www.linkedin.com/in/devhamed/)

---

## 🌟 Key Highlights

- **Multi-Tier Distributed LLM Fallback (OpenRouter):**
  - **Tier 1:** Google Gemini 2.5 Flash (Fast, high-precision structured classification)
  - **Tier 2:** Qwen 2.5 72B Instruct (Flagship open weights model)
  - **Tier 3:** Meta LLaMA 3.3 70B (High-capability open-source model)
  - **Tier 4:** OpenRouter Free Router (Zero-cost dynamic fallback)
  - *Automated failover:* If any provider encounters rate limits (`429`), timeouts, or outages, the system instantly cascades to the next tier without dropping requests.
- **Human-in-the-Loop (HITL) Workflow:**
  - Automated urgency routing (High/Critical urgency tickets route to manual assignment).
  - Low confidence AI drafts automatically pause for human review and diff comparison.
  - One-click approval or inline editing directly updates tickets and resumes the LangGraph state machine.
- **Production Layered Architecture:**
  - Decoupled **Repository Pattern** and **Service Layer** with zero self-referencing HTTP deadlocks.
  - Hybrid Database Engine: Automatic connection to PostgreSQL with zero-config local SQLite fallback.
  - Secure JWT authentication with native `bcrypt` password hashing.
  - Interactive **FastAPI REST API** with `/health` and `/ready` probes.
  - Modern **Streamlit Dashboard** featuring real-time KPI metrics, Plotly visualizations, ticket filters, and conversation diff tools.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    Client["Streamlit Dashboard\n(localhost:8501)"] -->|REST API + Bearer JWT| API["FastAPI Backend\n(localhost:8001)"]
    API --> Services["Service & Repository Layer\n(TicketService, ThreadService, AgentService)"]

    Services --> DB[("Database\n(PostgreSQL / SQLite fallback)")]

    subgraph Agentic Pipeline ["LangGraph Execution Engine"]
        CI["1. Classify Incident\n(Category, Intent, Urgency)"]
        Router1{"High / Critical Urgency?"}
        Manual["Manual Human Handling"]
        Search["2. Retrieve Knowledge Base"]
        Draft["3. Draft Response (RAG)"]
        Eval["4. Evaluate Confidence"]
        Router2{"Confidence > 75%?"}
        Auto["Auto-Resolve Ticket"]
        Review["Human Review & Diff"]
        Interrupt["HITL Approval Interrupt"]
        Approve["Deliver Approved Response"]
    end

    Services --> Agentic Pipeline
    CI --> Router1
    Router1 -->|Yes| Manual
    Router1 -->|No| Search --> Draft --> Eval --> Router2
    Router2 -->|Yes| Auto
    Router2 -->|No| Review --> Interrupt --> Approve

    subgraph Distributed LLM Engine ["OpenRouter Multi-Tier Fallback"]
        T1["Tier 1: Gemini 2.5 Flash"] -->|Failover| T2["Tier 2: Qwen 2.5 72B"]
        T2 -->|Failover| T3["Tier 3: LLaMA 3.3 70B OSS"]
        T3 -->|Failover| T4["Tier 4: OpenRouter Free Router"]
    end

    CI -.-> Distributed LLM Engine
    Draft -.-> Distributed LLM Engine
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10+ (Recommended: Python 3.11 / 3.12 / 3.13)
- An [OpenRouter API Key](https://openrouter.ai/keys)

### 2. Installation
Clone the repository and install the dependencies:
```bash
git clone https://github.com/Hamed18/Customer-Ticket-Automation-System.git
cd Customer-Ticket-Automation-System

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env` in the project root:
```bash
cp .env.example .env
```
Configure your keys in `.env`:
```env
OPENROUTER_API_KEY=sk-or-v1-your_openrouter_api_key_here
API_URL=http://127.0.0.1:8001
SECRET_KEY=your_secure_jwt_secret_key_here
```

### 4. Running the Application Locally

#### Start the FastAPI Backend:
```bash
uvicorn src.main:app --host 127.0.0.1 --port 8001 --reload
```
- API Docs: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
- Health Probe: [http://127.0.0.1:8001/health](http://127.0.0.1:8001/health)

#### Start the Streamlit Dashboard:
```bash
streamlit run app.py --server.port 8501
```
- Dashboard URL: [http://127.0.0.1:8501](http://127.0.0.1:8501)

---

## 🔑 Default Seeded Accounts

The database automatically initializes and seeds mock tickets and support agent accounts:

| Username | Password | Full Name | Role |
| :--- | :--- | :--- | :--- |
| `sai` | `sai123` | Hamed | Lead Support Agent |
| `ramya` | `ramya123` | Ramya | Support Specialist |
| `sandy` | `sandy123` | Sandy | Tier 2 Support |

---

## 📁 Repository Structure

```
Customer-Ticket-Automation-System/
├── app.py                     # Streamlit navigation entrypoint
├── pages/
│   ├── home.py                # Operations & analytics dashboard
│   ├── view_tickets.py        # Ticket listings, search & status filters
│   └── ticket_details.py      # Detailed ticket view, diff & HITL actions
├── src/
│   ├── main.py                # FastAPI server entry & lifespan manager
│   ├── config.py              # Centralized environment settings
│   ├── database.py            # Database engine (PostgreSQL + SQLite fallback)
│   ├── llms.py                # Distributed multi-tier fallback LLM system
│   ├── graph.py               # LangGraph compiled state machine & checkpointer
│   ├── nodes.py               # Incident classification & routing nodes
│   ├── retrieval.py           # Knowledge base retrieval pipeline
│   ├── seed.py                # Database seeder with native bcrypt hashing
│   ├── state.py               # State & context schemas
│   ├── ui_utils.py            # Streamlit API client & auth utilities
│   ├── models/                # SQLAlchemy ORM schemas (Users, Tickets, Threads)
│   ├── repositories/          # Data access layer (TicketRepository, ThreadRepository)
│   ├── routes/                # FastAPI routers (auth, tickets, agent, threads)
│   └── services/              # Domain services (TicketService, ThreadService, AgentService)
├── DockerFile.api             # Container image for FastAPI backend
├── DockerFile.ui              # Container image for Streamlit dashboard
├── requirements.txt           # Project dependencies
└── README.md                  # Project documentation
```

---

## 📄 License
This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

---

**Developed & Maintained by [Hamed](https://www.linkedin.com/in/devhamed/)**
