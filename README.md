# Finwise Scribe: Symbolic Generative AI for Market Forecasting

![Status](https://img.shields.io/badge/Status-Beta_v1.2-blue)
![Architecture](https://img.shields.io/badge/Architecture-Async_Microservices-orange)
![AI Model](https://img.shields.io/badge/Model-Neuro--Symbolic_Hybrid-green)
![Tech Stack](https://img.shields.io/badge/Stack-FastAPI_React_Redis_Celery-blueviolet)

**Finwise Scribe** is a financial reasoning engine that treats market data as a *language*. Unlike traditional numerical models (LSTM/ARIMA) that output raw numbers, Scribe tokenizes price action into discrete semantic symbols (e.g., `P_SURGE`, `P_STABLE`) and uses a Fine-Tuned Large Language Model to reason about future volatility states.

The platform employs a **Fire-and-Forget Architecture**, allowing it to handle computationally intensive AI inference tasks asynchronously without blocking the user experience.

---

## 🚀 Key Innovation: Symbolic Market Modeling

Standard AI views finance as **Time-Series Regression**. Scribe views finance as **Pattern Recognition**.

1.  **Ingestion:** Raw OHLCV data is fetched (Stooq/Yahoo Finance).
2.  **Symbolization:** Numerical data is discretely quantized into a vocabulary of tokens.
    * *Example:* `[Close: 150.0, Vol: High]` $\rightarrow$ `P_SURGE_V_HIGH`
3.  **Inference:** The Neuro-Symbolic Engine processes the *token sequence* to predict the next semantic state and generate a natural language explanation.

---

## 🛠️ System Architecture

The project utilizes an **Asynchronous Event-Driven Architecture** composed of 6 microservices. This design ensures that heavy AI computations do not freeze the API or the User Interface.

| Service | Port | Description |
| :--- | :--- | :--- |
| **Frontend** | `3000` | **React + Vite**. Interactive dashboard with Async Polling for real-time updates. |
| **API Gateway** | `8000` | **FastAPI (Async)**. Handles Auth, Rate Limiting, and Task Dispatching. |
| **Task Queue** | `N/A` | **Celery Worker**. Executes background AI inference jobs. |
| **Message Broker** | `6379` | **Redis**. Manages job queues and inter-service communication. |
| **Scribe Engine** | `8001` | **FastAPI**. Dedicated ML service for Symbolization and Prompt Engineering. |
| **Inference Node** | `11434`| **Ollama**. GPU-accelerated container serving the Quantized LLM. |
| **Database** | `5432` | **PostgreSQL**. Persistent storage for users, forecasts, and cache. |

### ⚡ asynchronous Workflow
1.  **Trigger:** User requests a forecast. API returns a `task_id` immediately (Non-blocking).
2.  **Process:** Redis queues the job; The Celery Worker picks it up and queries the AI Engine.
3.  **Update:** The Frontend polls the API and renders the result once the AI finishes "thinking."

---

## 💻 Quick Start

### Prerequisites
* **Docker Desktop** (v4.20+)
* **NVIDIA GPU** (Recommended for local inference acceleration)

### Installation
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/MuhammetAliVarlik/FinwiseBackend.git
    cd finwise-scribe
    ```

2.  **Launch the Stack:**
    ```bash
    docker-compose up -d --build
    ```

3.  **Initialize the Model (First Time Only):**
    Once containers are running, load the custom model into Ollama:
    ```bash
    docker exec -it finwise_ollama ollama create finwise_scribe_v1 -f /models/Modelfile
    ```

4.  **Access the Dashboard:**
    Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🧠 AI Agent Capabilities

The **Scribe Agent** operates in two distinct modes:

### 1. Shadow Mode Forecasting
* **Input:** Stock Symbol (e.g., "NVDA")
* **Process:** Fetches historical data $\rightarrow$ Symbolizes price action $\rightarrow$ Runs LSTM + LLM Hybrid Inference.
* **Output:** `P_SURGE` (High probability of upward momentum) or `P_CRASH` (Volatility warning).

### 2. Context-Aware Chat
* **Input:** Natural Language Query (e.g., *"Why is the market volatile?"*)
* **Process:** The engine injects the *Symbolized Market Context* into the System Prompt.
* **Output:** A grounded explanation citing specific technical patterns (e.g., "Volume spike detected").

---

## 📂 Project Structure

```text
finwise_scribe/
├── backend/            # API Gateway & Celery Worker
│   ├── app/tasks.py    # Background AI Jobs
│   └── app/worker.py   # Celery Configuration
├── frontend/           # React Dashboard (Vite, Tailwind)
├── llm_service/        # The "Brain" (Symbolizer logic)
├── models/             # GGUF Model files and Modelfiles
├── docker-compose.yml  # Full Stack Orchestration
└── README.md           # Project Documentation

---

## 📜 License
This project is part of a Master's Thesis research and is open-sourced under the MIT License.
