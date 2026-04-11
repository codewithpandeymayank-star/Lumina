import streamlit as st
import torch
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification
import pickle
from google import genai
from google.genai import types
from huggingface_hub import hf_hub_download
from groq import Groq
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
    negation_words = ['not good', 'not ok', 'not fine', 'not well', 'not great',
                      'actually not', 'but not', 'dont feel good', 'do not feel good',
                      'not feeling good', 'not feeling well', 'not happy', 'not okay']
    text_lower = text.lower()
    if any(neg in text_lower for neg in negation_words):
        if emotion in ["joy", "love", "surprise"]:
            emotion = "sadness"
    return emotion, round(confidence * 100, 1)

def get_ai_response(messages, emotion, confidence, api_key, groq_key):
    if groq_key:
        try:
            client = Groq(api_key=groq_key)
            system_msg = f"""You are Lumina — a professional, warm, empathetic AI mental health companion.
The user's detected emotion is: {emotion} (confidence: {confidence}%)
Rules:
- Talk like a caring friend, not a robot
- Remember the full conversation naturally
- Ask ONE thoughtful follow-up question
- Validate feelings before giving advice
- Keep responses STRICTLY 1-2 sentences maximum
- Use emojis occasionally
- Never say 'As an AI'
- Never give medical diagnosis"""
            conversation = [{"role": "system", "content": system_msg}]
            for msg in messages:
                role = "user" if msg['role'] == 'user' else "assistant"
                conversation.append({"role": role, "content": msg['content']})
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=conversation,
                max_tokens=100,
                temperature=0.8,
            )
            return response.choices[0].message.content
        except Exception as e:
            if '429' not in str(e) and 'limit' not in str(e).lower():
                return f"Error: {str(e)}"

    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            prompt = f"You are Lumina — empathetic AI. Emotion: {emotion}. Reply in 1-2 sentences max.\n"
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
            if '429' in str(e) or 'EXHAUSTED' in str(e):
                return "Daily AI limit reached. Please try again tomorrow. 🙏"
            if '503' in str(e) or 'UNAVAILABLE' in str(e):
                return "AI is busy right now, please try again in a moment. 🙏"
            return f"Error: {str(e)}"
    return "Please configure your API key. 🔑"

