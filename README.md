# ScholarAI — Master's Scholarship Finder Agent

An autonomous multi-agent AI system designed to help prospective graduate students discover, evaluate, and strategically win fully-funded international Master's degree scholarships.

---

## 🌟 Key Capabilities

1. **Profile Synthesizer Agent**: Normalizes international GPAs (4.0, 5.0, 10.0, or 100 percentage scales), analyzes academic tiers, assesses professional experience thresholds, and extracts eligibility tags.
2. **Live Discovery Agent (Google Search Grounded)**:
   - Queries Google Gemini with **live Google Search grounding** to discover 2025/2026/2027 application cycles, newly announced university fee waivers, and bilateral government quotas.
   - Cross-references with a pre-indexed curated repository of 16+ flagship global master's scholarships.
3. **Eligibility & Risk Auditor Agent**:
   - Calculates weighted 5-dimension match scores (0–100%) across Academic GPA, Work Experience, Field Fit, Language Proficiency, and Nationality.
   - Detects disqualification traps (such as strict 2-year post-graduation work requirements for Chevening or DAAD EPOS).
4. **Roadmap & Strategy Agent**:
   - Generates customized 4-phase milestone timelines (4–6 months out, 2–3 months out, final submission).
   - Engineers personalized **Statement of Purpose (SOP) blueprints** (compelling opening hook, academic bridge, program fit, and socio-economic impact return).
   - Generates document matrices and Letter of Recommendation (LOR) briefing packets.
5. **Interactive 1-on-1 Admissions Advisor Chat**:
   - Conversational AI loaded with the candidate's exact profile background and target scholarship requirements.
   - Critiques essay hooks, explains lower GPAs, coaches interview questions, and provides tailored advice.

---

## 🏛️ Flagship Scholarships Supported

| Scholarship | Host Country / Region | Coverage | Typical Deadline |
| :--- | :--- | :--- | :--- |
| **Erasmus Mundus (EMJM)** | Multi-country Europe (EU) | 100% Tuition + €1,400/mo stipend + travel | Dec – Feb |
| **Chevening Scholarships** | United Kingdom | 100% Tuition + living stipend + flights | Early Nov |
| **DAAD EPOS & Helmut-Schmidt** | Germany | Tuition-free + €934/mo + health + travel | Aug – Nov / Jul 31 |
| **Fulbright Foreign Student** | United States | Full tuition + stipend + J-1 visa + health | Feb – Oct (by country) |
| **Swedish Institute (SISGP)** | Sweden | Full tuition + SEK 12,000/mo + travel | Mid-Feb |
| **Eiffel Excellence** | France | €1,181/mo allowance + flights + cultural | Early Jan |
| **Swiss Government Excellence** | Switzerland (ETH/EPFL) | CHF 1,920/mo + health insurance + flights | Sep – Dec |
| **MEXT Japanese Government** | Japan | 100% Tuition + 144,000 JPY/mo + flights | Apr – Jun / Nov – Feb |
| **Global Korea Scholarship (GKS)**| South Korea (KAIST/SNU) | Tuition + 1,000,000 KRW/mo + language year | Feb – Mar |
| **Australia Awards** | Australia | Full tuition + living expenses + return airfare| April 30 |
| **ETH Zurich ESOP** | Switzerland | Tuition waiver + CHF 12,000/semester grant | Dec 15 |
| **Gates Cambridge** | University of Cambridge (UK) | Full university fees + £21,000/yr allowance | Oct – Jan |
| **Türkiye Bursları** | Turkey | 100% Tuition + stipend + free dorm + flights | Jan 10 – Feb 20 |
| **Master Mind Scholarships** | Flanders, Belgium (KU Leuven) | €10,000 grant + tuition waiver | Feb – Apr |
| **Stipendium Hungaricum** | Hungary | 100% Tuition + stipend + free dorm | Jan 15 |

---

## 🚀 Quickstart Guide

### 1. Requirements
- Python 3.10+ (Tested on Python 3.14)
- Google Gemini API Key (Optional, get free key at [Google AI Studio](https://aistudio.google.com/))

### 2. Installation
Open PowerShell or your command prompt in this directory:
```bash
pip install -r requirements.txt
```

### 3. Running the Application
Launch the server and web dashboard:
```bash
python run.py
```
Or start via Uvicorn:
```bash
uvicorn app:app --host 127.0.0.1 --port 8000
```
Then navigate to **http://127.0.0.1:8000** in your browser.

---

## 🔑 Activating Google Gemini Live Grounding

The application is fully operational out-of-the-box with its built-in knowledge base. To activate **real-time Google Search grounding**:
1. Click the **"Gemini Key: Configure Key"** button in the top navigation bar of the web interface.
2. Paste your Google AI Studio API key and click **Save & Test Key**.
3. The indicator will turn green (`Gemini Grounding: Active`), unlocking real-time search for upcoming application deadlines and live conversational advising.

Alternatively, set your key in the `.env` file:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## 🛠️ API Endpoints

### 🔐 User Accounts & Cloud Sync
- `POST /api/auth/register` — Create a new student account (Email, Password, Full Name, Nationality).
- `POST /api/auth/login` — Sign in and obtain a session token.
- `POST /api/auth/logout` — Invalidate user session token.
- `GET /api/auth/me` — Verify current user session details.
- `POST /api/user/profile` — Save/update student profile to database.
- `GET /api/user/profile` — Retrieve stored profile.
- `POST /api/user/bookmarks/toggle` — Bookmark/save a scholarship to account.
- `GET /api/user/bookmarks` — List bookmarked scholarship IDs.

### 🤖 Multi-Agent Workflow
- `GET /api/health` — System status and indexed scholarships count.
- `GET /api/scholarships` — Full list of curated master's scholarships.
- `POST /api/profile/analyze` — Run GPA normalization and candidate categorization.
- `POST /api/agent/discover` — Orchestrates discovery with live web grounding and eligibility checks.
- `POST /api/agent/evaluate` — Deep audit checking 5 criteria, strengths, and risk factors.
- `POST /api/agent/roadmap` — Generates 4-phase timeline, SOP blueprint, and document matrix.
- `POST /api/agent/chat` — Contextual chat with admissions advisor.
- `POST /api/api-key/set` — Dynamically activate and verify Gemini API key.
