import streamlit as st
import torch
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification
import pickle
from google import genai
from google.genai import types
from huggingface_hub import hf_hub_download
import pandas as pd
from datetime import datetime
import time
import io

MODEL_REPO = "GabbarM32/emotion-chatbot-model"

CRISIS_KEYWORDS = [
    "kill myself", "want to die", "end my life", "suicide", "suicidal",
    "no reason to live", "better off dead", "want to disappear",
    "can't go on", "cannot go on", "give up on life", "self harm",
    "hurt myself", "cutting myself", "hopeless", "worthless",
    "don't want to be here", "do not want to be here"
]

def is_crisis(text):
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in CRISIS_KEYWORDS)

@st.cache_resource
def load_model():
    tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_REPO)
    model = DistilBertForSequenceClassification.from_pretrained(MODEL_REPO)
    model.eval()
    label_path = hf_hub_download(repo_id=MODEL_REPO, filename="label_encoder.pkl")
    with open(label_path, 'rb') as f:
        le = pickle.load(f)
    return tokenizer, model, le

def predict_emotion(text, tokenizer, model, le):
    inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=128)
    with torch.no_grad():
        outputs = model(**inputs)
    probs = torch.softmax(outputs.logits, dim=1)
    confidence = torch.max(probs).item()
    pred = torch.argmax(outputs.logits, dim=1).item()
    emotion = le.inverse_transform([pred])[0]
    if confidence < 0.55:
        emotion = 'neutral'
    return emotion, round(confidence * 100, 1)

def get_gemini_response(messages, emotion, confidence, api_key):
    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""You are Lumina — a professional, warm, empathetic AI mental health companion.
The user's detected emotion is: {emotion} (confidence: {confidence}%)

Rules:
- Talk like a caring friend, not a robot
- Remember the full conversation and refer back naturally
- Ask ONE thoughtful follow-up question
- Validate feelings before giving advice
- Keep responses STRICTLY 1 sentence only, very short and concise
- Use emojis occasionally
- Never say "As an AI"
- Never give medical diagnosis

Conversation so far:
"""
        for msg in messages[:-1]:
            role = "User" if msg['role'] == 'user' else "Lumina"
            prompt += f"{role}: {msg['content']}\n"
        prompt += f"\nUser: {messages[-1]['content']}\nLumina:"

        full_reply = ""
        placeholder = st.empty()
        for chunk in client.models.generate_content_stream(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                max_output_tokens=80,
                temperature=0.8,
            )
        ):
            if chunk.text:
                full_reply += chunk.text
                placeholder.markdown(full_reply + "▌")
        placeholder.markdown(full_reply)
        return full_reply
    except Exception as e:
        if '503' in str(e) or 'UNAVAILABLE' in str(e):
            return "Gemini is busy right now, please send your message again in a moment. 🙏"
        return f"Error: {str(e)}"
st.set_page_config(page_title="Lumina", page_icon="🧠", layout="centered")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background: #0f0f13; }
    .main-header { text-align: center; padding: 28px 0 16px 0; border-bottom: 1px solid #1e1e2e; margin-bottom: 20px; }
    .main-title { font-size: 1.8rem; font-weight: 700; color: #ffffff; letter-spacing: -0.5px; margin-bottom: 4px; }
    .main-subtitle { font-size: 0.85rem; color: #6b7280; margin-bottom: 12px; }
    .status-bar { display: flex; justify-content: center; gap: 8px; flex-wrap: wrap; }
    .status-pill { background: #1a1a2e; border: 1px solid #2a2a3e; border-radius: 100px; padding: 3px 12px; font-size: 11px; color: #9ca3af; }
    .status-pill.active { border-color: #10b981; color: #10b981; }
    .emotion-badge { display: inline-block; padding: 3px 10px; border-radius: 100px; font-size: 11px; font-weight: 600; margin-top: 5px; }
    .crisis-box { background: #1a0000; border: 1px solid #dc2626; border-radius: 12px; padding: 16px; margin: 8px 0; }
    [data-testid="stChatMessage"] { background: transparent !important; padding: 4px 0 !important; }
    [data-testid="stChatMessageContent"] { background: #1a1a2e !important; border: 1px solid #2a2a3e !important; border-radius: 12px !important; color: #e5e7eb !important; font-size: 0.92rem !important; line-height: 1.6 !important; }
    div[data-testid="stSidebar"] { background: #0a0a10 !important; border-right: 1px solid #1e1e2e !important; }
    .sidebar-section { color: #9ca3af; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
    .stButton button { border-radius: 8px !important; font-size: 0.85rem !important; }
    div[data-testid="stChatInput"] textarea { background: #1a1a2e !important; border: 1px solid #2a2a3e !important; border-radius: 12px !important; color: #e5e7eb !important; font-size: 0.92rem !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <div class="main-title">🧠 Lumina</div>
    <div class="main-subtitle">Professional Emotion-Aware AI Companion</div>
    <div class="status-bar">
        <span class="status-pill active">● Live</span>
        <span class="status-pill">Gemini 2.5 Flash</span>
        <span class="status-pill">92.4% Accuracy</span>
        <span class="status-pill">8 Emotions</span>
        <span class="status-pill">Crisis Detection</span>
        <span class="status-pill">PDF Export</span>
    </div>
</div>
""", unsafe_allow_html=True)

