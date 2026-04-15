import streamlit as st

st.set_page_config(page_title="Lumina", layout="wide")

# Landing Page UI
st.title("🧠 Lumina")

st.write("Welcome to Lumina AI Emotion Chatbot")

if st.button("Start Chat"):
    st.switch_page("pages/Chat.py")