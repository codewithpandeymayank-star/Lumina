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
import plotly.graph_objects as go

MODEL_REPO = "GabbarM32/emotion-chatbot-model"

CRISIS_KEYWORDS = [
    "kill myself", "want to die", "end my life", "suicide", "suicidal",
    "no reason to live", "better off dead", "want to disappear",
    "can't go on", "cannot go on", "give up on life", "self harm",
    "hurt myself", "cutting myself", "hopeless", "worthless",
    "don't want to be here", "do not want to be here"
]

def is_crisis(text):
    return any(k in text.lower() for k in CRISIS_KEYWORDS)

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
    negation_words = ['not good','not ok','not fine','not well','not great',
                      'actually not','but not','dont feel good','do not feel good',
                      'not feeling good','not feeling well','not happy','not okay']
    if any(n in text.lower() for n in negation_words):
        if emotion in ["joy","love","surprise"]:
            emotion = "sadness"
    return emotion, round(confidence * 100, 1)

def get_ai_response(messages, emotion, confidence, api_key, groq_key):
    if groq_key:
        try:
            client = Groq(api_key=groq_key)
            system_msg = f"""You are Lumina, a warm empathetic AI mental health companion.
Detected emotion: {emotion} ({confidence}%). Rules: talk like a caring friend, validate feelings first,
ask ONE follow-up question, keep to 1-2 sentences, never say 'As an AI', no medical diagnosis."""
            conversation = [{"role": "system", "content": system_msg}]
            for msg in messages:
                role = "user" if msg['role'] == 'user' else "assistant"
                conversation.append({"role": role, "content": msg['content']})
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant", messages=conversation,
                max_tokens=100, temperature=0.8)
            return response.choices[0].message.content
        except Exception as e:
            if '429' not in str(e) and 'limit' not in str(e).lower():
                return f"Error: {str(e)}"
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            prompt = f"You are Lumina, empathetic AI. Emotion: {emotion}. Reply in 1-2 sentences.\n"
            for msg in messages[:-1]:
                prompt += f"{'User' if msg['role']=='user' else 'Lumina'}: {msg['content']}\n"
            prompt += f"\nUser: {messages[-1]['content']}\nLumina:"
            full_reply = ""
            placeholder = st.empty()
            for chunk in client.models.generate_content_stream(
                model="gemini-2.0-flash", contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                    max_output_tokens=80, temperature=0.8)):
                if chunk.text:
                    full_reply += chunk.text
                    placeholder.markdown(full_reply + "▌")
            placeholder.markdown(full_reply)
            return full_reply
        except Exception as e:
            if '429' in str(e) or 'EXHAUSTED' in str(e):
                return "Daily AI limit reached. Please try again tomorrow. 🙏"
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
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=0.75*inch, leftMargin=0.75*inch,
                                topMargin=0.75*inch, bottomMargin=0.75*inch)
        styles = getSampleStyleSheet()
        story = []
        title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=20,
                                     textColor=colors.HexColor('#0f172a'), spaceAfter=6, alignment=TA_CENTER)
        subtitle_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=11,
                                        textColor=colors.HexColor('#0ea5e9'), spaceAfter=4, alignment=TA_CENTER)
        story.append(Paragraph("Lumina — Mental Health Session Report", title_style))
        story.append(Paragraph("Emotion-Aware AI Companion Analysis", subtitle_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#0ea5e9')))
        story.append(Spacer(1, 0.2*inch))
        section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=13,
                                       textColor=colors.HexColor('#0f172a'), spaceBefore=12, spaceAfter=6)
        story.append(Paragraph("Session Summary", section_style))
        emotion_counts = {}
        for e in emotions:
            emotion_counts[e] = emotion_counts.get(e, 0) + 1
        dominant = max(emotion_counts, key=emotion_counts.get) if emotion_counts else "N/A"
        avg_conf = round(sum(confidences)/len(confidences), 1) if confidences else 0
        crisis_count = sum(1 for m in messages if m['role']=='user' and is_crisis(m['content']))
        if crisis_count > 0:
            risk_level, risk_color = "HIGH RISK", colors.HexColor('#dc2626')
            recommendation = "IMMEDIATE professional consultation recommended"
        elif dominant in ['sadness','fear','anger'] and len(emotions) > 3:
            risk_level, risk_color = "MODERATE RISK", colors.HexColor('#f97316')
            recommendation = "Professional consultation suggested"
        else:
            risk_level, risk_color = "LOW RISK", colors.HexColor('#16a34a')
            recommendation = "Regular monitoring recommended"
        summary_data = [['Metric','Value'],
            ['Total Messages', str(len([m for m in messages if m['role']=='user']))],
            ['Dominant Emotion', dominant.capitalize()],
            ['Average Confidence', f"{avg_conf}%"],
            ['Crisis Signals', str(crisis_count)],
            ['Risk Level', risk_level],
            ['Recommendation', recommendation]]
        st_table = Table(summary_data, colWidths=[2.5*inch, 4*inch])
        st_table.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0f172a')),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#f0f9ff'),colors.white]),
            ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#e0f2fe')),
            ('FONTNAME',(0,1),(0,-1),'Helvetica-Bold'),
            ('FONTSIZE',(0,0),(-1,-1),10),('PADDING',(0,0),(-1,-1),8),
            ('TEXTCOLOR',(1,5),(1,5),risk_color),('FONTNAME',(1,5),(1,5),'Helvetica-Bold')]))
        story.append(st_table)
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("Emotion Distribution", section_style))
        if emotion_counts:
            total = len(emotions)
            indicators = {'joy':'Positive — Good mental state','love':'Positive — Strong social connection',
                'surprise':'Neutral — Reactive state','neutral':'Neutral — Stable baseline',
                'fear':'Negative — Anxiety/stress','sadness':'Negative — Depression risk',
                'anger':'Negative — Frustration','disgust':'Negative — Aversion'}
            emo_data = [['Emotion','Count','%','Mental Health Indicator']]
            for emo, count in sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True):
                emo_data.append([emo.capitalize(), str(count), f"{round(count/total*100,1)}%", indicators.get(emo,'N/A')])
            emo_table = Table(emo_data, colWidths=[1.2*inch,0.8*inch,1*inch,3.5*inch])
            emo_table.setStyle(TableStyle([
                ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0ea5e9')),
                ('TEXTCOLOR',(0,0),(-1,0),colors.white),
                ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
                ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#f0f9ff'),colors.white]),
                ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#e0f2fe')),
                ('FONTSIZE',(0,0),(-1,-1),10),('PADDING',(0,0),(-1,-1),7)]))
            story.append(emo_table)
            story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("Conversation Log", section_style))
        user_style = ParagraphStyle('User', parent=styles['Normal'], fontSize=9,
                                    textColor=colors.HexColor('#0f172a'),
                                    backColor=colors.HexColor('#e0f2fe'), borderPadding=6, spaceAfter=4)
        bot_style = ParagraphStyle('Bot', parent=styles['Normal'], fontSize=9,
                                   textColor=colors.HexColor('#0f172a'),
                                   backColor=colors.HexColor('#f0fdf4'), borderPadding=6, spaceAfter=4)
        label_style = ParagraphStyle('Lbl', parent=styles['Normal'], fontSize=8,
                                     textColor=colors.HexColor('#64748b'), spaceAfter=2)
        emotion_idx = 0
        for i, msg in enumerate(messages):
            ts = timestamps[i] if i < len(timestamps) else ""
            if msg['role'] == 'user':
                emo = emotions[emotion_idx] if emotion_idx < len(emotions) else ""
                conf = confidences[emotion_idx] if emotion_idx < len(confidences) else ""
                story.append(Paragraph(f"User — {ts} | {emo.capitalize()} ({conf}%)", label_style))
                story.append(Paragraph(msg['content'], user_style))
                emotion_idx += 1
            else:
                fb = feedback.get(i,"")
                fb_text = " | Helpful" if fb=="up" else " | Not helpful" if fb=="down" else ""
                story.append(Paragraph(f"Lumina — {ts}{fb_text}", label_style))
                story.append(Paragraph(msg['content'], bot_style))
        story.append(Spacer(1,0.2*inch))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e0f2fe')))
        story.append(Paragraph("Clinician Notes", section_style))
        notes_table = Table([[''],[''],[''],[''],['']]*1, colWidths=[6.5*inch])
        notes_table.setStyle(TableStyle([('LINEBELOW',(0,0),(0,-1),0.5,colors.HexColor('#94a3b8')),('ROWHEIGHT',(0,0),(-1,-1),25)]))
        story.append(notes_table)
        story.append(Spacer(1,0.15*inch))
        disc = ParagraphStyle('Disc', parent=styles['Normal'], fontSize=8,
                              textColor=colors.HexColor('#94a3b8'), alignment=TA_CENTER)
        story.append(Paragraph("AI-generated report for professional reference only. Not a clinical diagnosis.", disc))
        story.append(Paragraph("Generated by Lumina | github.com/codewithpandeymayank-star/Lumina", disc))
        doc.build(story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"PDF Error: {str(e)}")
        return None

