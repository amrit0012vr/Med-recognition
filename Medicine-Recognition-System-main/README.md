# 🩺 MediScan AI — Medical Image & Medicine Recognition System

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.x-green.svg)](https://flask.palletsprojects.com/)
[![AI Engine](https://img.shields.io/badge/AI%20Model-Google%20Gemini%202.0%20%2F%202.5%20Flash-orange.svg)](https://aistudio.google.com/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

An intelligent, full-stack multimodal web application that utilizes Google's Gemini Vision models to analyze medical documents and diagnostic imagery—such as **handwritten doctor prescriptions, clinic slips, X-rays, MRIs, CT scans, dermatology photographs, and pharmaceutical packaging**.

---

## 🚀 Key Features

- **Multimodal Clinical Analysis:** Transcribes difficult handwritten doctor prescriptions, identifies medications and dosages, and generates structured observations for diagnostic scans.
- **Dynamic Model Discovery & Automatic Fallback:** Employs runtime ModelService inspection via `genai.list_models()` and automatically negotiates across active models (`gemini-2.5-flash`, `gemini-2.0-flash`, `gemini-1.5-flash-latest`, `gemini-1.5-pro`) to eliminate 404 deprecation errors.
- **Dual-Stage Medical Guardrail:** Filters out non-medical imagery (e.g. landscapes, memes, objects) using a two-stage verification pipeline before rendering findings.
- **Zero-Disk In-Memory Processing:** Processes file streams entirely in memory using `io.BytesIO` and Base64 Data URIs, eliminating disk I/O bottlenecks and upholding data privacy standards.
- **Modern Responsive Dashboard:** Features drag-and-drop file upload, live client-side image preview, CSS loading spinner, formatted Markdown-to-HTML report presentation, and a one-click **Copy Report** button.
- **Automated API Key Persistence:** Allows users to input their Google Gemini API key directly via the web UI, persisting it to `.env` for future requests.

---

## 🛠️ Tech Stack

| Technology | Category | Purpose |
| :--- | :--- | :--- |
| **Python 3.13** | Core Language | Backend business logic, byte stream manipulation, and API coordination. |
| **Flask 3.x** | Web Framework | Lightweight WSGI microservice routing, request handling, and template dispatching. |
| **Google Gemini API** | Multimodal LLM | Core generative vision intelligence (`google-generativeai` & `google-genai`). |
| **Pillow (PIL)** | Image Processing | Validates binary image integrity and handles formats in memory. |
| **io.BytesIO & Base64** | Data Serialization | In-memory stream buffering and Data URI generation without disk persistence. |
| **Python-Markdown** | Content Processing | Converts AI Markdown responses into semantic, readable HTML. |
| **python-dotenv** | Environment Security | 12-Factor App credential decoupling (`.env`). |
| **HTML5 & CSS3** | Frontend Presentation | Responsive medical UI tokens, CSS Grid, Flexbox, and keyframe animations. |
| **Vanilla JavaScript** | Client-Side UX | Drag-and-drop events, file detection, and modern Clipboard API. |

---

## 📋 System Architecture

```text
[User Uploads Image]
         │
         ▼
[Flask Request Ingestion] ───► Max 16MB Limit Check
         │
         ▼
[In-Memory Stream (io.BytesIO)] ───► Verified by Pillow (PIL)
         │
         ├───► Base64 Encoded (Instant Client Preview)
         ▼
[Google Gemini Multimodal API]
  ├── Dynamic ModelService Discovery (genai.list_models())
  └── Auto-Fallback (Gemini 2.5 Flash -> 2.0 Flash -> 1.5 Pro)
         │
         ▼
[Dual-Stage Verification Guardrail]
  ├── Stage 1: Multimodal Extraction & Clinical Findings
  └── Stage 2: Domain Relevance Verification
         │
         ▼
[Python-Markdown Parser] ───► Semantic HTML Formatting
         │
         ▼
[Rendered Medical Observations Dashboard]
```

---

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/amrit0012vr/Med-recognition.git
cd Med-recognition
```

### 2. Create and Activate a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Your API Key
1. Get a free API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Create a `.env` file in the project root:
   ```env
   GOOGLE_API_KEY=your_actual_gemini_api_key_here
   GEMINI_MODEL=gemini-2.0-flash
   PORT=5000
   ```
*(Alternatively, you can start the application and enter your API key directly on the web page; it will automatically be saved to `.env`.)*

### 5. Launch the Application
```bash
# Direct Python launch
python app.py

# Or on Windows using the included launcher:
.\run.bat
```

Open your browser and navigate to:
👉 **`http://127.0.0.1:5000`**

---

## 📂 Project Structure

```text
Med-recognition/
├── .env.example              # Environment variable template
├── .gitignore                # Ignored files (venv, .env, __pycache__)
├── app.py                    # Main Flask server & Gemini pipeline
├── requirements.txt          # Python project dependencies
├── run.bat                   # Windows one-click startup script
├── static/
│   └── style.css             # Custom responsive medical theme
└── templates/
    └── index.html            # Jinja2 dashboard template
```

---

## ⚠️ Medical Disclaimer

*This application is built for research, educational, and informational purposes only. It is not a certified medical device and should never replace professional medical judgment, diagnosis, or treatment. Always consult a licensed healthcare practitioner for medical concerns.*

---

## 📄 License

This project is open-source and licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author & Maintainer

- **GitHub:** [@amrit0012vr](https://github.com/amrit0012vr)
- **Repository:** [https://github.com/amrit0012vr/Med-recognition](https://github.com/amrit0012vr/Med-recognition)