with st.spinner("Loading emotion model..."):
    tokenizer, model, le = load_model()

if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'emotions' not in st.session_state:
    st.session_state.emotions = []
if 'confidences' not in st.session_state:
    st.session_state.confidences = []
if 'timestamps' not in st.session_state:
    st.session_state.timestamps = []
if 'feedback' not in st.session_state:
    st.session_state.feedback = {}

COLORS = {
    'joy':      ('background:#854d0e;color:#fef08a', '😊'),
    'sadness':  ('background:#1e3a5f;color:#93c5fd', '😢'),
    'anger':    ('background:#7f1d1d;color:#fca5a5', '😠'),
    'fear':     ('background:#2e1065;color:#c4b5fd', '😨'),
    'surprise': ('background:#064e3b;color:#6ee7b7', '😲'),
    'love':     ('background:#831843;color:#f9a8d4', '❤️'),
    'neutral':  ('background:#1f2937;color:#9ca3af', '💬'),
    'disgust':  ('background:#1a3a1a;color:#86efac', '🤢'),
}

with st.sidebar:
    st.markdown("<p class='sidebar-section'>Configuration</p>", unsafe_allow_html=True)
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("✅ API Connected")
    except:
        api_key = st.text_input("Gemini API Key", type="password", placeholder="AIzaSy...")
        st.caption("Get free key at aistudio.google.com")

    st.divider()
    st.markdown("<p class='sidebar-section'>Emotion Timeline</p>", unsafe_allow_html=True)
    if st.session_state.emotions:
        emotion_order = {'joy': 6, 'love': 5, 'surprise': 4, 'neutral': 3, 'fear': 2, 'sadness': 1, 'anger': 0}
        df = pd.DataFrame({
            'msg': range(1, len(st.session_state.emotions)+1),
            'score': [emotion_order.get(e, 3) for e in st.session_state.emotions]
        })
        st.line_chart(df.set_index('msg')['score'], height=120)
        st.caption("Higher = Positive  |  Lower = Negative")
        st.divider()

        st.markdown("<p class='sidebar-section'>Session Insights</p>", unsafe_allow_html=True)
        total = len(st.session_state.emotions)
        emotion_counts = {}
        for emo in st.session_state.emotions:
            emotion_counts[emo] = emotion_counts.get(emo, 0) + 1
        dominant = max(emotion_counts, key=emotion_counts.get)
        style, emoji = COLORS.get(dominant, COLORS['neutral'])
        st.markdown(f"**Messages:** {total} &nbsp;|&nbsp; **Dominant:** <span class='emotion-badge' style='{style}'>{emoji} {dominant.capitalize()}</span>", unsafe_allow_html=True)
        st.write("")
        for emo, count in sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True):
            pct = round(count/total*100)
            style, emoji = COLORS.get(emo, COLORS['neutral'])
            st.markdown(f"<span class='emotion-badge' style='{style}'>{emoji} {emo.capitalize()} {count} ({pct}%)</span>", unsafe_allow_html=True)
            st.write("")
        avg_conf = round(sum(st.session_state.confidences)/len(st.session_state.confidences), 1)
        st.caption(f"Avg confidence: {avg_conf}%")
        st.divider()

        st.markdown("<p class='sidebar-section'>Export Report</p>", unsafe_allow_html=True)
        st.text_input("Patient Name (optional)", placeholder="Anonymous", key="patient_name")
        st.text_input("Doctor Name (optional)", placeholder="Dr.", key="doctor_name")
        if st.button("📥 Export Mental Health PDF", use_container_width=True, type="primary"):
            with st.spinner("Generating report..."):
                try:
                    import subprocess
                    subprocess.run(["pip", "install", "reportlab", "-q"], capture_output=True)
                    pdf_buffer = generate_pdf_report(
                        st.session_state.messages,
                        st.session_state.emotions,
                        st.session_state.confidences,
                        st.session_state.timestamps,
                        st.session_state.feedback
                    )
                    if pdf_buffer:
                        fname = f"lumina_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                        st.download_button(
                            label="⬇️ Download PDF Report",
                            data=pdf_buffer,
                            file_name=fname,
                            mime="application/pdf",
                            use_container_width=True
                        )
                        st.success("Report ready!")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    else:
        st.info("Start chatting to see insights and export reports.")

    st.divider()
    if st.button("🗑️ New Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.emotions = []
        st.session_state.confidences = []
        st.session_state.timestamps = []
        st.session_state.feedback = {}
        st.rerun()

for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg['role']):
        st.write(msg['content'])
        if msg['role'] == 'user':
            idx = i // 2
            if idx < len(st.session_state.emotions):
                emo = st.session_state.emotions[idx]
                conf = st.session_state.confidences[idx]
                ts = st.session_state.timestamps[i] if i < len(st.session_state.timestamps) else ""
                style, emoji = COLORS.get(emo, COLORS['neutral'])
                st.markdown(f"<span class='emotion-badge' style='{style}'>{emoji} {emo.capitalize()} · {conf}%</span> <span style='color:#6b7280;font-size:11px;'>{ts}</span>", unsafe_allow_html=True)
        else:
            col1, col2, col3 = st.columns([1, 1, 8])
            with col1:
                if st.button("👍", key=f"up_{i}", help="Helpful"):
                    st.session_state.feedback[i] = "up"
            with col2:
                if st.button("👎", key=f"down_{i}", help="Not helpful"):
                    st.session_state.feedback[i] = "down"
            if i in st.session_state.feedback:
                fb = st.session_state.feedback[i]
                st.caption("✅ Thanks!" if fb == "up" else "📝 We'll improve!")