def generate_pdf_report(messages, emotions, confidences, timestamps, feedback):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.enums import TA_CENTER

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=0.75*inch, leftMargin=0.75*inch,
                                topMargin=0.75*inch, bottomMargin=0.75*inch)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle('Title', parent=styles['Title'],
                                     fontSize=20, textColor=colors.HexColor('#1a1a2e'),
                                     spaceAfter=6, alignment=TA_CENTER)
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
                                        fontSize=11, textColor=colors.HexColor('#4a4a8a'),
                                        spaceAfter=4, alignment=TA_CENTER)
        story.append(Paragraph("Lumina — Mental Health Session Report", title_style))
        story.append(Paragraph("Emotion-Aware AI Companion Analysis", subtitle_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#4a4a8a')))
        story.append(Spacer(1, 0.2*inch))

        section_style = ParagraphStyle('Section', parent=styles['Heading2'],
                                       fontSize=13, textColor=colors.HexColor('#1a1a2e'),
                                       spaceBefore=12, spaceAfter=6)
        story.append(Paragraph("Session Summary", section_style))

        emotion_counts = {}
        for e in emotions:
            emotion_counts[e] = emotion_counts.get(e, 0) + 1

        dominant = max(emotion_counts, key=emotion_counts.get) if emotion_counts else "N/A"
        avg_conf = round(sum(confidences)/len(confidences), 1) if confidences else 0
        crisis_count = sum(1 for m in messages if m['role'] == 'user' and is_crisis(m['content']))

        if crisis_count > 0:
            risk_level = "HIGH RISK"
            risk_color = colors.HexColor('#cc0000')
            recommendation = "IMMEDIATE professional consultation recommended"
        elif dominant in ['sadness', 'fear', 'anger'] and len(emotions) > 3:
            risk_level = "MODERATE RISK"
            risk_color = colors.HexColor('#ff8800')
            recommendation = "Professional consultation suggested"
        else:
            risk_level = "LOW RISK"
            risk_color = colors.HexColor('#006600')
            recommendation = "Regular monitoring recommended"

        summary_data = [
            ['Metric', 'Value'],
            ['Total Messages', str(len([m for m in messages if m['role'] == 'user']))],
            ['Dominant Emotion', dominant.capitalize()],
            ['Average Confidence', f"{avg_conf}%"],
            ['Crisis Signals Detected', str(crisis_count)],
            ['Risk Assessment', risk_level],
            ['Recommendation', recommendation],
        ]

        summary_table = Table(summary_data, colWidths=[2.5*inch, 4*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f0f2ff'), colors.white]),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#ccccdd')),
            ('FONTNAME', (0,1), (0,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('PADDING', (0,0), (-1,-1), 8),
            ('TEXTCOLOR', (1,5), (1,5), risk_color),
            ('FONTNAME', (1,5), (1,5), 'Helvetica-Bold'),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.2*inch))

        story.append(Paragraph("Emotion Distribution", section_style))
        if emotion_counts:
            total = len(emotions)
            indicators = {
                'joy': 'Positive — Good mental state',
                'love': 'Positive — Strong social connection',
                'surprise': 'Neutral — Reactive state',
                'neutral': 'Neutral — Stable baseline',
                'fear': 'Negative — Anxiety/stress present',
                'sadness': 'Negative — Depression risk',
                'anger': 'Negative — Frustration/aggression',
                'disgust': 'Negative — Aversion/discomfort',
            }
            emo_data = [['Emotion', 'Count', 'Percentage', 'Mental Health Indicator']]
            for emo, count in sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True):
                pct = round(count/total*100, 1)
                emo_data.append([emo.capitalize(), str(count), f"{pct}%", indicators.get(emo, 'N/A')])

            emo_table = Table(emo_data, colWidths=[1.2*inch, 0.8*inch, 1*inch, 3.5*inch])
            emo_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4a4a8a')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f0f2ff'), colors.white]),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#ccccdd')),
                ('FONTSIZE', (0,0), (-1,-1), 10),
                ('PADDING', (0,0), (-1,-1), 7),
            ]))
            story.append(emo_table)
            story.append(Spacer(1, 0.2*inch))

        story.append(Paragraph("Full Conversation Log", section_style))
        user_style = ParagraphStyle('User', parent=styles['Normal'],
                                    fontSize=9, textColor=colors.HexColor('#1a1a2e'),
                                    backColor=colors.HexColor('#e8f0fe'),
                                    borderPadding=6, spaceAfter=4)
        bot_style = ParagraphStyle('Bot', parent=styles['Normal'],
                                   fontSize=9, textColor=colors.HexColor('#1a1a2e'),
                                   backColor=colors.HexColor('#f0fff0'),
                                   borderPadding=6, spaceAfter=4)
        label_style = ParagraphStyle('Label', parent=styles['Normal'],
                                     fontSize=8, textColor=colors.HexColor('#666688'),
                                     spaceAfter=2)

        emotion_idx = 0
        for i, msg in enumerate(messages):
            ts = timestamps[i] if i < len(timestamps) else ""
            if msg['role'] == 'user':
                emo = emotions[emotion_idx] if emotion_idx < len(emotions) else ""
                conf = confidences[emotion_idx] if emotion_idx < len(confidences) else ""
                story.append(Paragraph(f"User — {ts} | Emotion: {emo.capitalize()} ({conf}%)", label_style))
                story.append(Paragraph(msg['content'], user_style))
                emotion_idx += 1
            else:
                fb = feedback.get(i, "")
                fb_text = " | Feedback: Helpful" if fb == "up" else " | Feedback: Not helpful" if fb == "down" else ""
                story.append(Paragraph(f"Lumina — {ts}{fb_text}", label_style))
                story.append(Paragraph(msg['content'], bot_style))

        story.append(Spacer(1, 0.2*inch))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#ccccdd')))
        story.append(Paragraph("Doctor / Therapist Notes", section_style))
        notes_data = [['', ''], ['', ''], ['', ''], ['', ''], ['', '']]
        notes_table = Table(notes_data, colWidths=[6.5*inch, 0.1*inch])
        notes_table.setStyle(TableStyle([
            ('LINEBELOW', (0,0), (0,-1), 0.5, colors.HexColor('#999999')),
            ('ROWHEIGHT', (0,0), (-1,-1), 25),
        ]))
        story.append(notes_table)
        story.append(Spacer(1, 0.15*inch))

        disclaimer_style = ParagraphStyle('Disclaimer', parent=styles['Normal'],
                                          fontSize=8, textColor=colors.HexColor('#888888'),
                                          alignment=TA_CENTER)
        story.append(Paragraph(
            "This report is generated by an AI system and is intended to assist mental health professionals only. "
            "It is not a medical diagnosis. Always consult a qualified professional for clinical decisions.",
            disclaimer_style))
        story.append(Paragraph(
            "Generated by Lumina | github.com/codewithpandeymayank-star/lumina",
            disclaimer_style))

        doc.build(story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"PDF Error: {str(e)}")
        return None

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
        <span class="status-pill">Groq + Llama 3</span>
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
        api_key = st.secrets.get("GEMINI_API_KEY", "")
        groq_key = st.secrets.get("GROQ_API_KEY", "")
        if groq_key:
            st.success("✅ Groq AI Connected")
        elif api_key:
            st.success("✅ Gemini Connected")
        else:
            st.warning("⚠️ No API key found")
    except:
        api_key = ""
        groq_key = ""
        st.warning("⚠️ No API key found")

    st.divider()
    st.markdown("<p class='sidebar-section'>Emotion Timeline</p>", unsafe_allow_html=True)
    if st.session_state.emotions:
        emotion_order = {'joy': 6, 'love': 5, 'surprise': 4, 'neutral': 3, 'fear': 2, 'sadness': 1, 'anger': 0, 'disgust': 0}
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
    else:
        with st.chat_message('assistant'):
            reply = get_ai_response(
                st.session_state.messages,
                emotion, confidence, api_key, groq_key
            )
            if reply:
                st.write(reply)
                st.session_state.messages.append({'role': 'assistant', 'content': reply})
                st.session_state.timestamps.append(ts)
    st.rerun()