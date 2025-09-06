# src/flowchart.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from .config import Config
import streamlit as st
import streamlit.components.v1 as components
import os

def generate_mermaid_flowchart(process_description: str) -> str:
    """Generate Mermaid flowchart code using Gemini"""
    try:
        cfg = Config()
        
        # Use the model from config
        llm = ChatGoogleGenerativeAI(
            model=cfg.CHAT_MODEL,  # Get from your config
            google_api_key=cfg.GEMINI_API_KEY,
            temperature=0.3,
            transport="rest"
        )
        
        # Simple and direct prompt
        system_prompt = """You are an expert at creating Mermaid flowchart diagrams. 
You must respond with ONLY the Mermaid code - no explanations, no markdown formatting, no JSON, just the raw Mermaid syntax."""
        
        user_prompt = f"""Create a flowchart in Mermaid format for this process:

{process_description}

Requirements:
- Start with "flowchart TD" or "flowchart LR"
- Use clear node IDs (A, B, C, etc.) with descriptive labels in brackets
- Use arrows --> to show flow
- Use curly braces for decision nodes: C{{Decision?}}
- Use |label| for arrow labels when needed

Return ONLY the Mermaid code, nothing else."""

        # Create messages
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        # Get response directly
        response = llm.invoke(messages)
        
        # Clean up the response
        mermaid_code = response.content.strip()
        
        # Remove any markdown formatting if present
        if mermaid_code.startswith("```"):
            lines = mermaid_code.split('\n')
            # Remove first line if it's ```mermaid or ```
            if lines.strip().startswith("```"):
                lines = lines[1:]
            # Remove last line if it's ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            mermaid_code = '\n'.join(lines)
        
        return mermaid_code.strip()
        
    except Exception as e:
        raise Exception(f"Error generating Mermaid code: {str(e)}")

def render_mermaid_chart(mermaid_code: str):
    """Render Mermaid chart in Streamlit using HTML"""
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
        <script>
            mermaid.initialize({{
                startOnLoad: true,
                theme: 'default',
                securityLevel: 'loose',
                flowchart: {{
                    useMaxWidth: true,
                    htmlLabels: true,
                    curve: 'basis'
                }}
            }});
        </script>
        <style>
            .mermaid {{
                text-align: center;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="mermaid">
{mermaid_code}
        </div>
    </body>
    </html>
    """
    
    components.html(html_code, height=600, scrolling=True)

def troubleshoot_with_gemini(error_msg: str, original_description: str) -> str:
    """Use Gemini to help troubleshoot flowchart generation issues"""
    try:
        cfg = Config()
        llm = ChatGoogleGenerativeAI(
            model=cfg.CHAT_MODEL,
            google_api_key=cfg.GEMINI_API_KEY,
            temperature=0.7,
            transport="rest"
        )
        
        troubleshoot_prompt = f"""I'm having trouble generating a Mermaid flowchart. Here's the error and context:

Original Process Description: {original_description}

Error: {error_msg}

Please help by:
1. Suggesting what might be wrong
2. Providing a simple, working Mermaid flowchart example for the process
3. Give tips for better process descriptions

Respond in a helpful, conversational way."""

        messages = [
            SystemMessage(content="You are a helpful assistant that helps debug and improve Mermaid flowchart generation."),
            HumanMessage(content=troubleshoot_prompt)
        ]
        
        response = llm.invoke(messages)
        return response.content
        
    except Exception as e:
        return f"Troubleshooting also failed: {str(e)}"

def render_flowchart_ui():
    """Streamlit UI for Mermaid flowchart generation with troubleshooting"""
    st.header("Flowchart Generator")
    st.write("Describe a process or workflow, and I will generate an interactive Mermaid flowchart.")
    
    # Example processes
    with st.expander("See Example Process Descriptions"):
        st.markdown("""
        **Example 1 - Simple Process:**
        User logs into system, system validates credentials, if valid show dashboard, if invalid show error message.
        
        **Example 2 - Business Process:**
        Customer places order, system checks inventory, if available process payment, if payment successful send confirmation email and ship product, if payment fails notify customer.
        
        **Example 3 - Decision Tree:**
        Employee requests time off, manager reviews request, if approved update calendar and notify employee, if denied send rejection reason to employee.
        """)
    
    # Input area
    process_desc = st.text_area(
        "Process Description", 
        height=150, 
        placeholder="Describe your process step by step...",
        help="Be specific about steps, decisions, and outcomes for best results."
    )
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        generate_btn = st.button("Generate Flowchart", type="primary")
    
    with col2:
        troubleshoot_btn = st.button("🔧 Get Help", disabled=not process_desc.strip())
    
    # Generate flowchart
    if generate_btn:
        if not process_desc.strip():
            st.warning("Please enter a process description.")
            return
        
        with st.spinner("Generating flowchart..."):
            try:
                # Generate the Mermaid code
                flowchart_code = generate_mermaid_flowchart(process_desc)
                
                if flowchart_code:
                    st.success("Flowchart generated successfully!")
                    
                    # Display the rendered flowchart
                    st.subheader("Interactive Flowchart")
                    render_mermaid_chart(flowchart_code)
                    
                    # Show the code in an expander
                    with st.expander("View Mermaid Code"):
                        st.code(flowchart_code, language="text")
                        
                        # Download button
                        st.download_button(
                            label="Download Mermaid Code",
                            data=flowchart_code,
                            file_name="flowchart.mmd",
                            mime="text/plain"
                        )
                else:
                    st.error("Generated flowchart code was empty.")
                
            except Exception as e:
                error_msg = str(e)
                st.error(f"Error generating flowchart: {error_msg}")
                
                # Auto-troubleshoot
                st.info("Getting help from AI...")
                with st.spinner("Analyzing the issue..."):
                    try:
                        help_text = troubleshoot_with_gemini(error_msg, process_desc)
                        
                        st.subheader("AI Troubleshooting Help")
                        st.markdown(help_text)
                        
                    except Exception as help_error:
                        st.error(f"Troubleshooting failed: {str(help_error)}")
    
    # Manual troubleshooting
    if troubleshoot_btn:
        with st.spinner("Getting suggestions..."):
            try:
                help_text = troubleshoot_with_gemini("User requested help", process_desc)
                
                st.subheader("AI Suggestions")
                st.markdown(help_text)
                
            except Exception as e:
                st.error(f"Error getting help: {str(e)}")

