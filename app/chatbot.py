import streamlit as st
import torch
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification
import pickle
from google import genai
from google.genai import types
from huggingface_hub import hf_hub_download

MODEL_REPO = "GabbarM32/emotion-chatbot-model"

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
    if confidence < 0.40:
        emotion = 'neutral'
    return emotion, round(confidence * 100, 1)

def get_gemini_response(messages, emotion, confidence, api_key):
    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""You are EmotiBot — a warm, empathetic AI companion.
The user's detected emotion is: {emotion} (confidence: {confidence}%)

Rules:
- Talk like a caring friend, not a robot
- Remember the full conversation and refer back naturally
- Ask thoughtful follow-up questions
- Validate feelings before giving advice
- Keep responses 2-4 sentences
- Use emojis occasionally
- Never say "As an AI"

Conversation so far:
"""
        for msg in messages[:-1]:
            role = "User" if msg['role'] == 'user' else "EmotiBot"
            prompt += f"{role}: {msg['content']}\n"

        prompt += f"\nUser: {messages[-1]['content']}\nEmotiBot:"

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                max_output_tokens=150,
                temperature=0.8,
            )
        )
        if response.text and response.text.strip():
            return response.text
        return "I'm here for you. Could you tell me a bit more? 💙"
    except Exception as e:
        return f"Error: {str(e)}"

st.set_page_config(page_title="EmotiBot", page_icon="💬", layout="centered")

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0a1628 0%, #0d2144 50%, #0a1628 100%); }
    .main-title { font-size: 2.5rem; font-weight: 700; color: #4da6ff; letter-spacing: 1px; text-align: center; padding-top: 20px; }
    .main-subtitle { font-size: 0.95rem; color: #7ab3e0; text-align: center; margin-bottom: 10px; }
    .status-bar { display: flex; justify-content: center; gap: 12px; margin: 10px 0 20px 0; flex-wrap: wrap; }
    .status-item { background: rgba(77,166,255,0.1); border: 1px solid rgba(77,166,255,0.3); border-radius: 20px; padding: 4px 14px; font-size: 12px; color: #4da6ff; }
    .emotion-badge { display: inline-block; padding: 4px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; margin-top: 6px; }
    [data-testid="stChatMessageContent"] { background: rgba(13,33,68,0.8) !important; border: 1px solid rgba(77,166,255,0.2) !important; border-radius: 16px !important; color: #e8f0fe !important; }
    div[data-testid="stSidebar"] { background: rgba(10,22,40,0.95) !important; border-right: 1px solid rgba(77,166,255,0.2) !important; }
    .sidebar-title { color: #4da6ff; font-size: 1.1rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">💬 Emotion-Aware Chatbot</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Your emotion-aware AI companion — powered by Google Gemini</div>', unsafe_allow_html=True)
st.markdown("""
<div class="status-bar">
    <span class="status-item">🟢 Online</span>
    <span class="status-item">🧠 Gemini AI</span>
    <span class="status-item">⚡ 91.8% Accuracy</span>
    <span class="status-item">💙 6 Emotions</span>
</div>
""", unsafe_allow_html=True)

with st.spinner("🔄 Loading emotion model..."):
    tokenizer, model, le = load_model()

if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'emotions' not in st.session_state:
    st.session_state.emotions = []
if 'confidences' not in st.session_state:
    st.session_state.confidences = []

COLORS = {
    'joy':      ('background:#FAC775;color:#633806', '😊'),
    'sadness':  ('background:#1a4a7a;color:#85B7EB', '😢'),
    'anger':    ('background:#7a2a1a;color:#F0997B', '😠'),
    'fear':     ('background:#2a1a7a;color:#AFA9EC', '😨'),
    'surprise': ('background:#1a7a5a;color:#9FE1CB', '😲'),
    'love':     ('background:#7a1a4a;color:#F4C0D1', '❤️'),
    'neutral':  ('background:#2a2a2a;color:#D3D1C7', '💬'),
}

with st.sidebar:
    st.markdown("<p class='sidebar-title'>⚙️ Settings</p>", unsafe_allow_html=True)
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("✅ API Connected")
    except:
        api_key = st.text_input("🔑 Gemini API Key", type="password", placeholder="AIzaSy...")
        st.caption("Get free key at aistudio.google.com")
    st.divider()
    st.markdown("<p class='sidebar-title'>📊 Insights</p>", unsafe_allow_html=True)
    if st.session_state.emotions:
        total = len(st.session_state.emotions)
        st.markdown(f"**Total messages:** {total}")
        emotion_counts = {}
        for emo in st.session_state.emotions:
            emotion_counts[emo] = emotion_counts.get(emo, 0) + 1
        dominant = max(emotion_counts, key=emotion_counts.get)
        style, emoji = COLORS.get(dominant, COLORS['neutral'])
        st.markdown(f"**Dominant:**")
        st.markdown(f"<span class='emotion-badge' style='{style}'>{emoji} {dominant.capitalize()}</span>", unsafe_allow_html=True)
        st.write("")
        st.divider()
        for emo, count in sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True):
            pct = round(count/total*100)
            style, emoji = COLORS.get(emo, COLORS['neutral'])
            st.markdown(f"<span class='emotion-badge' style='{style}'>{emoji} {emo.capitalize()}: {count} ({pct}%)</span>", unsafe_allow_html=True)
            st.write("")
        st.divider()
        avg_conf = round(sum(st.session_state.confidences)/len(st.session_state.confidences), 1)
        st.markdown(f"**Avg confidence:** {avg_conf}%")
    else:
        st.info("💬 Start chatting to see insights!")
    st.divider()
    if st.button("🗑️ New Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.emotions = []
        st.session_state.confidences = []
        st.rerun()

for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg['role']):
        st.write(msg['content'])
        if msg['role'] == 'user':
            idx = i // 2
            if idx < len(st.session_state.emotions):
                emo = st.session_state.emotions[idx]
                conf = st.session_state.confidences[idx]
                style, emoji = COLORS.get(emo, COLORS['neutral'])
                st.markdown(f"<span class='emotion-badge' style='{style}'>{emoji} {emo.capitalize()} • {conf}%</span>", unsafe_allow_html=True)

if prompt := st.chat_input("Talk to me — share anything on your mind..."):
    with st.chat_message('user'):
        st.write(prompt)
    emotion, confidence = predict_emotion(prompt, tokenizer, model, le)
    st.session_state.emotions.append(emotion)
    st.session_state.confidences.append(confidence)
    style, emoji = COLORS.get(emotion, COLORS['neutral'])
    st.markdown(f"<span class='emotion-badge' style='{style}'>{emoji} {emotion.capitalize()} • {confidence}%</span>", unsafe_allow_html=True)
    st.session_state.messages.append({'role': 'user', 'content': prompt})
    if api_key and api_key.startswith('AIza'):
        with st.chat_message('assistant'):
            with st.spinner("thinking... 💭"):
                reply = get_gemini_response(
                    st.session_state.messages,
                    emotion, confidence, api_key
                )
                st.write(reply)
                st.session_state.messages.append({'role': 'assistant', 'content': reply})
    else:
        with st.chat_message('assistant'):
            st.warning("⚠️ Please enter your Gemini API key in the sidebar!")
    st.rerun()
