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
    chunks = [text[i:i+64] for i in range(0, len(text.split()), 64)]
    all_logits = []
    for chunk in [text]:
        inputs = tokenizer(chunk, return_tensors='pt', truncation=True, padding=True, max_length=128)
        with torch.no_grad():
            outputs = model(**inputs)
        all_logits.append(outputs.logits)
    logits = torch.mean(torch.stack(all_logits), dim=0)
    probs = torch.softmax(logits, dim=1)
    confidence = torch.max(probs).item()
    pred = torch.argmax(logits, dim=1).item()
    emotion = le.inverse_transform([pred])[0]
    all_probs = {le.inverse_transform([i])[0]: round(probs[0][i].item() * 100, 1) 
                 for i in range(len(le.classes_))}
    if confidence < 0.40:
        emotion = 'neutral'
    return emotion, round(confidence * 100, 1), all_probs

def get_smart_response(text, emotion, all_probs):
    text_lower = text.lower()
    words = text_lower.split()

    greetings = ['hi','hello','hey','sup','howdy','good morning','good evening','good afternoon','what\'s up','wassup']
    if any(g in text_lower for g in greetings) and len(words) < 6:
        return random.choice([
            "Hey there! 👋 How are you feeling today? I'm here to listen.",
            "Hello! Great to have you here. What's on your mind today?",
            "Hi! I'm your emotion-aware companion. How's your day going?",
        ])

    bot_questions = ['who are you','what are you','what can you do','are you a bot','are you real','are you human','what is your name','your name']
    if any(q in text_lower for q in bot_questions):
        return random.choice([
            "I'm an emotion-aware AI chatbot! 🤖 I'm trained on thousands of real conversations to understand how you feel — whether you're happy, sad, angry, scared, or anything in between. Just talk to me naturally!",
            "I'm your empathetic AI companion, powered by DistilBERT with 91.8% emotion detection accuracy! I can understand complex emotions in your messages and respond with genuine empathy. What's on your mind?",
        ])

    negative_words = ['not good','not well','not okay','not fine','not great','dont feel','don\'t feel','feeling bad','feeling terrible','feeling awful','nothing is','everything is wrong','nothing works','cant do','can\'t do','no one','nobody','nothing']
    if any(n in text_lower for n in negative_words):
        return random.choice([
            "I can sense that things aren't going well for you right now. 💙 Sometimes life just feels heavy and overwhelming. You don't have to pretend everything is okay — I'm here to listen without any judgment. What's been going on?",
            "It sounds like you're going through a really tough time. 😔 Those feelings are completely valid. Sometimes just putting it into words can help. Would you like to talk about what's been bothering you?",
            "I hear you — and I want you to know that it's okay to not be okay. 💜 Whatever you're going through right now, you don't have to face it alone. Tell me more about what's happening.",
        ])

    overwhelm_words = ['too much','overwhelmed','stressed','pressure','burden','exhausted','tired of','fed up','cant take','can\'t take','falling apart','breaking down','losing it','going crazy','so hard','very hard','really hard']
    if any(o in text_lower for o in overwhelm_words):
        return random.choice([
            "It sounds like you're carrying a really heavy load right now. 😔 When everything piles up at once, it can feel completely overwhelming. Take a deep breath — you're stronger than you think. What's been weighing on you the most?",
            "I can feel the exhaustion in your words. 💙 It's okay to feel this way — you've been dealing with a lot. Sometimes we just need someone to acknowledge how hard things are. I'm here. What's going on?",
        ])

    complex_sad = ['nobody understands','no one cares','all alone','completely alone','feel empty','feel hollow','feel numb','lost everything','given up','no point','what\'s the point','don\'t see the point']
    if any(c in text_lower for c in complex_sad):
        return random.choice([
            "What you're feeling sounds really painful, and I want you to know — I hear you. 💙 Feeling alone and misunderstood is one of the hardest things a person can experience. You matter, and your feelings matter. Please know you're not as alone as you feel right now.",
            "I'm really glad you shared that with me. 💜 Feeling like no one understands can be incredibly isolating. But reaching out — even to a chatbot — shows courage. I'm here, and I'm listening to every word.",
        ])

    RESPONSES = {
        'joy': [
            "That's absolutely wonderful to hear! 😊 Happiness like yours is truly contagious. What's been going so well for you? I'd love to hear all about it!",
            "Yay! It sounds like things are really going your way right now! 🌟 Moments like these are so precious — what's been making you feel so good?",
            "That's so amazing! 🎉 You deserve all the happiness in the world. Tell me more about what's been making you smile!",
            "I love hearing this! 😄 Your positive energy is wonderful. What's the highlight of your day been so far?",
        ],
        'sadness': [
            "I'm really sorry you're going through this. 💙 It takes courage to open up about how you're feeling, and I want you to know that I'm here for you. You don't have to go through this alone — would you like to talk about what's been happening?",
            "That sounds really painful, and your feelings are completely valid. 😢 Sometimes life can feel so heavy and overwhelming. I'm here to listen without any judgment — take your time and share as much or as little as you'd like.",
            "I hear the sadness in your words, and I want you to know that it's okay to feel this way. 💜 Emotions like these remind us that we deeply care about things. What's been weighing on your heart lately?",
            "You don't have to carry this alone. 🤗 Whatever you're going through, sharing it can sometimes make the burden a little lighter. I'm right here — what's been on your mind?",
        ],
        'anger': [
            "I can completely understand why you're feeling this way — that sounds genuinely frustrating. 😤 It's okay to feel angry, especially when things feel unfair or out of control. Would you like to talk through what happened?",
            "Your anger makes total sense given what you've described. 💢 Sometimes the world can be genuinely infuriating. Take a deep breath — I'm here to listen, and I won't dismiss what you're feeling.",
            "That sounds really difficult to deal with. 😠 Anger often comes from feeling unheard or disrespected, and those feelings are completely valid. What's been going on that's gotten you so frustrated?",
        ],
        'fear': [
            "I can hear that you're feeling really anxious right now, and I want you to know that's completely understandable. 💜 Fear is a sign that something matters deeply to you. Take a slow, deep breath — you're not alone in this. What's been worrying you?",
            "Feeling scared or anxious can be so overwhelming, especially when we can't see a clear way forward. 😨 But you've faced difficult things before, and you have more strength than you realize. Would you like to talk through what's frightening you?",
            "It's okay to feel afraid — everyone does sometimes. 🤝 What matters is that you reached out instead of keeping it bottled up. I'm here with you. What's been making you feel this way?",
        ],
        'surprise': [
            "Wow, that sounds like quite a turn of events! 😲 Life really can catch us off guard sometimes. Was this a good surprise or a not-so-great one? Tell me everything!",
            "Oh! That must have really caught you off guard! 🤩 Unexpected things can be both exciting and unsettling at the same time. How are you feeling about it all?",
            "That's quite something! 😮 Sometimes life throws us the most unexpected curveballs. Are you doing okay with everything that's happened?",
        ],
        'love': [
            "That's absolutely beautiful to hear! ❤️ Love and deep connection are some of the most powerful feelings we can experience. Tell me more — who or what has your heart feeling so full?",
            "Aww, that's so heartwarming! 🥰 There's nothing quite like that warm feeling of love and connection. What's been filling your heart with such good feelings?",
            "That's really lovely! 💕 Caring deeply about someone or something makes life so much richer. I'd love to hear more about what's making you feel this way!",
        ],
        'neutral': [
            "Thanks for sharing that with me! 😊 I'm here and listening — feel free to tell me more about what's been on your mind lately.",
            "That's interesting! I'd love to understand more about what you mean. Could you tell me a bit more about how you're feeling or what's been going on?",
            "I'm here for you! 🙂 Sometimes it's hard to put feelings into words, and that's completely okay. Take your time — what would you like to talk about?",
        ],
    }

    replies = RESPONSES.get(emotion, RESPONSES['neutral'])
    return random.choice(replies)

st.set_page_config(page_title="Emotion-Aware Chatbot", page_icon="🤖", layout="centered")
st.title("🤖 Emotion-Aware Chatbot")
st.caption("Powered by DistilBERT • 91.8% accuracy • Understands complex emotions")

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

if prompt := st.chat_input("Share anything — how you feel, what happened today, or just say hi!"):
    with st.chat_message('user'):
        st.write(prompt)
    emotion, confidence, all_probs = predict_emotion(prompt, tokenizer, model, le)
    st.session_state.emotions.append(emotion)
    st.session_state.confidences.append(confidence)
    st.markdown(f"<span style='background:{COLORS.get(emotion,'#D3D1C7')};padding:3px 12px;border-radius:20px;font-size:12px;font-weight:500'>{EMOJIS.get(emotion,'💬')} {emotion.capitalize()} detected • {confidence}% confidence</span>", unsafe_allow_html=True)
    reply = get_smart_response(prompt, emotion, all_probs)
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
