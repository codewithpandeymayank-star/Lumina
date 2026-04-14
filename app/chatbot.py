import streamlit as st

st.set_page_config(page_title="Lumina", layout="wide")

st.title("Lumina 🧠")

st.write("Welcome to your AI mental health assistant")

if st.button("Start Chat 🚀"):
    st.switch_page("Chat")