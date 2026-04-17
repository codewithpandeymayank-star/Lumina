import streamlit as st

st.set_page_config(page_title="Lumina", layout="wide")

# Landing Page UI
st.title("🧠 Lumina")

st.write("Welcome to Lumina AI Emotion Chatbot")


st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

    *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

  html, body, .stApp {
    font-family: 'DM Sans', sans-serif;
    background: #080b12;
    color: #E6EAF2;   /* brighter text */
}
            html, body, .stApp {
    font-family: 'DM Sans', sans-serif;
    background: #080b12;
    color: #E6EAF2;
}

/* 🔥 ADD THIS RIGHT HERE */
.main, .block-container {
    max-width: 100% !important;
    padding-left: 3rem !important;
    padding-right: 3rem !important;
}

.page {
    max-width: 1200px !important;
    # display: flex;
    # align-items: center;
    # justify-content: center;

}
            p, span, div {
    color: #E6EAF2 !important;
    font-size: 16px;
}

            p, span, div {
    color: #E6EAF2 !important;
    font-size: 16px;
}

/* 🔥 ADD THIS HERE */
section[data-testid="stSidebarNav"] > div:first-child {
    display: none !important;
}
small {
    color: #B8C1D1 !important;
    font-size: 14px;
}

    div[data-testid="stSidebar"] { display: none !important; }
    #MainMenu, header, footer { visibility: hidden; }
    .block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
}
    .stButton > button { all: unset; cursor: pointer; }

    /* ── Canvas ── */
    .canvas {
        position: fixed; inset: 0; z-index: 0; pointer-events: none;
        overflow: hidden;
    }
    .orb {
        position: absolute; border-radius: 50%;
        filter: blur(80px); opacity: 0.18;
        animation: drift 18s ease-in-out infinite alternate;
    }
    .orb-1 { width: 700px; height: 700px; background: radial-gradient(circle, #0ea5e9, transparent 70%); top: -200px; left: -200px; animation-duration: 22s; }
    .orb-2 { width: 500px; height: 500px; background: radial-gradient(circle, #6366f1, transparent 70%); bottom: -150px; right: -100px; animation-duration: 18s; animation-delay: -9s; }
    .orb-3 { width: 400px; height: 400px; background: radial-gradient(circle, #14b8a6, transparent 70%); top: 40%; left: 40%; animation-duration: 26s; animation-delay: -13s; opacity: 0.1; }
    @keyframes drift { 0% { transform: translate(0,0) scale(1); } 100% { transform: translate(60px,40px) scale(1.1); } }

    /* Grain overlay */
    .canvas::after {
        content: '';
        position: fixed; inset: 0;
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
        opacity: 0.4; pointer-events: none;
    }

    /* ── Layout ── */
    .page { position: relative; z-index: 1; max-width: 1120px; margin: 0 auto; padding: 0 32px; }

    /* ── Nav ── */
    .nav {
        display: flex; justify-content: space-between; align-items: center;
        padding: 24px 48px;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        background: rgba(8,11,18,0.7);
        backdrop-filter: blur(16px);
        position: sticky; top: 0; z-index: 100;
    }
    .nav-brand {
        font-family: 'Sora', sans-serif;
        font-weight: 700; font-size: 1.15rem;
        color: #fff; letter-spacing: -0.3px;
        display: flex; align-items: center; gap: 10px;
    }
    .nav-dot {
        width: 8px; height: 8px; border-radius: 50%;
        background: #0ea5e9;
        box-shadow: 0 0 10px #0ea5e9;
        animation: pulse-dot 2.5s ease-in-out infinite;
    }
    @keyframes pulse-dot {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(0.7); }
    }
    .nav-links { display: flex; gap: 36px; }
    .nav-link { font-size: 0.85rem; color: #a0aec0; font-weight: 400; letter-spacing: 0.2px; }

    /* ── Hero ── */
    .hero {
        text-align: center;
        padding: 120px 24px 96px;
        animation: fadeUp 0.9s ease both;
    }
    @keyframes fadeUp { from { opacity: 0; transform: translateY(24px); } to { opacity: 1; transform: translateY(0); } }

    .eyebrow {
        display: inline-flex; align-items: center; gap: 8px;
        background: rgba(14,165,233,0.08);
        border: 1px solid rgba(14,165,233,0.2);
        color: #38bdf8; padding: 6px 18px;
        border-radius: 100px; font-size: 11px;
        font-weight: 600; letter-spacing: 1.5px;
        text-transform: uppercase; margin-bottom: 36px;
    }
    .eyebrow-dot { width: 5px; height: 5px; border-radius: 50%; background: #38bdf8; animation: pulse-dot 2s infinite; }

    .hero-h1 {
        font-family: 'Sora', sans-serif;
        font-size: clamp(2.8rem, 6vw, 5rem);
        font-weight: 800; color: #ffffff;
        line-height: 1.08; letter-spacing: -2.5px;
        margin-bottom: -10px;
        align-items: center; display: flex; justify-content: center;
    }
    .hero-h1 .accent {
        background: linear-gradient(120deg, #38bdf8 10%, #818cf8 50%, #a78bfa 90%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
        align-self: center;
    }
            
    .hero-h2 {
        font-family: 'Sora', sans-serif;
        font-size: clamp(1.5rem, 6vw, 3rem);
        font-weight: 800; color: #ffffff;
        line-height: 1.08; letter-spacing: -2.5px;
        padding: 0 4px;
        margin-bottom: 28px;
        align-items: center; display: flex; justify-content: center;
    }

    .hero-h2 .accent {
        background: linear-gradient(120deg, #38bdf8 10%, #818cf8 50%, #a78bfa 90%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: 0.5px;
        padding: 2px 2px;
        line-height: 2;
        align-self: center;
    }

    .hero-p {
    font-size: 1.15rem;
    color: #a0aec0;
    line-height: 1.9;
    max-width: 800px;   /* 🔥 FIXED */
    margin: 0 auto 52px;
    font-weight: 300;
}

    /* ── CTA button ── */
    .cta-wrap { display: flex; gap: 14px; justify-content: center; align-items: center; margin-bottom: 96px; }

    .btn-cta {
        display: inline-flex; align-items: center; gap: 8px;
        background: linear-gradient(135deg, #0ea5e9, #6366f1);
        color: #fff; padding: 15px 36px;
        border-radius: 14px; font-family: 'Sora', sans-serif;
        font-weight: 600; font-size: 0.92rem;
        box-shadow: 0 0 40px rgba(14,165,233,0.3), 0 4px 16px rgba(0,0,0,0.4);
        transition: transform 0.2s, box-shadow 0.2s;
        text-decoration: none; letter-spacing: -0.2px;
    }
    .btn-cta:hover { transform: translateY(-2px); box-shadow: 0 0 60px rgba(14,165,233,0.5), 0 8px 24px rgba(0,0,0,0.5); }

    .btn-ghost {
        display: inline-flex; align-items: center; gap: 8px;
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.09);
        color: #6b7a8d; padding: 15px 28px;
        border-radius: 14px; font-size: 0.88rem; font-weight: 500;
        transition: all 0.2s; text-decoration: none;
    }
    .btn-ghost:hover { background: rgba(255,255,255,0.07); color: #9ca3af; }

    /* ── Stats ── */
    .stats {
        display: grid; grid-template-columns: repeat(4, 1fr);
        max-width: 760px; margin: 0 auto 110px;
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 22px;
        background: rgba(255,255,255,0.02);
        backdrop-filter: blur(12px);
        overflow: hidden;
    }
    .stat { padding: 32px 20px; text-align: center; border-right: 1px solid rgba(255,255,255,0.05); }
    .stat:last-child { border-right: none; }
    .stat-n {
        font-family: 'Sora', sans-serif;
        font-size: 2rem; font-weight: 800;
        background: linear-gradient(120deg, #38bdf8, #818cf8);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; letter-spacing: -1px;
    }
    .stat-l { font-size: 0.72rem; color: #6b7280; margin-top: 5px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.8px; }

    /* ── Section ── */
    .section { padding: 90px 0; }
    .sec-tag { text-align: center; font-size: 10px; font-weight: 700; color: #0ea5e9; letter-spacing: 2.5px; text-transform: uppercase; margin-bottom: 14px; }
    .sec-h { font-family: 'Sora', sans-serif; text-align: center; font-size: clamp(1.7rem, 3.5vw, 2.5rem); font-weight: 800; color: #ffffff; letter-spacing: -1px; margin-bottom: 14px; }
    .sec-p { text-align: center; color: #3d4d5c; font-size: 0.95rem; max-width: 460px; margin: 0 auto 60px; line-height: 1.8; font-weight: 300; }

    /* ── Feature cards ── */
    .feat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
    .feat-card {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 22px; padding: 32px 28px;
        position: relative; overflow: hidden;
        transition: border-color 0.3s, transform 0.3s;
    }
    .feat-card::after {
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
        background: linear-gradient(90deg, transparent, rgba(14,165,233,0.4), transparent);
        opacity: 0; transition: opacity 0.3s;
    }
    .feat-card:hover { border-color: rgba(14,165,233,0.2); transform: translateY(-3px); }
    .feat-card:hover::after { opacity: 1; }
    .feat-icon {
        width: 46px; height: 46px; border-radius: 13px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.3rem; margin-bottom: 18px;
    }
    .feat-h { font-family: 'Sora', sans-serif; font-size: 0.92rem; font-weight: 700; color: #d0daf0; margin-bottom: 10px; letter-spacing: -0.2px; }
    .feat-p { font-size: 0.8rem; color: #6b7280; line-height: 1.75; font-weight: 300; }

    /* ── Steps ── */
    .steps-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
    .step-card {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 20px; padding: 32px 22px; text-align: center;
    }
    .step-n {
        width: 32px; height: 32px; border-radius: 10px;
        background: linear-gradient(135deg, #0ea5e9, #6366f1);
        display: flex; align-items: center; justify-content: center;
        font-family: 'Sora', sans-serif; font-size: 12px; font-weight: 700; color: #fff;
        margin: 0 auto 18px;
    }
    .step-icon { font-size: 1.7rem; margin-bottom: 14px; }
    .step-h { font-family: 'Sora', sans-serif; font-size: 0.88rem; font-weight: 700; color: #c8d0e0; margin-bottom: 8px; }
    .step-p { font-size: 0.78rem; color: #6b7280; line-height: 1.7; font-weight: 300; }

    /* ── CTA box ── */
    .cta-section { padding: 90px 0; text-align: center; }
    .cta-box {
        background: linear-gradient(135deg, rgba(14,165,233,0.07), rgba(99,102,241,0.07), rgba(167,139,250,0.04));
        border: 1px solid rgba(14,165,233,0.15);
        border-radius: 28px; padding: 72px 48px;
        max-width: 680px; margin: 0 auto; position: relative; overflow: hidden;
    }
    .cta-box::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
        background: linear-gradient(90deg, transparent, rgba(14,165,233,0.6), rgba(99,102,241,0.6), transparent);
    }
    .cta-h { font-family: 'Sora', sans-serif; font-size: clamp(1.8rem, 3.5vw, 2.6rem); font-weight: 800; color: #ffffff; letter-spacing: -1.5px; margin-bottom: 18px; }
    .cta-p { color: #3d4d5c; font-size: 0.95rem; line-height: 1.8; margin-bottom: 40px; font-weight: 300; }

    /* ── Footer ── */
    .footer {
        border-top: 1px solid rgba(255,255,255,0.04);
        padding: 40px 48px;
        display: flex; justify-content: space-between; align-items: center;
    }
    .footer-brand { font-family: 'Sora', sans-serif; font-size: 0.95rem; font-weight: 700; color: #c8d0e0; display: flex; align-items: center; gap: 8px; }
    .footer-links { display: flex; gap: 28px; }
    .footer-link { color: #6b7280; font-size: 0.8rem; }
    .footer-copy { color: #1e2733; font-size: 0.78rem; }
    .disc {
        text-align: center; color: #1a2230; font-size: 0.72rem;
        padding: 14px 48px; border-top: 1px solid rgba(255,255,255,0.02);
    }
</style>

<div class="canvas">
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="orb orb-3"></div>
</div>

<!-- Nav -->
<div class="nav">
    <div class="nav-brand">
        <div class="nav-dot"></div>
        Lumina
    </div>
    <div class="nav-links">
        <span class="nav-link">Features</span>
        <span class="nav-link">How it works</span>
        <span class="nav-link">For Clinicians</span>
    </div>
</div>

<!-- Hero -->
<div class="page">
<div class="hero">
    <div class="eyebrow"><div class="eyebrow-dot"></div> Emotion-Aware AI</div>
    <h1 class="hero-h1">
    Your mind 
    </h1>
    <h2 class="hero-h2">        
        <span class="accent"> deserves to be understood</span>
    </h2>
    <p class="hero-p">
        Lumina listens deeply, reads your emotional state in real-time,
        and responds with genuine human empathy — powered by AI trained
        on 61,000+ emotional conversations.
    </p>
</div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1.6, 1.2, 1.6])
with col2:
    if st.button("✦  Start Chatting — It's Free", use_container_width=True, type="primary"):
        st.switch_page("pages/Chat.py")

st.markdown("""
<!-- Stats -->
<div class="page">
<div class="stats">
    <div class="stat"><div class="stat-n">92.4%</div><div class="stat-l">Accuracy</div></div>
    <div class="stat"><div class="stat-n">8</div><div class="stat-l">Emotions</div></div>
    <div class="stat"><div class="stat-n">61K+</div><div class="stat-l">Trained On</div></div>
    <div class="stat"><div class="stat-n">24/7</div><div class="stat-l">Available</div></div>
</div>

<!-- Features -->
<div class="section">
    <div class="sec-tag">Capabilities</div>
    <div class="sec-h">Everything you need to feel heard</div>
    <div class="sec-p">Built with clinical-grade AI to support your mental wellness — every single day.</div>
    <div class="feat-grid">
        <div class="feat-card">
            <div class="feat-icon" style="background:rgba(14,165,233,0.1)">🎭</div>
            <div class="feat-h">Real-Time Emotion Detection</div>
            <div class="feat-p">8 emotions identified instantly using fine-tuned DistilBERT — trained on 61,000+ sentences at 92.4% accuracy.</div>
        </div>
        <div class="feat-card">
            <div class="feat-icon" style="background:rgba(99,102,241,0.1)">💬</div>
            <div class="feat-h">Empathetic AI Responses</div>
            <div class="feat-p">Groq LLaMA 3.1 with Gemini 2.0 Flash fallback — responses feel warm, natural, and deeply personal.</div>
        </div>
        <div class="feat-card">
            <div class="feat-icon" style="background:rgba(239,68,68,0.1)">🚨</div>
            <div class="feat-h">Crisis Detection</div>
            <div class="feat-p">Automatically detects distress signals and immediately surfaces emergency helplines with care.</div>
        </div>
        <div class="feat-card">
            <div class="feat-icon" style="background:rgba(20,184,166,0.1)">📊</div>
            <div class="feat-h">Emotion Analytics</div>
            <div class="feat-p">A visual timeline tracks your emotional journey — dominant moods, patterns, and session insights.</div>
        </div>
        <div class="feat-card">
            <div class="feat-icon" style="background:rgba(245,158,11,0.1)">📄</div>
            <div class="feat-h">Clinical PDF Reports</div>
            <div class="feat-p">Export professional mental health reports with risk assessment, ready to share with your therapist.</div>
        </div>
        <div class="feat-card">
            <div class="feat-icon" style="background:rgba(167,139,250,0.1)">🔒</div>
            <div class="feat-h">Completely Private</div>
            <div class="feat-p">Zero data storage. Your conversations exist only in your session — never stored, never shared.</div>
        </div>
    </div>
</div>

<!-- How it works -->
<div class="section" style="padding-top:0">
    <div class="sec-tag">Process</div>
    <div class="sec-h">How Lumina works</div>
    <div class="sec-p">From your words to emotional clarity — in seconds.</div>
    <div class="steps-grid">
        <div class="step-card">
            <div class="step-n">1</div>
            <div class="step-icon">💬</div>
            <div class="step-h">Share</div>
            <div class="step-p">Type how you're feeling in your own words, naturally and freely</div>
        </div>
        <div class="step-card">
            <div class="step-n">2</div>
            <div class="step-icon">🧠</div>
            <div class="step-h">Detect</div>
            <div class="step-p">AI identifies your emotion with 92.4% accuracy in milliseconds</div>
        </div>
        <div class="step-card">
            <div class="step-n">3</div>
            <div class="step-icon">💙</div>
            <div class="step-h">Respond</div>
            <div class="step-p">Receive a warm, personalized, empathetic reply crafted just for you</div>
        </div>
        <div class="step-card">
            <div class="step-n">4</div>
            <div class="step-icon">📄</div>
            <div class="step-h">Report</div>
            <div class="step-p">Export a clinical-grade session report for your doctor or therapist</div>
        </div>
    </div>
</div>
</div>

<!-- CTA -->
<div class="cta-section">
<div class="page">
<div class="cta-box">
    <div class="cta-h">Ready to feel understood?</div>
    <div class="cta-p">Join thousands of people using Lumina to understand and manage their emotions — one conversation at a time.</div>
</div>
</div>
</div>

<!-- Footer -->
<div class="footer">
    <div class="footer-brand"><div class="nav-dot"></div> Lumina</div>
    <div class="footer-links">
        <span class="footer-link">Privacy</span>
        <span class="footer-link">Terms</span>
        <span class="footer-link">Contact</span>
        <span class="footer-link">GitHub</span>
    </div>
    <div class="footer-copy">© 2026 Lumina</div>
</div>
<div class="disc">⚠ Lumina is not a substitute for professional mental health care. In crisis, please contact a qualified professional.</div>
""", unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)