def make_emotion_chart(emotions, confidences):
    if not emotions:
        return None
    emotion_order = {'joy':7,'love':6,'surprise':5,'neutral':4,'fear':3,'sadness':2,'anger':1,'disgust':0}
    emotion_colors = {'joy':'#F59E0B','love':'#EC4899','surprise':'#14B8A6','neutral':'#94A3B8',
                      'fear':'#8B5CF6','sadness':'#3B82F6','anger':'#EF4444','disgust':'#22C55E'}
    emojis = {'joy':'😊','love':'❤️','surprise':'😲','neutral':'💬','fear':'😨','sadness':'😢','anger':'😠','disgust':'🤢'}
    scores = [emotion_order.get(e,4) for e in emotions]
    colors_list = [emotion_colors.get(e,'#94A3B8') for e in emotions]
    x = list(range(1, len(emotions)+1))
    hover_texts = [f"{emojis.get(e,'•')} {e.capitalize()}<br>Confidence: {c}%" for e,c in zip(emotions, confidences)]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=scores, fill='tozeroy', fillcolor='rgba(14,165,233,0.07)',
                             line=dict(width=0), showlegend=False, hoverinfo='skip'))
    fig.add_trace(go.Scatter(
        x=x, y=scores, mode='lines+markers',
        line=dict(color='rgba(14,165,233,0.6)', width=2.5, shape='spline', smoothing=1.3),
        marker=dict(size=11, color=colors_list, line=dict(color='white', width=2.5), symbol='circle'),
        text=hover_texts, hovertemplate='%{text}<extra></extra>', showlegend=False))
    fig.add_hrect(y0=5.5, y1=7.8, fillcolor='rgba(16,185,129,0.04)', line_width=0,
                  annotation_text="Positive", annotation_position="right",
                  annotation_font=dict(color='rgba(16,185,129,0.45)', size=8))
    fig.add_hrect(y0=3.5, y1=5.5, fillcolor='rgba(148,163,184,0.03)', line_width=0,
                  annotation_text="Neutral", annotation_position="right",
                  annotation_font=dict(color='rgba(148,163,184,0.4)', size=8))
    fig.add_hrect(y0=-0.3, y1=3.5, fillcolor='rgba(239,68,68,0.04)', line_width=0,
                  annotation_text="Negative", annotation_position="right",
                  annotation_font=dict(color='rgba(239,68,68,0.4)', size=8))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=4, r=64, t=4, b=4), height=170,
        xaxis=dict(showgrid=False, showline=False, zeroline=False,
                   tickfont=dict(color='rgba(100,116,139,0.7)', size=9), title='', dtick=1),
        yaxis=dict(showgrid=True, gridcolor='rgba(14,165,233,0.06)', showline=False, zeroline=False,
                   ticktext=['Disgust','Anger','Sadness','Fear','Neutral','Surprise','Love','Joy'],
                   tickvals=[0,1,2,3,4,5,6,7],
                   tickfont=dict(color='rgba(100,116,139,0.6)', size=8), range=[-0.3,7.8]),
        hoverlabel=dict(bgcolor='#1e293b', bordercolor='rgba(14,165,233,0.4)',
                        font=dict(color='white', size=12)))
    return fig

