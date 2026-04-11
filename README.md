<div align="center">

# 🌟 Lumina
### Emotion-Aware AI Mental Health Chatbot

*An intelligent mental health companion that understands how you feel — and responds with empathy.*

[![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-DistilBERT-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/GabbarM32/emotion-chatbot-model)
[![Groq](https://img.shields.io/badge/Groq-LLaMA_3.1-F54E00?style=for-the-badge)](https://groq.com)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)
[![Accuracy](https://img.shields.io/badge/Emotion_Accuracy-92.4%25-6366F1?style=for-the-badge)](#model)

**[🚀 Try Live Demo](https://emotion-chatbot-84ucakfxfq5qn9fwhrgqvo.streamlit.app)** &nbsp;|&nbsp; **[🤗 HuggingFace Model](https://huggingface.co/GabbarM32/emotion-chatbot-model)**

![Lumina Banner](https://img.shields.io/badge/Mental_Health-AI_Companion-gradient?style=for-the-badge)

</div>

---

## 🧠 What is Lumina?

Lumina is an AI-powered mental health chatbot that detects your emotional state in real-time using a fine-tuned DistilBERT model, then generates empathetic, context-aware responses using Groq's LLaMA 3.1. It's not just a chatbot — it's a companion that truly *understands* you.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🎭 **8-Emotion Detection** | Detects joy, sadness, anger, fear, love, surprise, disgust, neutral |
| 💬 **Empathetic AI Responses** | Powered by Groq LLaMA 3.1-8B with Gemini 2.0 Flash as fallback |
| 🔄 **Negation Handling** | "not happy" correctly maps to sadness, not joy |
| 🚨 **Crisis Detection** | Auto-detects distress keywords and shows emergency helplines |
| 📊 **Emotion Timeline Graph** | Visual chart of your emotional journey through the session |
| 📄 **PDF Report Export** | Download your full session as a mental health report |
| 👍 **Feedback System** | Thumbs up/down on every response for quality tracking |
| ⚡ **Streaming Replies** | Live token-by-token streaming for a natural chat feel |
| 🛡️ **Dual AI Fallback** | Groq (14,400 req/day free) → Gemini if rate-limited |

---

## 🏗️ Architecture

```
User Input
    │
    ▼
┌─────────────────────────────────────────┐
│  DistilBERT Fine-tuned Emotion Model    │
│  GabbarM32/emotion-chatbot-model        │
│  92.4% accuracy · 8 emotions · 61K rows │
└────────────────┬────────────────────────┘
                 │ emotion label + confidence score
                 ▼
┌────────────────────────┐     rate limit
│  Groq API              │ ──────────────► Gemini 2.0 Flash
│  llama-3.1-8b-instant  │                 (fallback)
└────────────┬───────────┘
             │ empathetic response (streaming)
             ▼
┌─────────────────────────────────────────┐
│  Streamlit UI                           │
│  Session State → Emotion Graph → PDF    │
└─────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Groq API key → [console.groq.com](https://console.groq.com) (free)
- Gemini API key → [aistudio.google.com](https://aistudio.google.com) (free)

### 1. Clone the repository
```bash
git clone https://github.com/codewithpandeymayank-star/Lumina.git
cd Lumina
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Add your API keys
```bash
mkdir -p .streamlit
```

Create `.streamlit/secrets.toml` *(never commit this file!)*:
```toml
GROQ_API_KEY = "gsk_your_key_here"
GEMINI_API_KEY = "your_gemini_key_here"
```

### 4. Run the app
```bash
streamlit run app/Home.py
```

Open your browser at **http://localhost:8501** 🎉

---

## 🤖 Model Details <a name="model"></a>

| Property | Value |
|---|---|
| **Base Model** | `distilbert-base-uncased` |
| **Training Dataset** | Emotions dataset (61,410 sentences) |
| **Accuracy** | 92.4% on held-out test set |
| **Emotions** | joy, sadness, anger, fear, love, surprise, disgust, neutral |
| **HuggingFace** | [GabbarM32/emotion-chatbot-model](https://huggingface.co/GabbarM32/emotion-chatbot-model) |

---

## 📁 Project Structure

```
Lumina/
├── app/
│   ├── Home.py          # Landing page
│   ├── chatbot.py       # Core AI logic (emotion detection + LLM)
│   └── pages/
│       └── Chat.py      # Chat interface
├── model/               # Local model files (gitignored binaries)
├── .streamlit/
│   └── secrets.toml     # API keys (NOT committed — in .gitignore)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🆘 Crisis Resources

Lumina automatically detects crisis language and immediately surfaces emergency contacts:

| Resource | Contact |
|---|---|
| **iCall (India)** | 9152987821 |
| **Vandrevala Foundation** | 1860-2662-345 |
| **AASRA** | 9820466627 |
| **International Directory** | [findahelpline.com](https://findahelpline.com) |

> ⚠️ *Lumina is an AI companion and does not replace professional mental health care.*

---

## 🛠️ Tech Stack

- **Emotion Detection** — DistilBERT (fine-tuned, HuggingFace Transformers)
- **LLM Responses** — Groq API (LLaMA 3.1-8B-Instant)
- **Fallback LLM** — Google Gemini 2.0 Flash
- **Frontend** — Streamlit
- **PDF Generation** — ReportLab
- **Data Visualization** — Plotly

---

## 🤝 Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

---

## 📜 License

MIT License © 2024 [Mayank Pandey](https://github.com/codewithpandeymayank-star)

---

<div align="center">
  <i>Built with ❤️ to make mental health support more accessible</i>
</div>
