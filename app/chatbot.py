import streamlit as st
import torch
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification
import pickle
import random
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
    inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=64)
    with torch.no_grad():
        outputs = model(**inputs)
    probs = torch.softmax(outputs.logits, dim=1)
    confidence = torch.max(probs).item()
    pred = torch.argmax(outputs.logits, dim=1).item()
    emotion = le.inverse_transform([pred])[0]
    if confidence < 0.45:
        emotion = 'neutral'
    return emotion, round(confidence * 100, 1)

def get_smart_response(text, emotion):
    text_lower = text.lower()
    greetings = ['hi','hello','hey','what\'s up','howdy','good morning','good evening','good afternoon']
    if any(g in text_lower for g in greetings):
        return random.choice([
            "Hey there! 👋 How are you feeling today?",
            "Hello! I'm here to chat and listen. How's your day going?",
            "Hi! Great to see you. What's on your mind?",
        ]), '👋', '#B5D4F4'
    questions = ['how are you','what are you','who are you','what can you do','are you a bot','are you real']
    if any(q in text_lower for q in questions):
        return random.choice([
            "I'm an emotion-aware chatbot! 🤖 I can understand how you feel and respond with empathy. Tell me what's on your mind!",
            "I'm here to listen and understand your emotions. Share anything — I won't judge! 😊",
            "I'm your empathetic AI companion! I detect emotions in what you say and try to respond in the most helpful way.",
        ]), '🤖', '#C0DD97'
    RESPONSES = {
        'joy':      {'emoji':'😊','color':'#FAC775','replies':["That's absolutely wonderful! 😊 What's making your day so great?","Yay! Your joy is contagious! 🌟 Tell me more!","That's so amazing! 🎉 What's the best part of your day?"]},
        'sadness':  {'emoji':'😢','color':'#85B7EB','replies':["I'm really sorry you're feeling this way. 💙 I'm right here — want to talk?","You're not alone in this. 🤗 Sometimes just talking helps. What's going on?","I hear you, and I care. 💙 Take your time — I'm listening."]},
        'anger':    {'emoji':'😠','color':'#F0997B','replies':["I can hear you're frustrated. 😤 Take a deep breath — want to tell me what happened?","Your anger is valid. 💢 I'm here to listen without judgment.","It sounds like something really got to you. 😠 Let it out — I'm here."]},
        'fear':     {'emoji':'😨','color':'#AFA9EC','replies':["It's okay to feel scared. 💜 Take a slow breath. I'm right here with you.","You don't have to face this alone. 🤝 Want to talk it through?","Fear can feel overwhelming. 😨 But you've gotten through hard things before."]},
        'surprise': {'emoji':'😲','color':'#9FE1CB','replies':["Whoa, something unexpected happened! 😲 Good or bad surprise? Tell me!","Oh wow! Life is full of surprises! 🤩 What happened?","That must have caught you off guard! Are you okay?"]},
        'love':     {'emoji':'❤️','color':'#F4C0D1','replies':["Aww, that's so beautiful! ❤️ Tell me more!","That's so heartwarming! 🥰 Who or what are you feeling this way about?","Your heart is so full right now! ❤️ That's a wonderful feeling!"]},
        'neutral':  {'emoji':'💬','color':'#D3D1C7','replies':["Thanks for sharing! 😊 Tell me more — I'm all ears.","Interesting! I'd love to hear more about what's on your mind.","I'm here and listening! Feel free to share whatever's on your mind. 🙂"]},
    }
    info = RESPONSES.get(emotion, RESPONSES['neutral'])
    return random.choice(info['replies']), info['emoji'], info['color']

st.set_page_config(page_title="Emotion-Aware Chatbot", page_icon="🤖", layout="centered")
st.title("🤖 Emotion-Aware Chatbot")
st.caption("Powered by DistilBERT • 91.8% accuracy • Understands 6 emotions")

with st.spinner("Loading AI model... please wait ⏳"):
    tokenizer, model, le = load_model()

if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'emotions' not in st.session_state:
    st.session_state.emotions = []
if 'confidences' not in st.session_state:
    st.session_state.confidences = []

COLORS = {'joy':'#FAC775','sadness':'#85B7EB','anger':'#F0997B','fear':'#AFA9EC','surprise':'#9FE1CB','love':'#F4C0D1','neutral':'#D3D1C7'}
EMOJIS = {'joy':'😊','sadness':'😢','anger':'😠','fear':'😨','surprise':'😲','love':'❤️','neutral':'💬'}

for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg['role']):
        st.write(msg['content'])
        if msg['role'] == 'user':
            idx = i // 2
            if idx < len(st.session_state.emotions):
                emo = st.session_state.emotions[idx]
                conf = st.session_state.confidences[idx]
                st.markdown(f"<span style='background:{COLORS.get(emo,'#D3D1C7')};padding:3px 12px;border-radius:20px;font-size:12px;font-weight:500'>{EMOJIS.get(emo,'💬')} {emo.capitalize()} detected • {conf}% confidence</span>", unsafe_allow_html=True)

if prompt := st.chat_input("Type anything — how you feel, what happened, or just say hi!"):
    with st.chat_message('user'):
        st.write(prompt)
    emotion, confidence = predict_emotion(prompt, tokenizer, model, le)
    st.session_state.emotions.append(emotion)
    st.session_state.confidences.append(confidence)
    st.markdown(f"<span style='background:{COLORS.get(emotion,'#D3D1C7')};padding:3px 12px;border-radius:20px;font-size:12px;font-weight:500'>{EMOJIS.get(emotion,'💬')} {emotion.capitalize()} detected • {confidence}% confidence</span>", unsafe_allow_html=True)
    reply, _, _ = get_smart_response(prompt, emotion)
    with st.chat_message('assistant'):
        st.write(reply)
    st.session_state.messages.append({'role':'user','content':prompt})
    st.session_state.messages.append({'role':'assistant','content':reply})
    st.rerun()

with st.sidebar:
    st.header("📊 Emotion History")
    if st.session_state.emotions:
        emotion_counts = {}
        for emo in st.session_state.emotions:
            emotion_counts[emo] = emotion_counts.get(emo, 0) + 1
        st.subheader("Summary")
        for emo, count in emotion_counts.items():
            st.write(f"{EMOJIS.get(emo,'💬')} {emo.capitalize()}: {count} message(s)")
        st.divider()
        st.subheader("Message Log")
        for i, (emo, conf) in enumerate(zip(st.session_state.emotions, st.session_state.confidences)):
            st.write(f"**#{i+1}** {EMOJIS.get(emo,'💬')} {emo.capitalize()} ({conf}%)")
    else:
        st.info("Start chatting to see your emotion history here!")
    st.divider()
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.emotions = []
        st.session_state.confidences = []
        st.rerun()
