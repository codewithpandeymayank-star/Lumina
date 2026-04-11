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
            system_msg = f"""You are Lumina — a warm, professional, empathetic AI mental health companion.
The user's detected emotion is: {emotion} (confidence: {confidence}%)
Rules:
- Talk like a caring, insightful friend — never robotic
- Remember the full conversation and refer back naturally
- Ask ONE thoughtful follow-up question per response
- Always validate feelings before offering perspective
- Keep responses to 1-2 sentences maximum
- Use emojis sparingly and meaningfully
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
            prompt = f"You are Lumina — empathetic AI companion. Emotion: {emotion}. Reply in 1-2 sentences max.\n"
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
                    max_output_tokens=80, temperature=0.8,
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
                return "AI is momentarily busy — please try again. 🙏"
            return f"Error: {str(e)}"
    return "Please configure your API key in the sidebar. 🔑"

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
                                     fontSize=20, textColor=colors.HexColor('#0f172a'),
                                     spaceAfter=6, alignment=TA_CENTER)
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
                                        fontSize=11, textColor=colors.HexColor('#0ea5e9'),
                                        spaceAfter=4, alignment=TA_CENTER)
        story.append(Paragraph("Lumina — Mental Health Session Report", title_style))
        story.append(Paragraph("Emotion-Aware AI Companion Analysis", subtitle_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#0ea5e9')))
        story.append(Spacer(1, 0.2*inch))

        section_style = ParagraphStyle('Section', parent=styles['Heading2'],
                                       fontSize=13, textColor=colors.HexColor('#0f172a'),
                                       spaceBefore=12, spaceAfter=6)
        story.append(Paragraph("Session Summary", section_style))

        emotion_counts = {}
        for e in emotions:
            emotion_counts[e] = emotion_counts.get(e, 0) + 1

        dominant = max(emotion_counts, key=emotion_counts.get) if emotion_counts else "N/A"
        avg_conf = round(sum(confidences)/len(confidences), 1) if confidences else 0
        crisis_count = sum(1 for m in messages if m['role'] == 'user' and is_crisis(m['content']))

        if crisis_count > 0:
            risk_level, risk_color = "HIGH RISK", colors.HexColor('#dc2626')
            recommendation = "IMMEDIATE professional consultation recommended"
        elif dominant in ['sadness', 'fear', 'anger'] and len(emotions) > 3:
            risk_level, risk_color = "MODERATE RISK", colors.HexColor('#f97316')
            recommendation = "Professional consultation suggested"
        else:
            risk_level, risk_color = "LOW RISK", colors.HexColor('#16a34a')
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
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f0f9ff'), colors.white]),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e0f2fe')),
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
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0ea5e9')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f0f9ff'), colors.white]),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e0f2fe')),
                ('FONTSIZE', (0,0), (-1,-1), 10),
                ('PADDING', (0,0), (-1,-1), 7),
            ]))
            story.append(emo_table)
            story.append(Spacer(1, 0.2*inch))

        story.append(Paragraph("Full Conversation Log", section_style))
        user_style = ParagraphStyle('User', parent=styles['Normal'],
                                    fontSize=9, textColor=colors.HexColor('#0f172a'),
                                    backColor=colors.HexColor('#e0f2fe'),
                                    borderPadding=6, spaceAfter=4)
        bot_style = ParagraphStyle('Bot', parent=styles['Normal'],
                                   fontSize=9, textColor=colors.HexColor('#0f172a'),
                                   backColor=colors.HexColor('#f0fdf4'),
                                   borderPadding=6, spaceAfter=4)
        label_style = ParagraphStyle('Label', parent=styles['Normal'],
                                     fontSize=8, textColor=colors.HexColor('#64748b'), spaceAfter=2)

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
                fb_text = " | Feedback: Helpful ✓" if fb == "up" else " | Feedback: Not helpful" if fb == "down" else ""
                story.append(Paragraph(f"Lumina — {ts}{fb_text}", label_style))
                story.append(Paragraph(msg['content'], bot_style))

        story.append(Spacer(1, 0.2*inch))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e0f2fe')))
        story.append(Paragraph("Clinician Notes", section_style))
        notes_data = [['', ''], ['', ''], ['', ''], ['', ''], ['', '']]
        notes_table = Table(notes_data, colWidths=[6.5*inch, 0.1*inch])
        notes_table.setStyle(TableStyle([
            ('LINEBELOW', (0,0), (0,-1), 0.5, colors.HexColor('#94a3b8')),
            ('ROWHEIGHT', (0,0), (-1,-1), 25),
        ]))
        story.append(notes_table)
        story.append(Spacer(1, 0.15*inch))

        disc_style = ParagraphStyle('Disc', parent=styles['Normal'],
                                    fontSize=8, textColor=colors.HexColor('#94a3b8'), alignment=TA_CENTER)
        story.append(Paragraph(
            "This report is AI-generated to assist mental health professionals only. It is not a clinical diagnosis. "
            "Always consult a qualified professional for clinical decisions.", disc_style))
        story.append(Paragraph("Generated by Lumina | github.com/codewithpandeymayank-star/Lumina", disc_style))

        doc.build(story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"PDF Error: {str(e)}")
        return None


# ─────────────────────────────────────────────
st.set_page_config(page_title="Lumina · Chat", page_icon="🌙", layout="centered")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

    *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
    html, body, .stApp { font-family: 'DM Sans', sans-serif; background: #080b12; color: #c8d0e0; }

    #MainMenu, footer { visibility: hidden; }
    header { visibility: hidden; }

    /* Canvas */
    .stApp::before {
        content: '';
        position: fixed; inset: 0; z-index: 0; pointer-events: none;
        background:
            radial-gradient(ellipse 600px 600px at -10% -10%, rgba(14,165,233,0.07) 0%, transparent 70%),
            radial-gradient(ellipse 500px 500px at 110% 110%, rgba(99,102,241,0.06) 0%, transparent 70%);
    }

    /* ── Header ── */
    .chat-header {
        text-align: center;
        padding: 32px 0 20px;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        margin-bottom: 24px;
        position: relative;
    }
    .header-brand {
        font-family: 'Sora', sans-serif;
        font-size: 1.5rem; font-weight: 800;
        color: #f0f4ff; letter-spacing: -0.5px;
        display: flex; align-items: center; justify-content: center; gap: 10px;
        margin-bottom: 6px;
    }
    .live-dot {
        width: 8px; height: 8px; border-radius: 50%;
        background: #10b981; box-shadow: 0 0 10px #10b981;
        animation: pulse-live 2.5s ease-in-out infinite;
        display: inline-block;
    }
    @keyframes pulse-live {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.4; transform: scale(0.6); }
    }
    .header-sub { font-size: 0.8rem; color: #2d3748; font-weight: 300; margin-bottom: 14px; }
    .pills { display: flex; justify-content: center; gap: 8px; flex-wrap: wrap; }
    .pill {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 100px; padding: 3px 12px;
        font-size: 10.5px; color: #2d3748; font-weight: 500; letter-spacing: 0.2px;
    }
    .pill-live { border-color: rgba(16,185,129,0.3); color: #10b981; }

    /* ── Emotion badge ── */
    .emo-badge {
        display: inline-flex; align-items: center; gap: 5px;
        padding: 3px 11px; border-radius: 100px;
        font-size: 10.5px; font-weight: 600; margin-top: 6px;
        letter-spacing: 0.2px;
    }
    .ts { color: #1e2733; font-size: 10px; margin-left: 4px; }

    /* ── Chat messages ── */
    [data-testid="stChatMessage"] {
        background: transparent !important;
        padding: 3px 0 !important;
    }
    [data-testid="stChatMessageContent"] {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 16px !important;
        color: #c8d0e0 !important;
        font-size: 0.9rem !important;
        line-height: 1.65 !important;
        font-family: 'DM Sans', sans-serif !important;
    }

    /* ── Crisis ── */
    .crisis-box {
        background: rgba(220,38,38,0.06);
        border: 1px solid rgba(220,38,38,0.3);
        border-radius: 16px; padding: 20px;
        margin: 6px 0; font-size: 0.88rem; line-height: 1.7;
    }

    /* ── Sidebar ── */
    div[data-testid="stSidebar"] {
        background: rgba(5,8,15,0.95) !important;
        border-right: 1px solid rgba(255,255,255,0.05) !important;
        backdrop-filter: blur(16px) !important;
    }
    .sb-label {
        font-family: 'Sora', sans-serif;
        font-size: 9.5px; font-weight: 700;
        color: #1e2733; text-transform: uppercase;
        letter-spacing: 1.5px; margin-bottom: 10px;
    }
    .sb-status {
        display: flex; align-items: center; gap: 8px;
        background: rgba(16,185,129,0.06);
        border: 1px solid rgba(16,185,129,0.15);
        border-radius: 10px; padding: 8px 12px;
        font-size: 0.8rem; color: #10b981; margin-bottom: 4px;
    }

    /* ── Chat input ── */
    div[data-testid="stChatInput"] textarea {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 14px !important;
        color: #c8d0e0 !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.9rem !important;
    }
    div[data-testid="stChatInput"] textarea:focus {
        border-color: rgba(14,165,233,0.3) !important;
        box-shadow: 0 0 0 2px rgba(14,165,233,0.08) !important;
    }

    /* ── Buttons ── */
    .stButton button {
        border-radius: 10px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="chat-header">
    <div class="header-brand">
        <span class="live-dot"></span> Lumina
    </div>
    <div class="header-sub">Emotion-Aware AI Mental Health Companion</div>
    <div class="pills">
        <span class="pill pill-live">● Live</span>
        <span class="pill">Groq · LLaMA 3.1</span>
        <span class="pill">92.4% Accuracy</span>
        <span class="pill">8 Emotions</span>
        <span class="pill">Crisis Detection</span>
        <span class="pill">PDF Export</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Load model
with st.spinner("Initialising emotion model…"):
    tokenizer, model, le = load_model()

# Session state
for k in ['messages', 'emotions', 'confidences', 'timestamps', 'feedback']:
    if k not in st.session_state:
        st.session_state[k] = {} if k == 'feedback' else []

COLORS = {
    'joy':      ('background:rgba(133,77,14,0.5);color:#fef08a;border:1px solid rgba(133,77,14,0.6)', '😊'),
    'sadness':  ('background:rgba(30,58,95,0.5);color:#93c5fd;border:1px solid rgba(30,58,95,0.6)', '😢'),
    'anger':    ('background:rgba(127,29,29,0.5);color:#fca5a5;border:1px solid rgba(127,29,29,0.6)', '😠'),
    'fear':     ('background:rgba(46,16,101,0.5);color:#c4b5fd;border:1px solid rgba(46,16,101,0.6)', '😨'),
    'surprise': ('background:rgba(6,78,59,0.5);color:#6ee7b7;border:1px solid rgba(6,78,59,0.6)', '😲'),
    'love':     ('background:rgba(131,24,67,0.5);color:#f9a8d4;border:1px solid rgba(131,24,67,0.6)', '❤️'),
    'neutral':  ('background:rgba(31,41,55,0.5);color:#9ca3af;border:1px solid rgba(31,41,55,0.6)', '💬'),
    'disgust':  ('background:rgba(26,58,26,0.5);color:#86efac;border:1px solid rgba(26,58,26,0.6)', '🤢'),
}

# Sidebar
with st.sidebar:
    st.markdown("<div class='sb-label'>Connection</div>", unsafe_allow_html=True)
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
        groq_key = st.secrets.get("GROQ_API_KEY", "")
        if groq_key:
            st.markdown("<div class='sb-status'>✅ Groq AI Connected</div>", unsafe_allow_html=True)
        elif api_key:
            st.markdown("<div class='sb-status'>✅ Gemini Connected</div>", unsafe_allow_html=True)
        else:
            st.warning("⚠️ No API key found")
    except:
        api_key, groq_key = "", ""
        st.warning("⚠️ No API key found")

    st.divider()
    st.markdown("<div class='sb-label'>Emotion Timeline</div>", unsafe_allow_html=True)

    if st.session_state.emotions:
        emotion_order = {'joy': 6, 'love': 5, 'surprise': 4, 'neutral': 3, 'fear': 2, 'sadness': 1, 'anger': 0, 'disgust': 0}
        df = pd.DataFrame({
            'msg': range(1, len(st.session_state.emotions)+1),
            'Mood': [emotion_order.get(e, 3) for e in st.session_state.emotions]
        })
        st.line_chart(df.set_index('msg')['Mood'], height=130)
        st.caption("↑ Positive  ·  ↓ Negative")
        st.divider()

        st.markdown("<div class='sb-label'>Session Insights</div>", unsafe_allow_html=True)
        total = len(st.session_state.emotions)
        emotion_counts = {}
        for emo in st.session_state.emotions:
            emotion_counts[emo] = emotion_counts.get(emo, 0) + 1
        dominant = max(emotion_counts, key=emotion_counts.get)
        style, emoji = COLORS.get(dominant, COLORS['neutral'])
        st.markdown(
            f"**{total} messages** &nbsp;·&nbsp; Dominant: "
            f"<span class='emo-badge' style='{style}'>{emoji} {dominant.capitalize()}</span>",
            unsafe_allow_html=True
        )
        st.write("")
        for emo, count in sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True):
            pct = round(count/total*100)
            s, em = COLORS.get(emo, COLORS['neutral'])
            st.markdown(f"<span class='emo-badge' style='{s}'>{em} {emo.capitalize()} · {count} ({pct}%)</span>", unsafe_allow_html=True)
            st.write("")
        avg_conf = round(sum(st.session_state.confidences)/len(st.session_state.confidences), 1)
        st.caption(f"Avg confidence: {avg_conf}%")
        st.divider()

        st.markdown("<div class='sb-label'>Export Report</div>", unsafe_allow_html=True)
        st.text_input("Patient name", placeholder="Anonymous", key="patient_name")
        st.text_input("Clinician name", placeholder="Dr.", key="doctor_name")
        if st.button("📥 Generate PDF Report", use_container_width=True, type="primary"):
            with st.spinner("Building report…"):
                try:
                    import subprocess
                    subprocess.run(["pip", "install", "reportlab", "-q"], capture_output=True)
                    pdf_buffer = generate_pdf_report(
                        st.session_state.messages, st.session_state.emotions,
                        st.session_state.confidences, st.session_state.timestamps,
                        st.session_state.feedback
                    )
                    if pdf_buffer:
                        fname = f"lumina_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                        st.download_button("⬇️ Download PDF", data=pdf_buffer,
                                           file_name=fname, mime="application/pdf",
                                           use_container_width=True)
                        st.success("Report ready!")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    else:
        st.caption("Start chatting to see insights.")

    st.divider()
    if st.button("↺  New Conversation", use_container_width=True):
        for k in ['messages', 'emotions', 'confidences', 'timestamps']:
            st.session_state[k] = []
        st.session_state.feedback = {}
        st.rerun()

# Chat history
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
                st.markdown(
                    f"<span class='emo-badge' style='{style}'>{emoji} {emo.capitalize()} · {conf}%</span>"
                    f"<span class='ts'>{ts}</span>",
                    unsafe_allow_html=True
                )
        else:
            c1, c2, c3 = st.columns([1, 1, 9])
            with c1:
                if st.button("👍", key=f"up_{i}", help="Helpful"):
                    st.session_state.feedback[i] = "up"
            with c2:
                if st.button("👎", key=f"dn_{i}", help="Not helpful"):
                    st.session_state.feedback[i] = "down"
            if i in st.session_state.feedback:
                st.caption("✅ Thanks!" if st.session_state.feedback[i] == "up" else "📝 Noted — we'll improve!")

# Input
if prompt := st.chat_input("Share what's on your mind…"):
    ts = datetime.now().strftime("%I:%M %p")
    with st.chat_message('user'):
        st.write(prompt)
    st.session_state.timestamps.append(ts)

    emotion, confidence = predict_emotion(prompt, tokenizer, model, le)
    st.session_state.emotions.append(emotion)
    st.session_state.confidences.append(confidence)
    style, emoji = COLORS.get(emotion, COLORS['neutral'])
    st.markdown(
        f"<span class='emo-badge' style='{style}'>{emoji} {emotion.capitalize()} · {confidence}%</span>"
        f"<span class='ts'>{ts}</span>",
        unsafe_allow_html=True
    )
    st.session_state.messages.append({'role': 'user', 'content': prompt})

    if is_crisis(prompt):
        crisis_reply = """I'm really concerned about you right now. Please reach out immediately.

🆘 iCall (India): 9152987821
🆘 Vandrevala Foundation: 1860-2662-345 (24/7)
🆘 AASRA: 9820466627
🆘 National Helpline: 14416

You are not alone — people care about you. 💙"""
        with st.chat_message('assistant'):
            st.markdown(f"<div class='crisis-box'>🚨 <strong>Crisis Support</strong><br><br>{crisis_reply}</div>", unsafe_allow_html=True)
        st.session_state.messages.append({'role': 'assistant', 'content': crisis_reply})
        st.session_state.timestamps.append(ts)
    else:
        with st.chat_message('assistant'):
            reply = get_ai_response(st.session_state.messages, emotion, confidence, api_key, groq_key)
            if reply:
                st.write(reply)
                st.session_state.messages.append({'role': 'assistant', 'content': reply})
                st.session_state.timestamps.append(ts)
    st.rerun()
