# src/text_summarizer.py
from pathlib import Path
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from .config import Config
from .trans import youtube_to_transcript

import os

def _read_text_utf8(path: str) -> str:
    # Read robustly as UTF-8, ignoring bad bytes if any
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def _get_transcript_txt(url: str) -> str:
    return youtube_to_transcript(url)


def summarize_text_file(path: str, llm: Optional[ChatGoogleGenerativeAI] = None) -> str:

    cfg = Config()
    if llm is None:
        llm = ChatGoogleGenerativeAI(
            model=cfg.CHAT_MODEL_best,               # reuse your chat model
            temperature=1,
            google_api_key=cfg.GEMINI_API_KEY,  # reuse your API key
            transport="rest"                    # avoid gRPC event loop issues
        )

    text = _read_text_utf8(path)
    if not text.strip():
        return "File is empty or unreadable."

    prompt = (
        "You are a helpful assistant. Read the text below and produce a concise summary "
        "according to the text given in bullet points. highlighting key facts, concepts, numbers, and decisions."
        "Avoid fluff, keep it faithful to the source.\n\n"
        f"--- BEGIN TEXT ---\n{text}\n--- END TEXT ---"
    )
    result = llm.invoke(prompt)
    return getattr(result, "content", str(result))

def render_txt_summary_ui(url: str = "./texts"):
    """
    Render a simple Streamlit UI to pick a .txt and display the summary.
    Call this inside a tab/container in app.py.
    """
    import streamlit as st
    import asyncio

    youtube_url = st.text_input(
        "Enter YouTube URL:", 
        placeholder="https://www.youtube.com/watch?v=..."
    )

    if st.button("Get Transcript & Summarize"):
        if not youtube_url.strip():
            st.error("Please enter a YouTube URL")
            return
            
        try:
            with st.spinner("Getting transcript and generating summary..."):
                # Handle async function
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                # Get transcript
                transcript_text = loop.run_until_complete(youtube_to_transcript(youtube_url))
                
                # Create a temporary file to use with existing summarize_text_file function
                temp_file = "temp_transcript.txt"
                with open(temp_file, "w", encoding="utf-8") as f:
                    f.write(transcript_text)
                
                # Use existing summarize function
                summary = summarize_text_file(temp_file)
                
                # Clean up temp file
                os.remove(temp_file)
            
            st.subheader("Summary")
            st.markdown(summary)
            
            with st.expander("Show original transcript"):
                st.code(transcript_text)
                
        except Exception as e:
            st.error(f"Error processing video: {str(e)}")
