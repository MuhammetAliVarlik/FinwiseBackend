# Finwise Scribe: Symbolic Generative AI for Market Forecasting

![Status](https://img.shields.io/badge/Status-Prototype_v1-blue)
![Architecture](https://img.shields.io/badge/Architecture-Microservices-orange)
![AI Model](https://img.shields.io/badge/Model-Llama--3_Quantized-green)
![Tech Stack](https://img.shields.io/badge/Stack-FastAPI_React_Docker-blueviolet)

**Finwise Scribe** is a financial reasoning engine that treats market data as a *language*. Unlike traditional numerical models (LSTM/ARIMA) that output raw numbers, Scribe tokenizes price action into discrete semantic symbols (e.g., `P_SURGE`, `P_STABLE`) and uses a Fine-Tuned Large Language Model (Llama-3) to reason about future volatility states.

---

## 🚀 Key Innovation: Symbolic Market Modeling

Standard AI views finance as **Time-Series Regression**. Scribe views finance as **Pattern Recognition**.

1.  **Ingestion:** Raw OHLCV data is fetched (Stooq/Yahoo Finance).
2.  **Symbolization:** Numerical data is discretely quantized into a vocabulary of tokens.
    * *Example:* `[Close: 150.0, Vol: High]` $\rightarrow$ `P_SURGE_V_HIGH`
3.  **Inference:** The Llama-3 model processes the *token sequence* (context window) to predict the next semantic state and generate a natural language explanation.

---

## 🛠️ System Architecture

The project utilizes a **4-Container Microservice Architecture** to ensure scalability and separation of concerns:

| Service | Port | Description |
| :--- | :--- | :--- |
| **Frontend** | `3000` | **React + Vite**. Interactive dashboard for charting and AI chat. |
| **API Gateway** | `8000` | **FastAPI**. Monolith handling Auth, User Management, and Routing. |
| **Scribe Engine** | `8001` | **FastAPI**. Dedicated ML service for Symbolization and Prompt Engineering. |
| **Inference Node** | `11434`| **Ollama**. GPU-accelerated container serving the `finwise_scribe_v1` model. |
| **Database** | `5432` | **PostgreSQL**. Persistent storage for user data and stock caches. |

---

## 💻 Quick Start

### Prerequisites
* **Docker Desktop** (with WSL2 backend on Windows)
* **NVIDIA GPU** (Recommended for Ollama acceleration)

### Installation
1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/MuhammetAliVarlik/FinwiseBackend.git](https://github.com/MuhammetAliVarlik/FinwiseBackend.git)
    cd finwise-scribe
    ```

2.  **Launch the Stack:**
    ```bash
    docker-compose up --build
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

The **Scribe Agent** is capable of two distinct modes of operation:

### 1. Predictive Forecasting
* **Input:** Stock Symbol (e.g., "MSFT")
* **Process:** Fetches last 60 days of data $\rightarrow$ Symbolizes $\rightarrow$ Predicts next token.
* **Output:** `P_SURGE` (High probability of upward momentum) or `P_STABLE`.

### 2. Context-Aware Chat
* **Input:** Natural Language Query (e.g., *"Why is the market volatile?"*)
* **Process:** The engine injects the *Symbolized Market Context* into the System Prompt.
* **Output:** A grounded explanation citing technical patterns visible in the token sequence.

---

## 📂 Project Structure

```text
finwise_scribe/
├── backend/            # API Gateway (Auth, Users, Stock Proxy)
├── frontend/           # React Dashboard (Vite, Tailwind, Charts)
├── llm_service/        # The "Brain" (Symbolizer logic, Ollama connector)
├── models/             # GGUF Model files and Modelfiles
├── docker-compose.yml  # Orchestration Config
└── README.md           # This file
```

---

## 📜 License
This project is part of a Master's Thesis research and is open-sourced under the MIT License.
