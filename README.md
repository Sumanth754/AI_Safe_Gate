# 🛡️ SafeGate: AI Security & Governance Proxy

SafeGate is a security-first API proxy designed to protect sensitive data (PII) before it reaches Large Language Models (LLMs). It acts as a middleman between your application and AI providers (like OpenAI), ensuring compliance, security, and cost-visibility.

---

## 🚀 Key Features
- **Automatic PII Scrubbing:** Detects and masks names, emails, phone numbers, SSNs, and API keys using **Microsoft Presidio**.
- **Real-time Audit Trail:** Logs every request, showing original vs. scrubbed text and the number of prevented leaks.
- **Cost & Token Tracking:** Monitors token usage and calculates costs across different models.
- **Governance Dashboard:** A clean, responsive UI to visualize security metrics and test scrubbing in real-time.
- **Mock Mode:** Test the system without an OpenAI API key.

## 🛠️ Tech Stack
- **Backend:** [FastAPI](https://fastapi.tiangolo.com/), [SQLAlchemy](https://www.sqlalchemy.org/)
- **Frontend:** HTML5, [Tailwind CSS](https://tailwindcss.com/)
- **Security Engine:** [Microsoft Presidio](https://microsoft.github.io/presidio/)
- **Database:** SQLite (Local/Development)

---

## 🏗️ Getting Started

### 1. Installation
```bash
git clone https://github.com/YOUR_USERNAME/SafeGate.git
cd SafeGate
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_lg
```

### 2. Run the Project
```bash
# Start the Backend (FastAPI)
python -m uvicorn backend.main:app --reload --port 8000
```
Open `frontend/index.html` in your browser to access the dashboard.

---

## 🌐 Deployment

### Backend (Render / Railway)
1. Push this repository to GitHub.
2. Connect your repo to [Render](https://render.com/).
3. Set the **Build Command**: `pip install -r requirements.txt && python -m spacy download en_core_web_lg`
4. Set the **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

### Frontend (GitHub Pages / Vercel)
1. Since it's a static `index.html`, you can deploy it directly to GitHub Pages or Vercel.
2. **Note:** Update the `API_BASE` variable in `frontend/index.html` to your deployed backend URL.

---

## 📄 License
This project is open-source and free to use.
