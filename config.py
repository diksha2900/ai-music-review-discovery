"""Shared config for local (.env) and Streamlit Cloud (secrets)."""

import os

from dotenv import load_dotenv

load_dotenv()


def get_groq_api_key():
    key = os.getenv("GROQ_API_KEY")
    if key:
        return key
    try:
        import streamlit as st
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return None
