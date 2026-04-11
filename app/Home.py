import streamlit as st

st.set_page_config(
    page_title="EmotiBot — AI Mental Health Companion",
    page_icon="🧠",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    * { font-family: 'Inter', sans-serif; margin: 0; padding: 0; box-sizing: border-box; }
    
    .stApp {
        background: #050508;
        overflow-x: hidden;
    }
    
    div[data-testid="stSidebar"] { display: none !important; }
    #MainMenu { visibility: hidden; }
    header { visibility: hidden; }
    footer { visibility: hidden; }
    .block-container { padding: 0 !important; max-width: 100% !important; }

    .page-wrap {
        max-width: 1100px;
        margin: 0 auto;
        padding: 0 24px;
        position: relative;
    }

    /* Background orbs */
    .bg-orb-1 {
        position: fixed;
        top: -200px;
        left: -200px;
        width: 600px;
        height: 600px;
        background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%);
        pointer-events: none;
        z-index: 0;
    }
    .bg-orb-2 {
        position: fixed;
        bottom: -200px;
        right: -200px;
        width: 600px;
        height: 600px;
        background: radial-gradient(circle, rgba(236,72,153,0.1) 0%, transparent 70%);
        pointer-events: none;
        z-index: 0;
    }
    .bg-orb-3 {
        position: fixed;
        top: 40%;
        left: 50%;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(139,92,246,0.08) 0%, transparent 70%);
        pointer-events: none;
        z-index: 0;
    }

    /* Nav */
    .nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 48px;
        border-bottom: 1px solid rgba(255,255,255,0.06);
        backdrop-filter: blur(10px);
        position: sticky;
        top: 0;
        z-index: 100;
        background: rgba(5,5,8,0.8);
    }
    .nav-logo {
        font-size: 1.2rem;
        font-weight: 700;
        color: #ffffff;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .nav-links {
        display: flex;
        gap: 32px;
        align-items: center;
    }
    .nav-link {
        color: #6b7280;
        font-size: 0.9rem;
        text-decoration: none;
        font-weight: 500;
    }

    /* Hero */
    .hero {
        text-align: center;
        padding: 100px 24px 80px 24px;
        position: relative;
        z-index: 1;
    }
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(99,102,241,0.1);
        border: 1px solid rgba(99,102,241,0.3);
        color: #a5b4fc;
        padding: 6px 16px;
        border-radius: 100px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-bottom: 28px;
    }
    .hero-title {
        font-size: 4rem;
        font-weight: 900;
        color: #ffffff;
        line-height: 1.1;
        margin-bottom: 24px;
        letter-spacing: -2px;
    }
    .hero-title .grad {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .hero-sub {
        font-size: 1.1rem;
        color: #6b7280;
        max-width: 520px;
        margin: 0 auto 48px auto;
        line-height: 1.8;
        font-weight: 400;
    }
    .hero-buttons {
        display: flex;
        gap: 12px;
        justify-content: center;
        align-items: center;
        margin-bottom: 80px;
    }
    .btn-primary {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white;
        padding: 14px 32px;
        border-radius: 12px;
        font-size: 0.95rem;
        font-weight: 600;
        border: none;
        cursor: pointer;
        box-shadow: 0 0 30px rgba(99,102,241,0.4);
    }
    .btn-secondary {
        background: rgba(255,255,255,0.05);
        color: #9ca3af;
        padding: 14px 32px;
        border-radius: 12px;
        font-size: 0.95rem;
        font-weight: 600;
        border: 1px solid rgba(255,255,255,0.1);
        cursor: pointer;
    }

    /* Stats */
    .stats {
        display: flex;
        justify-content: center;
        gap: 0;
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 20px;
        background: rgba(255,255,255,0.02);
        backdrop-filter: blur(10px);
        overflow: hidden;
        max-width: 700px;
        margin: 0 auto 100px auto;
    }
    .stat {
        flex: 1;
        padding: 28px 20px;
        text-align: center;
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    .stat:last-child { border-right: none; }
    .stat-num {
        font-size: 1.8rem;
        font-weight: 800;
        color: #ffffff;
        background: linear-gradient(135deg, #6366f1, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stat-lbl {
        font-size: 0.78rem;
        color: #4b5563;
        margin-top: 4px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Section */
    .section {
        padding: 80px 24px;
        position: relative;
        z-index: 1;
    }
    .section-label {
        text-align: center;
        font-size: 11px;
        font-weight: 700;
        color: #6366f1;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 12px;
    }
    .section-title {
        text-align: center;
        font-size: 2.2rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -1px;
        margin-bottom: 12px;
    }
    .section-sub {
        text-align: center;
        color: #6b7280;
        font-size: 1rem;
        margin-bottom: 56px;
        max-width: 500px;
        margin-left: auto;
        margin-right: auto;
    }

    /* Feature grid */
    .feat-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
        max-width: 960px;
        margin: 0 auto;
    }
    .feat-card {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 20px;
        padding: 28px;
        transition: all 0.3s;
        position: relative;
        overflow: hidden;
    }
    .feat-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(99,102,241,0.5), transparent);
    }
    .feat-icon-wrap {
        width: 44px;
        height: 44px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.3rem;
        margin-bottom: 16px;
    }
    .feat-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 8px;
    }
    .feat-desc {
        font-size: 0.82rem;
        color: #4b5563;
        line-height: 1.7;
    }

    /* Steps */
    .steps-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        max-width: 960px;
        margin: 0 auto;
        position: relative;
    }
    .step-card {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 20px;
        padding: 28px 20px;
        text-align: center;
        position: relative;
    }
    .step-num {
        width: 28px;
        height: 28px;
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: 700;
        color: white;
        margin: 0 auto 16px auto;
    }
    .step-icon { font-size: 1.6rem; margin-bottom: 12px; }
    .step-text {
        font-size: 0.82rem;
        color: #6b7280;
        line-height: 1.6;
    }

    /* CTA */
    .cta-section {
        text-align: center;
        padding: 80px 24px;
        position: relative;
        z-index: 1;
    }
    .cta-box {
        background: linear-gradient(135deg, rgba(99,102,241,0.1), rgba(139,92,246,0.1), rgba(236,72,153,0.05));
        border: 1px solid rgba(99,102,241,0.2);
        border-radius: 28px;
        padding: 64px 40px;
        max-width: 700px;
        margin: 0 auto;
        position: relative;
        overflow: hidden;
    }
    .cta-box::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(99,102,241,0.8), rgba(236,72,153,0.8), transparent);
    }
    .cta-title {
        font-size: 2.4rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -1px;
        margin-bottom: 16px;
    }
    .cta-sub {
        color: #6b7280;
        font-size: 1rem;
        margin-bottom: 36px;
        line-height: 1.7;
    }

    /* Footer */
    .footer {
        border-top: 1px solid rgba(255,255,255,0.06);
        padding: 40px 48px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        position: relative;
        z-index: 1;
    }
    .footer-logo {
        font-size: 1rem;
        font-weight: 700;
        color: #ffffff;
    }
    .footer-links {
        display: flex;
        gap: 24px;
    }
    .footer-link {
        color: #4b5563;
        font-size: 0.82rem;
        text-decoration: none;
    }
    .footer-copy {
        color: #374151;
        font-size: 0.82rem;
    }
    .disclaimer {
        text-align: center;
        color: #1f2937;
        font-size: 0.75rem;
        padding: 16px 48px;
        border-top: 1px solid rgba(255,255,255,0.03);
    }
