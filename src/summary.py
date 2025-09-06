
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

def generate_enhanced_summary(text: str, llm: Optional[ChatGoogleGenerativeAI] = None) -> dict:
    """Generate an enhanced summary with key points and insights using Gemini Pro"""
    cfg = Config()
    if llm is None:
        llm = ChatGoogleGenerativeAI(
            model=cfg.CHAT_MODEL_BEST,
            temperature=0.3,
            google_api_key=cfg.GEMINI_API_KEY,
            transport="rest"
        )
    
    if not text.strip():
        return {"summary": "Text is empty or unreadable.", "key_points": [], "insights": ""}
    
    prompt = f"""
    Analyze the following text and provide a comprehensive analysis:
    
    {text}
    
    Please provide:
    1. A concise summary in bullet points highlighting key facts, concepts, numbers, and decisions
    2. The 3 most important key points
    3. Any notable insights or takeaways
    
    Format your response as:
    
    SUMMARY:
    [bullet point summary here]
    
    KEY POINTS:
    1. [first key point]
    2. [second key point] 
    3. [third key point]
    
    INSIGHTS:
    [insights and takeaways here]
    """
    
    result = llm.invoke(prompt)
    response_content = result.content
    
    # Parse the response
    sections = {"summary": "", "key_points": [], "insights": ""}
    current_section = None
    
    lines = response_content.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('SUMMARY:'):
            current_section = 'summary'
            continue
        elif line.startswith('KEY POINTS:'):
            current_section = 'key_points'
            continue
        elif line.startswith('INSIGHTS:'):
            current_section = 'insights'
            continue
        
        if current_section == 'summary' and line:
            sections['summary'] += line + '\n'
        elif current_section == 'key_points' and line and (line.startswith('1.') or line.startswith('2.') or line.startswith('3.')):
            sections['key_points'].append(line)
        elif current_section == 'insights' and line:
            sections['insights'] += line + ' '
    
    # Fallback if parsing fails
    if not sections['summary']:
        sections['summary'] = response_content
    
    return sections

def summarize_text_file(path: str, llm: Optional[ChatGoogleGenerativeAI] = None) -> str:
    cfg = Config()
    if llm is None:
        llm = ChatGoogleGenerativeAI(
            model=cfg.CHAT_MODEL_BEST,
            temperature=0.3,
            google_api_key=cfg.GEMINI_API_KEY,
            transport="rest"
        )
    text = _read_text_utf8(path)
    if not text.strip():
        return "File is empty or unreadable."
    
    prompt = (
        "You are a helpful assistant. Read the text below and produce a concise summary "
        "according to the text given in bullet points. highlighting key facts, concepts, numbers, and decisions. "
        "Avoid fluff, keep it faithful to the source.\n\n"
        f"--- BEGIN TEXT ---\n{text}\n--- END TEXT ---"
    )
    result = llm.invoke(prompt)
    return getattr(result, "content", str(result))

def render_txt_summary_ui(url: str = "./texts"):
    """
    Streamlit UI for YouTube video summarization using Gemini Pro.
    """
    import streamlit as st
    import asyncio
    
    st.header("YouTube Video Summarizer")
    st.write("Enter a YouTube URL to get a comprehensive analysis of the video content using Gemini Pro.")
    
    # Main input
    youtube_url = st.text_input(
        "Enter YouTube URL:", 
        placeholder="https://www.youtube.com/watch?v=..."
    )
    
    # Processing options
    with st.expander("Analysis Options"):
        analysis_type = st.selectbox(
            "Analysis Type:",
            ["Standard Summary", "Enhanced Analysis"],
            help="Choose between a simple summary or detailed analysis with key points and insights"
        )
        
        save_transcript = st.checkbox(
            "Save transcript to file",
            value=False,
            help="Save the transcript as a text file for future reference"
        )
    
    if st.button("Analyze Video", type="primary"):
        if not youtube_url.strip():
            st.error("Please enter a YouTube URL")
            return
            
        try:
            with st.spinner("Getting transcript from video..."):
                # Handle async function
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                # Get transcript
                transcript_text = loop.run_until_complete(youtube_to_transcript(youtube_url))
                
                if not transcript_text or len(transcript_text.strip()) < 50:
                    st.error("Could not get a valid transcript from the video. The video might not have audio or may be unavailable.")
                    return
                
            with st.spinner("Analyzing content with Gemini Pro..."):
                if analysis_type == "Enhanced Analysis":
                    # Use enhanced analysis
                    analysis = generate_enhanced_summary(transcript_text)
                    
                    # Display enhanced results
                    st.success("Analysis completed successfully!")
                    
                    # Summary section
                    st.subheader("Summary")
                    if analysis['summary']:
                        st.markdown(analysis['summary'])
                    
                    # Key points section  
                    if analysis['key_points']:
                        st.subheader("Key Points")
                        for point in analysis['key_points']:
                            st.markdown(f"- {point}")
                    
                    # Insights section
                    if analysis['insights']:
                        st.subheader("Insights & Takeaways")
                        st.markdown(analysis['insights'])
                    
                else:
                    # Standard summary
                    temp_file = "temp_transcript.txt"
                    with open(temp_file, "w", encoding="utf-8") as f:
                        f.write(transcript_text)
                    
                    summary = summarize_text_file(temp_file)
                    os.remove(temp_file)
                    
                    st.success("Summary generated successfully!")
                    st.subheader("Summary")
                    st.markdown(summary)
            
            # Statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Transcript Words", len(transcript_text.split()))
            with col2:
                if analysis_type == "Enhanced Analysis":
                    summary_text = analysis.get('summary', '')
                else:
                    summary_text = summary
                st.metric("Summary Words", len(summary_text.split()))
            with col3:
                if len(transcript_text.split()) > 0:
                    compression = round((1 - len(summary_text.split())/len(transcript_text.split())) * 100, 1)
                    st.metric("Compression", f"{compression}%")
            
            # Save transcript if requested
            if save_transcript:
                try:
                    # Extract video ID for filename
                    if "watch?v=" in youtube_url:
                        video_id = youtube_url.split("watch?v=")[-1].split("&")[0]
                    elif "youtu.be/" in youtube_url:
                        video_id = youtube_url.split("youtu.be/")[-1].split("?")[0]
                    else:
                        video_id = "unknown"
                    
                    transcript_file = f"transcript_{video_id}.txt"
                    with open(transcript_file, "w", encoding="utf-8") as f:
                        f.write(transcript_text)
                    
                    st.success(f"Transcript saved as: {transcript_file}")
                    
                    # Download button
                    st.download_button(
                        label="Download Transcript",
                        data=transcript_text,
                        file_name=transcript_file,
                        mime="text/plain"
                    )
                    
                except Exception as save_error:
                    st.warning(f"Could not save transcript: {str(save_error)}")
            
            # Show transcript in expandable section
            with st.expander("View Full Transcript"):
                st.text_area("Transcript:", transcript_text, height=300, disabled=True)
                
                # Word count for transcript
                words = len(transcript_text.split())
                sentences = len([s for s in transcript_text.split('.') if s.strip()])
                st.caption(f"Transcript contains {words} words and approximately {sentences} sentences.")
                
        except Exception as e:
            st.error(f"Error processing video: {str(e)}")
            st.info("Please ensure the YouTube URL is valid and the video has audio content.")
            
            # Debug info
            with st.expander("Debug Information"):
                st.code(f"Error details: {str(e)}")
                st.write("Common issues:")
                st.write("- Video is private or restricted")
                st.write("- Video has no audio track") 
                st.write("- Network connectivity issues")
                st.write("- Invalid YouTube URL format")
