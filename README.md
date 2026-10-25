# 🎫 Customer Ticket Automation System

An enterprise-ready, AI-driven **Customer Support & IT Incident Resolution Platform** with Human-in-the-Loop (HITL) review, powered by **FastAPI**, **LangGraph**, **React 19 + Vite**, and a **Distributed Multi-Tier LLM Fallback System** on OpenRouter / Gemini.

Made with ❤️ by [Hamed](https://www.linkedin.com/in/devhamed/)

---

## 🌟 Key Features

- **React 19 + Vite Frontend SPA:**
  - Modern, high-performance dark aesthetic with zero-dependency SVG icons.
  - Real-time KPI metrics (Open, In Progress, Resolved, Pending Human Review).
  - Multi-tenant switching, search, status/priority filters, and inline modal ticket management.
  - Interactive ticket chat & internal staff notes synchronized directly to persistent database.
- **Enterprise Multi-Tenant Isolation:**
  - Strict tenant boundary enforcement (`tenant_id`).
  - Role-based access control (`Customer`, `Support Specialist`, `Lead Support Agent`).
  - Cross-tenant data leakage prevention across tickets, episodic memories, and conversation threads.
- **Episodic Memory System:**
  - Persistent, tenant-isolated memory capturing past resolutions and customer context.
  - Low-latency keyword and recency relevance ranking algorithm.
  - Automatic knowledge capture upon ticket resolution and dynamic injection into agent retrieval.
- **Automated TTL Reaper Worker:**
  - Background worker running periodically in FastAPI lifespan.
  - Sweeps expired guest sessions, temporary tickets, and transient memories.
  - Role-protected manual trigger endpoint (`POST /reaper/trigger`).
- **Distributed Multi-Tier LLM Fallback (OpenRouter):**
  - **Tier 1:** Google Gemini 2.5 Flash (Fast, high-precision structured classification)
  - **Tier 2:** Qwen 2.5 72B Instruct (Flagship open weights model)
  - **Tier 3:** Meta LLaMA 3.3 70B (High-capability open-source model)
  - **Tier 4:** OpenRouter Free Router (Zero-cost dynamic fallback)
  - *Automated failover:* If any provider encounters rate limits (`429`), timeouts, or outages, the system cascades without dropping requests.
- **Multi-Device Database Persistence:**
  - Zero reliance on browser `localStorage` or container disk for chats and notes.
  - 100% database-backed models (`TicketMessage`, `TicketNote`).
  - Seamlessly rehydrates ticket history when logging in from any new device, browser, or tab.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    Client["React 19 SPA (Vite)\n(Vercel / localhost:3000)"] -->|REST API + Bearer JWT| API["FastAPI Backend\n(Render / localhost:8001)"]
    API --> Services["Domain Service Layer\n(TicketService, ThreadService, AgentService, MemoryService, ReaperService)"]

    Services --> DB[("Database\n(Neon PostgreSQL / SQLite fallback)")]

    subgraph Agentic Pipeline ["LangGraph Execution Engine"]
        CI["1. Classify Incident\n(Category, Intent, Urgency)"]
        Router1{"High / Critical Urgency?"}
        Manual["Manual Human Handling"]
        Search["2. Retrieve Knowledge & Episodic Memory"]
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

    subgraph Distributed LLM Engine ["Multi-Tier LLM Fallback"]
        T1["Tier 1: Gemini 2.5 Flash"] -->|Failover| T2["Tier 2: Qwen 2.5 72B"]
        T2 -->|Failover| T3["Tier 3: LLaMA 3.3 70B"]
        T3 -->|Failover| T4["Tier 4: OpenRouter Free Router"]
    end

    CI -.-> Distributed LLM Engine
    Draft -.-> Distributed LLM Engine
```

---

## 📁 Repository Structure

```
Customer-Ticket-Automation-System/
├── Backend/                         # FastAPI Backend Application
│   ├── src/
│   │   ├── main.py                  # FastAPI entrypoint, lifespan & CORS
│   │   ├── config.py                # Pydantic v2 environment settings
│   │   ├── database.py              # PostgreSQL & SQLite fallback engine
│   │   ├── graph.py                 # LangGraph state machine & checkpointer
│   │   ├── llms.py                  # Distributed multi-tier fallback LLM client
│   │   ├── nodes.py                 # Incident classification & routing nodes
│   │   ├── retrieval.py             # Knowledge retrieval pipeline
│   │   ├── seed.py                  # Database seeder with bcrypt hashing
│   │   ├── state.py                 # LangGraph state schemas
│   │   ├── models/                  # SQLAlchemy models (User, Ticket, Note, Message, Memory)
│   │   ├── repositories/            # Data access layer
│   │   ├── routes/                  # API endpoints (auth, tickets, agent, memories, reaper)
│   │   ├── schemas/                 # Pydantic validation schemas
│   │   ├── services/                # Business logic & background workers
│   │   └── utils/                   # JWT handlers, password hashing, DB migrations
│   ├── tests/                       # Automated test suites
│   ├── requirements.txt             # Python backend dependencies
│   ├── langgraph.json               # LangGraph configuration
│   └── app.py                       # Legacy Streamlit reference
├── Frontend/                        # React 19 + Vite Frontend SPA
│   ├── src/
│   │   ├── components/              # React components (Dashboard, Modals, Navbar, Auth)
│   │   ├── context/                 # AuthContext & session state management
│   │   ├── icons.jsx                # Zero-dependency SVG icon system
│   │   ├── api.js                   # Unified API client with automatic token attachment
│   │   ├── App.jsx                  # Main application routing & view orchestration
│   │   └── main.jsx                 # React root mount
│   ├── package.json                 # Node.js dependencies & scripts
│   ├── vite.config.js               # Vite bundler & reverse proxy configuration
│   └── vercel.json                  # Vercel SPA routing rewrite rules
├── docker/                          # Containerization Configurations
│   ├── Dockerfile.api               # Multi-stage production container for FastAPI
│   ├── Dockerfile.ui                # Multi-stage container with Nginx for React SPA
│   ├── nginx.conf                   # Nginx reverse proxy & SPA fallback configuration
│   └── docker-compose.yml           # Full-stack local orchestration (Postgres, API, UI)
├── .env.example                     # Environment configuration template
└── README.md                        # Documentation
```

---

## 🔑 Default Seeded Accounts

The database automatically initializes tables and seeds mock accounts on first launch:

| Username | Password | Full Name | Role | Tenant | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `sai` | `sai123` | Hamed | Lead Support Agent | `default` | Full administrative & HITL review access |
| `ramya` | `ramya123` | Ramya | Support Specialist | `default` | Incident response & ticket editing |
| `customer1` | `customer123` | John Customer | Customer | `default` | Standard customer ticket view |
| `acme_user` | `acme123` | Acme Employee | Customer | `tenant_acme` | Isolated multi-tenant demonstration user |

> **Guest Access:** You can also click **"Continue as Guest (Demo)"** on the login page to immediately test the application with a temporary guest session governed by the 24-hour automated TTL Reaper.

---

## 🚀 Local Development Setup

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ (Node 20 recommended) & npm

### 2. Backend Setup
```bash
# Clone the repository
git clone https://github.com/Hamed18/Customer-Ticket-Automation-System.git
cd Customer-Ticket-Automation-System

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install backend dependencies
pip install -r Backend/requirements.txt

# Configure environment variables
cp .env.example .env

# Start FastAPI backend server
uvicorn src.main:app --host 127.0.0.1 --port 8001 --reload --app-dir Backend
```
- API Documentation: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
- Health Check: [http://127.0.0.1:8001/health](http://127.0.0.1:8001/health)

### 3. Frontend Setup
```bash
# Open a new terminal
cd Frontend

# Install frontend dependencies
npm install

# Start Vite development server
npm run dev
```
- Frontend Application: [http://localhost:3000](http://localhost:3000)

### 4. Running with Docker Compose
To run PostgreSQL, the FastAPI Backend, and the React Frontend together with a single command:
```bash
docker compose -f docker/docker-compose.yml up --build
```
- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend API: [http://localhost:8001](http://localhost:8001)

---

## 🌐 Production Deployment Guide (Free Cloud Stack)

### Stack Architecture
- **Database:** [Neon](https://neon.tech/) (Serverless PostgreSQL with 0.5 GiB free storage)
- **Backend:** [Render](https://render.com/) (Free Web Service for Python / FastAPI)
- **Frontend:** [Vercel](https://vercel.com/) (Free Edge Hosting for Vite React SPA)

---

### Step 1: Provision Neon PostgreSQL
1. Sign up at [neon.tech](https://neon.tech/).
2. Create a new project (e.g. `ticket-system-db`).
3. Under the **Dashboard**, copy your PostgreSQL connection string:
   ```
   postgresql://[user]:[password]@[endpoint].neon.tech/[dbname]?sslmode=require
   ```
4. *Note:* The backend automatically formats this connection string for SQLAlchemy compatibility (`postgresql+psycopg2://`).

---

### Step 2: Deploy Backend on Render
1. Sign in to [render.com](https://render.com/) and click **New +** &rarr; **Web Service**.
2. Connect your GitHub repository: `Customer-Ticket-Automation-System`.
3. Configure settings:
   - **Name:** `ticket-system-api` (or your choice)
   - **Language:** `Python 3`
   - **Branch:** `main`
   - **Root Directory:** `Backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** `Free`
4. Add the following **Environment Variables**:
   - `DATABASE_URL`: *(Your Neon PostgreSQL connection string from Step 1)*
   - `SECRET_KEY`: *(Generate a secure random string, e.g. `openssl rand -hex 32`)*
   - `OPENROUTER_API_KEY`: *(Your OpenRouter API Key)*
   - `GOOGLE_API_KEY`: *(Optional, for direct Gemini fallback)*
   - `CORS_ORIGINS`: `https://your-frontend.vercel.app,http://localhost:3000` *(You can update this after Step 3)*
5. Click **Create Web Service**. Once deployed, copy your Render URL:
   `https://ticket-system-api.onrender.com`

> **Cold Start Optimization:** Render free instances spin down after 15 minutes of inactivity. Set up a free monitor on [UptimeRobot](https://uptimerobot.com/) or [cron-job.org](https://cron-job.org/) to ping `https://<your-render-url>/health` every 10 minutes to prevent sleep.

---

### Step 3: Deploy Frontend on Vercel
1. Sign in to [vercel.com](https://vercel.com/) and click **Add New** &rarr; **Project**.
2. Import your GitHub repository: `Customer-Ticket-Automation-System`.
3. Configure project settings:
   - **Framework Preset:** `Vite`
   - **Root Directory:** Click Edit and select `Frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
4. Under **Environment Variables**, add:
   - `VITE_API_URL`: `https://ticket-system-api.onrender.com` *(Your Render backend URL from Step 2, without trailing slash)*
5. Click **Deploy**. Vercel will build and deploy your React SPA in seconds with global CDN distribution and SPA client-side routing.

---

## 🔐 Required API Keys & Credentials Summary

| Variable Name | Required | Provider / Source | Purpose |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | **Yes** (Prod) | [Neon](https://neon.tech/) | Persistent serverless PostgreSQL connection string |
| `SECRET_KEY` | **Yes** | User Generated | Cryptographic key for signing JWT tokens |
| `OPENROUTER_API_KEY` | **Yes** | [OpenRouter](https://openrouter.ai/) | Multi-tier LLM fallback (Qwen, LLaMA, Free router) |
| `GOOGLE_API_KEY` | Optional | [Google AI Studio](https://aistudio.google.com/) | Direct Gemini Flash inference |
| `VITE_API_URL` | **Yes** (Vercel) | Render URL | Tells React SPA where to send API requests |
| `CORS_ORIGINS` | Optional | Render Settings | Allowed frontend domains (defaults permit Vercel domains) |

---

## 🧪 Testing & Verification

Run the comprehensive test suites from the root repository:

```bash
# 1. Auth, Guest Session & Multi-Tenant Isolation
python Backend/tests/test_auth_and_isolation.py

# 2. Episodic Memory, TTL Reaper & Penetration Security
python Backend/tests/test_consolidation.py

# 3. Multi-Browser Zero-LocalStorage Persistence
python Backend/tests/test_multi_browser_persistence.py
```

---

## 📄 License
This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

---

**Developed & Maintained by [Hamed](https://www.linkedin.com/in/devhamed/)**