</style>

<!-- Background orbs -->
<div class="bg-orb-1"></div>
<div class="bg-orb-2"></div>
<div class="bg-orb-3"></div>

<!-- Nav -->
<div class="nav">
    <div class="nav-logo">🧠 EmotiBot</div>
    <div class="nav-links">
        <span class="nav-link">Features</span>
        <span class="nav-link">How it works</span>
        <span class="nav-link">For Doctors</span>
    </div>
</div>

<!-- Hero -->
<div class="hero">
    <div class="badge">✦ AI Mental Health Companion</div>
    <div class="hero-title">
        Your emotions deserve<br>
        <span class="grad">to be understood</span>
    </div>
    <div class="hero-sub">
        EmotiBot listens, understands, and responds with genuine empathy. 
        Powered by advanced AI trained on 61,000+ emotional conversations.
    </div>
</div>
""", unsafe_allow_html=True)

# CTA Buttons
col1, col2, col3 = st.columns([1.5, 1, 1.5])
with col2:
    if st.button("✦ Start Chatting Free", use_container_width=True, type="primary"):
        st.switch_page("pages/Chat.py")

st.markdown("""
<!-- Stats -->
<div class="page-wrap">
<div class="stats">
    <div class="stat">
        <div class="stat-num">92.4%</div>
        <div class="stat-lbl">Accuracy</div>
    </div>
    <div class="stat">
        <div class="stat-num">8</div>
        <div class="stat-lbl">Emotions</div>
    </div>
    <div class="stat">
        <div class="stat-num">61K+</div>
        <div class="stat-lbl">Training Data</div>
    </div>
    <div class="stat">
        <div class="stat-num">24/7</div>
        <div class="stat-lbl">Available</div>
    </div>