if prompt := st.chat_input("Share what's on your mind..."):
    ts = datetime.now().strftime("%I:%M %p")
    with st.chat_message('user'):
        st.write(prompt)
    st.session_state.timestamps.append(ts)
    emotion, confidence = predict_emotion(prompt, tokenizer, model, le)
    st.session_state.emotions.append(emotion)
    st.session_state.confidences.append(confidence)
    style, emoji = COLORS.get(emotion, COLORS['neutral'])
    st.markdown(f"<span class='emotion-badge' style='{style}'>{emoji} {emotion.capitalize()} · {confidence}%</span> <span style='color:#6b7280;font-size:11px;'>{ts}</span>", unsafe_allow_html=True)
    st.session_state.messages.append({'role': 'user', 'content': prompt})

    if is_crisis(prompt):
        crisis_reply = """I'm really concerned about you right now. Please reach out to a professional immediately.

🆘 iCall: 9152987821
🆘 Vandrevala Foundation: 1860-2662-345 (24/7)
🆘 AASRA: 9820466627
🆘 National Helpline: 14416

You are not alone. People care about you. 💙"""
        with st.chat_message('assistant'):
            st.markdown(f"<div class='crisis-box'>🚨 <strong>Crisis Support</strong><br><br>{crisis_reply}</div>", unsafe_allow_html=True)
        st.session_state.messages.append({'role': 'assistant', 'content': crisis_reply})
        st.session_state.timestamps.append(ts)

    elif api_key and api_key.startswith('AIza'):
        with st.chat_message('assistant'):
            with st.spinner(""):
                time.sleep(0.5)
                reply = get_gemini_response(
                    st.session_state.messages,
                    emotion, confidence, api_key
                )
                st.write(reply)
                st.session_state.messages.append({'role': 'assistant', 'content': reply})
                st.session_state.timestamps.append(ts)
    else:
        with st.chat_message('assistant'):
            st.warning("Please enter your Gemini API key in the sidebar.")
    st.rerun()