# ─────────────────────────────────────────────
st.set_page_config(page_title="Lumina · Chat", page_icon="🌙", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=DM+Sans:wght@300;400;500&display=swap');
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
html,body,.stApp{font-family:'DM Sans',sans-serif;background:#f8fafc;color:#1e293b}
#MainMenu,footer{visibility:hidden}header{visibility:hidden}
.stApp{background:linear-gradient(135deg,#f0f9ff 0%,#f8fafc 50%,#fdf4ff 100%);min-height:100vh}
.lumina-header{background:rgba(255,255,255,0.88);backdrop-filter:blur(20px);border-bottom:1px solid rgba(14,165,233,0.12);padding:18px 0 14px;text-align:center;margin-bottom:8px;position:sticky;top:0;z-index:100}
.lumina-logo{font-family:'Plus Jakarta Sans',sans-serif;font-size:1.4rem;font-weight:700;color:#0f172a;letter-spacing:-0.5px;display:flex;align-items:center;justify-content:center;gap:8px;margin-bottom:9px}
.live-dot{width:7px;height:7px;border-radius:50%;background:#10b981;box-shadow:0 0 0 3px rgba(16,185,129,0.2);display:inline-block;animation:pglow 2s infinite}
@keyframes pglow{0%,100%{box-shadow:0 0 0 3px rgba(16,185,129,0.2)}50%{box-shadow:0 0 0 6px rgba(16,185,129,0.06)}}
.header-pills{display:flex;justify-content:center;gap:6px;flex-wrap:wrap}
.pill{background:rgba(14,165,233,0.08);border:1px solid rgba(14,165,233,0.18);color:#0ea5e9;padding:3px 10px;border-radius:100px;font-size:10px;font-weight:600;letter-spacing:0.3px}
.pill-g{background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.2);color:#10b981}
.pill-s{background:rgba(148,163,184,0.08);border:1px solid rgba(148,163,184,0.18);color:#64748b}
.emo-badge{display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:100px;font-size:10.5px;font-weight:600;margin-top:5px}
.ts{color:#94a3b8;font-size:10px;margin-left:4px}
[data-testid="stChatMessage"]{background:transparent!important;padding:2px 0!important}
[data-testid="stChatMessageContent"]{background:rgba(255,255,255,0.92)!important;border:1px solid rgba(14,165,233,0.1)!important;border-radius:18px 18px 18px 4px!important;color:#1e293b!important;font-size:0.9rem!important;line-height:1.65!important;box-shadow:0 2px 14px rgba(0,0,0,0.07)!important;font-family:'DM Sans',sans-serif!important}
.crisis-box{background:linear-gradient(135deg,rgba(254,226,226,0.95),rgba(255,237,213,0.9));border:1px solid rgba(220,38,38,0.2);border-radius:16px;padding:20px;margin:6px 0;font-size:0.88rem;line-height:1.7;box-shadow:0 4px 20px rgba(220,38,38,0.08)}
div[data-testid="stSidebar"]{background:rgba(255,255,255,0.94)!important;border-right:1px solid rgba(14,165,233,0.1)!important;backdrop-filter:blur(20px)!important}
.sb-label{font-family:'Plus Jakarta Sans',sans-serif;font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px;margin-top:2px}
.sb-ok{display:flex;align-items:center;gap:8px;background:linear-gradient(135deg,rgba(16,185,129,0.08),rgba(14,165,233,0.05));border:1px solid rgba(16,185,129,0.2);border-radius:12px;padding:10px 14px;font-size:0.82rem;color:#059669;font-weight:600;margin-bottom:4px}
.stat-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px}
.sc{background:linear-gradient(135deg,rgba(14,165,233,0.07),rgba(99,102,241,0.04));border:1px solid rgba(14,165,233,0.12);border-radius:12px;padding:12px 14px}
.sc-lbl{font-size:9.5px;color:#94a3b8;font-weight:600;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:2px}
.sc-val{font-family:'Plus Jakarta Sans',sans-serif;font-size:1.25rem;font-weight:700;color:#0f172a}
.stButton button{border-radius:12px!important;font-family:'DM Sans',sans-serif!important;font-size:0.85rem!important;font-weight:600!important;transition:all 0.2s!important}
div[data-testid="stChatInput"] textarea{background:rgba(255,255,255,0.97)!important;border:1.5px solid rgba(14,165,233,0.2)!important;border-radius:16px!important;color:#1e293b!important;font-family:'DM Sans',sans-serif!important;font-size:0.9rem!important;box-shadow:0 4px 20px rgba(14,165,233,0.08)!important}
div[data-testid="stChatInput"] textarea:focus{border-color:rgba(14,165,233,0.4)!important;box-shadow:0 4px 24px rgba(14,165,233,0.15)!important}
div[data-testid="stSidebar"] input{background:rgba(248,250,252,0.9)!important;border:1px solid rgba(14,165,233,0.15)!important;border-radius:10px!important;color:#1e293b!important;font-size:0.85rem!important}
hr{border-color:rgba(14,165,233,0.1)!important}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="lumina-header">
    <div class="lumina-logo"><span class="live-dot"></span>Lumina</div>
    <div class="header-pills">
        <span class="pill pill-g">● Live</span>
        <span class="pill">Groq · LLaMA 3.1</span>
        <span class="pill pill-s">92.4% Accuracy</span>
        <span class="pill pill-s">8 Emotions</span>
        <span class="pill pill-s">Crisis Detection</span>
        <span class="pill pill-s">PDF Export</span>
    </div>
</div>
""", unsafe_allow_html=True)

with st.spinner("Initialising emotion model…"):
    tokenizer, model, le = load_model()

for k in ['messages','emotions','confidences','timestamps','feedback']:
    if k not in st.session_state:
        st.session_state[k] = {} if k == 'feedback' else []

COLORS = {
    'joy':     ('background:linear-gradient(135deg,#fef3c7,#fde68a);color:#92400e;border:1px solid rgba(245,158,11,0.3)','😊'),
    'sadness': ('background:linear-gradient(135deg,#dbeafe,#bfdbfe);color:#1e40af;border:1px solid rgba(59,130,246,0.3)','😢'),
    'anger':   ('background:linear-gradient(135deg,#fee2e2,#fecaca);color:#991b1b;border:1px solid rgba(239,68,68,0.3)','😠'),
    'fear':    ('background:linear-gradient(135deg,#ede9fe,#ddd6fe);color:#5b21b6;border:1px solid rgba(139,92,246,0.3)','😨'),
    'surprise':('background:linear-gradient(135deg,#ccfbf1,#99f6e4);color:#065f46;border:1px solid rgba(20,184,166,0.3)','😲'),
    'love':    ('background:linear-gradient(135deg,#fce7f3,#fbcfe8);color:#9d174d;border:1px solid rgba(236,72,153,0.3)','❤️'),
    'neutral': ('background:linear-gradient(135deg,#f1f5f9,#e2e8f0);color:#475569;border:1px solid rgba(148,163,184,0.3)','💬'),
    'disgust': ('background:linear-gradient(135deg,#dcfce7,#bbf7d0);color:#14532d;border:1px solid rgba(34,197,94,0.3)','🤢'),
}

with st.sidebar:
    st.markdown("<div class='sb-label'>Connection</div>", unsafe_allow_html=True)
    try:
        api_key = st.secrets.get("GEMINI_API_KEY","")
        groq_key = st.secrets.get("GROQ_API_KEY","")
        if groq_key:
            st.markdown("<div class='sb-ok'>✅ Groq AI Connected</div>", unsafe_allow_html=True)
        elif api_key:
            st.markdown("<div class='sb-ok'>✅ Gemini Connected</div>", unsafe_allow_html=True)
        else:
            st.warning("⚠️ No API key found")
    except:
        api_key, groq_key = "", ""
        st.warning("⚠️ No API key found")

    st.divider()

    if st.session_state.emotions:
        total = len(st.session_state.emotions)
        emotion_counts = {}
        for emo in st.session_state.emotions:
            emotion_counts[emo] = emotion_counts.get(emo, 0) + 1
        dominant = max(emotion_counts, key=emotion_counts.get)
        avg_conf = round(sum(st.session_state.confidences)/len(st.session_state.confidences), 1)

        st.markdown(f"""
        <div class="stat-grid">
          <div class="sc"><div class="sc-lbl">Messages</div><div class="sc-val">{total}</div></div>
          <div class="sc"><div class="sc-lbl">Avg Conf.</div><div class="sc-val">{avg_conf}%</div></div>
        </div>""", unsafe_allow_html=True)

        style, emoji = COLORS.get(dominant, COLORS['neutral'])
        st.markdown(
            f"<div style='margin-bottom:14px'><div style='font-size:9.5px;color:#94a3b8;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px'>Dominant Emotion</div>"
            f"<span class='emo-badge' style='{style}'>{emoji} {dominant.capitalize()}</span></div>",
            unsafe_allow_html=True)

        st.markdown("<div class='sb-label'>Emotion Journey</div>", unsafe_allow_html=True)
        fig = make_emotion_chart(st.session_state.emotions, st.session_state.confidences)
        if fig:
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar':False})

        st.markdown("<div class='sb-label'>Breakdown</div>", unsafe_allow_html=True)
        for emo, count in sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True):
            pct = round(count/total*100)
            s, em = COLORS.get(emo, COLORS['neutral'])
            st.markdown(
                f"<div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:7px'>"
                f"<span class='emo-badge' style='{s}'>{em} {emo.capitalize()}</span>"
                f"<span style='font-size:11px;color:#64748b;font-weight:600'>{count} · {pct}%</span></div>",
                unsafe_allow_html=True)

        st.divider()
        st.markdown("<div class='sb-label'>Export Report</div>", unsafe_allow_html=True)
        st.text_input("Patient name", placeholder="Anonymous", key="patient_name")
        st.text_input("Clinician name", placeholder="Dr.", key="doctor_name")
        if st.button("📥 Generate PDF Report", use_container_width=True, type="primary"):
            with st.spinner("Building report…"):
                try:
                    import subprocess
                    subprocess.run(["pip","install","reportlab","-q"], capture_output=True)
                    pdf_buffer = generate_pdf_report(
                        st.session_state.messages, st.session_state.emotions,
                        st.session_state.confidences, st.session_state.timestamps,
                        st.session_state.feedback)
                    if pdf_buffer:
                        fname = f"lumina_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                        st.download_button("⬇️ Download PDF", data=pdf_buffer,
                                           file_name=fname, mime="application/pdf",
                                           use_container_width=True)
                        st.success("Report ready!")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    else:
        st.markdown("""
        <div style='text-align:center;padding:28px 16px;color:#94a3b8;font-size:0.85rem;line-height:1.7'>
            <div style='font-size:2rem;margin-bottom:10px'>💬</div>
            Start chatting to see your emotion insights, journey graph, and timeline here
        </div>""", unsafe_allow_html=True)

    st.divider()
    if st.button("↺  New Conversation", use_container_width=True):
        for k in ['messages','emotions','confidences','timestamps']:
            st.session_state[k] = []
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
                st.markdown(
                    f"<span class='emo-badge' style='{style}'>{emoji} {emo.capitalize()} · {conf}%</span>"
                    f"<span class='ts'>{ts}</span>", unsafe_allow_html=True)
        else:
            c1, c2, c3 = st.columns([1,1,9])
            with c1:
                if st.button("👍", key=f"up_{i}", help="Helpful"):
                    st.session_state.feedback[i] = "up"
            with c2:
                if st.button("👎", key=f"dn_{i}", help="Not helpful"):
                    st.session_state.feedback[i] = "down"
            if i in st.session_state.feedback:
                st.caption("✅ Thanks!" if st.session_state.feedback[i]=="up" else "📝 Noted!")

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
        f"<span class='ts'>{ts}</span>", unsafe_allow_html=True)
    st.session_state.messages.append({'role':'user','content':prompt})

    if is_crisis(prompt):
        crisis_reply = """I'm really concerned about you right now. Please reach out immediately.\n\n🆘 iCall: 9152987821\n🆘 Vandrevala: 1860-2662-345 (24/7)\n🆘 AASRA: 9820466627\n🆘 National: 14416\n\nYou are not alone. 💙"""
        with st.chat_message('assistant'):
            st.markdown(f"<div class='crisis-box'>🚨 <strong>Crisis Support</strong><br><br>{crisis_reply}</div>", unsafe_allow_html=True)
        st.session_state.messages.append({'role':'assistant','content':crisis_reply})
        st.session_state.timestamps.append(ts)
    else:
        with st.chat_message('assistant'):
            reply = get_ai_response(st.session_state.messages, emotion, confidence, api_key, groq_key)
            if reply:
                st.write(reply)
                st.session_state.messages.append({'role':'assistant','content':reply})
                st.session_state.timestamps.append(ts)
    st.rerun()