</div>
</div>

<!-- Features -->
<div class="section">
<div class="page-wrap">
    <div class="section-label">Features</div>
    <div class="section-title">Everything you need to feel heard</div>
    <div class="section-sub">Built with cutting-edge AI to support your mental wellness journey.</div>
    <div class="feat-grid">
        <div class="feat-card">
            <div class="feat-icon-wrap" style="background:rgba(99,102,241,0.15)">🎭</div>
            <div class="feat-title">Real-Time Emotion Detection</div>
            <div class="feat-desc">Detects 8 emotions instantly using fine-tuned DistilBERT trained on 61,000+ sentences with 92.4% accuracy.</div>
        </div>
        <div class="feat-card">
            <div class="feat-icon-wrap" style="background:rgba(139,92,246,0.15)">💬</div>
            <div class="feat-title">Empathetic AI Responses</div>
            <div class="feat-desc">Powered by Gemini 2.5 Flash with real-time streaming — responses feel natural and deeply human.</div>
        </div>
        <div class="feat-card">
            <div class="feat-icon-wrap" style="background:rgba(239,68,68,0.15)">🚨</div>
            <div class="feat-title">Crisis Detection</div>
            <div class="feat-desc">Automatically detects distress signals and immediately connects users with emergency helplines.</div>
        </div>
        <div class="feat-card">
            <div class="feat-icon-wrap" style="background:rgba(16,185,129,0.15)">📊</div>
            <div class="feat-title">Emotion Analytics</div>
            <div class="feat-desc">Visual timeline tracking your emotional journey with insights on dominant moods and patterns.</div>
        </div>
        <div class="feat-card">
            <div class="feat-icon-wrap" style="background:rgba(245,158,11,0.15)">📄</div>
            <div class="feat-title">Clinical PDF Reports</div>
            <div class="feat-desc">Export professional mental health reports with risk assessment for doctors and therapists.</div>
        </div>
        <div class="feat-card">
            <div class="feat-icon-wrap" style="background:rgba(99,102,241,0.15)">🔒</div>
            <div class="feat-title">Private & Secure</div>
            <div class="feat-desc">Zero data storage. Your conversations are completely private and never shared with anyone.</div>
        </div>
    </div>
</div>
</div>

<!-- How it works -->
<div class="section" style="padding-top:0">
<div class="page-wrap">
    <div class="section-label">Process</div>
    <div class="section-title">How EmotiBot works</div>
    <div class="section-sub">Four simple steps to emotional clarity.</div>
    <div class="steps-grid">
        <div class="step-card">
            <div class="step-num">1</div>
            <div class="step-icon">💬</div>
            <div class="feat-title">Share</div>
            <div class="step-text">Type how you're feeling in your own words, naturally</div>
        </div>
        <div class="step-card">
            <div class="step-num">2</div>
            <div class="step-icon">🧠</div>
            <div class="feat-title">Detect</div>
            <div class="step-text">AI instantly identifies your emotion with 92.4% accuracy</div>
        </div>
        <div class="step-card">
            <div class="step-num">3</div>
            <div class="step-icon">💙</div>
            <div class="feat-title">Respond</div>
            <div class="step-text">Receive a warm, personalized empathetic response</div>
        </div>
        <div class="step-card">
            <div class="step-num">4</div>
            <div class="step-icon">📄</div>
            <div class="feat-title">Report</div>
            <div class="step-text">Export clinical report for your doctor when needed</div>
        </div>
    </div>
</div>
</div>

<!-- CTA -->
<div class="cta-section">
<div class="cta-box">
    <div class="cta-title">Ready to feel understood?</div>
    <div class="cta-sub">Join thousands of people using EmotiBot to understand and manage their emotions better every day.</div>
</div>
</div>

<!-- Footer -->
<div class="footer">
    <div class="footer-logo">🧠 EmotiBot</div>
    <div class="footer-links">
        <span class="footer-link">Privacy Policy</span>
        <span class="footer-link">Terms of Use</span>
        <span class="footer-link">Contact</span>
        <span class="footer-link">GitHub</span>
    </div>
    <div class="footer-copy">© 2026 EmotiBot. All rights reserved.</div>
</div>
<div class="disclaimer">
    ⚠️ EmotiBot is not a substitute for professional mental health care. If you are in crisis, please contact a qualified professional.
</div>
""", unsafe_allow_html=True)