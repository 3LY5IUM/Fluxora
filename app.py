import streamlit as st
import os
import sys
from dotenv import load_dotenv
from pathlib import Path
# add the dir to python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Load .env into environment
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

from src.summary import render_txt_summary_ui
from src.mermaid import render_flowchart_ui
from src.localization import render_localization_ui
from src.quiz import render_quiz_ui
from src.creds import render_credits_ui


# Disable Streamlit's file watcher to avoid torch.classes inspection
os.environ["STREAMLIT_SERVER_ENABLE_FILE_WATCHER"] = "false"

def pdf_processing_tab():
    """Handle all PDF processing functionality"""
    st.header("PDF Document Analysis")
    st.markdown("Upload any PDF document and I will help you understand it and answer any and every query you may have regarding the document.")
    
    st.subheader("Upload PDF documents")
    uploaded_files = st.file_uploader(
            "Upload PDF documents",
            type="pdf",
            accept_multiple_files=True,
            help="this is where you are suppose to upload pdf files that you want to query."
            )
    process_docs = st.button("Process Document", type="primary")

    # process the uploaded documents.
    if process_docs and uploaded_files:
        with st.spinner("Processing the uploaded documents to extract all relavent data..."):
            try:
                all_elements = []
                for uploaded_file in uploaded_files:
                    st.info(f"Processing: {uploaded_file.name}")
                    # save uploaded file temporarily
                    safe_name = Path(uploaded_file.name).name
                    temp_path = f"temp_{safe_name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # process pdf
                    from src.pdf_processor import PDF_processor
                    from src.vectors import add_documents
                    elements = st.session_state.pdf_processor.process_pdf(temp_path)
                    all_elements.extend(elements)
                    # clean up temp file
                    os.remove(temp_path)
                
                add_documents(st.session_state.vector_store, all_elements)
                st.session_state.documents_processed = True
                st.success(f"Sucessfully analyzed {len(uploaded_files)} documents with {len(all_elements)} elements")
            except Exception as e:
                st.error(f"Error processing documents: {str(e)}")
    
    # chat interface.
    st.markdown("---")
    st.subheader("Which query may I assist you regarding this document")
    
    if not st.session_state.documents_processed:
        st.info("Please upload and process documents to start chatting.")
        return
    
    # Display chat history 
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # display chat message
    if prompt := st.chat_input("What queries do you have regarding this pdf Sir"):
        # add the user mssg.
        st.session_state.messages.append({"role": "user", "content": prompt})
        # display the user query.
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # st.chat_mssg is used for creating chating bubbles.
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                try:
                    from src.vectors import query
                    from src.chat import get_respo
                    
                    # Query the vector store directly
                    results = query(st.session_state.vector_store, prompt)
                
                    # Process results into expected format
                    processed_results = []
                    for doc in results:
                        processed_results.append({
                            "content": doc.page_content,
                            "metadata": doc.metadata
                        })
                    
                    response = get_respo(
                        prompt,
                        processed_results,
                        st.session_state.messages[:-1]
                    )
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    error_msg = f"Sorry sir but there is an error generating response: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

def main():
    st.set_page_config(
        page_title="Atlas",
        page_icon="",
        layout="wide"
    )
    
    # Handle API key setup
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        st.sidebar.warning("No Gemini API key found in .env.")
        api_key = st.sidebar.text_input(
            "Enter your Gemini API Key", type="password"
        )
        if api_key:
            # save the api key this time to the env file.
            with open(env_path, "a") as f:
                f.write(f"\nGEMINI_API_KEY={api_key}\n")
            os.environ["GEMINI_API_KEY"] = api_key
            st.sidebar.success("API key saved to .env")
        else:
            st.stop()
    
    os.environ["GEMINI_API_KEY"] = api_key

    # Handle API key setup (Deepgram)
    deepgram_api_key = os.getenv("DEEPGRAM_API_KEY", "").strip()
    if not deepgram_api_key:
        st.sidebar.warning("No Deepgram API key found in .env.")
        deepgram_api_key = st.sidebar.text_input("Enter your Deepgram API Key", type="password")
        if deepgram_api_key:
            with open(env_path, "a") as f:
                f.write(f"\nDEEPGRAM_API_KEY={deepgram_api_key}\n")
            os.environ["DEEPGRAM_API_KEY"] = deepgram_api_key  # export for current run
            st.sidebar.success("Deepgram API key saved to .env")
        else:
            st.stop()
    os.environ["DEEPGRAM_API_KEY"] = deepgram_api_key  # ensure set for this process
    
    # Initialize components in session state
    if "config" not in st.session_state:
        from src.config import Config
        st.session_state.config = Config()
    
    if "pdf_processor" not in st.session_state:
        from src.pdf_processor import PDF_processor
        st.session_state.pdf_processor = PDF_processor()
    
    if "vector_store" not in st.session_state:
        from src.vectors import setup_vs
        st.session_state.vector_store = setup_vs(api_key)
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "documents_processed" not in st.session_state:
        st.session_state.documents_processed = False
    
    # Main title
    st.title("Fluxora: Your Learning Wingman")
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Localizer","Interactive Quiz","PDF Analysis", "Youtube Summary", "Flowchart", "Credits"])
    
    with tab1:
         render_localization_ui()
    
    with tab2:
        render_quiz_ui()

    with tab3:
        pdf_processing_tab()

    with tab4:
        render_txt_summary_ui("./texts")

    with tab5:
        render_flowchart_ui()

    with tab6:
        render_credits_ui()

if __name__ == "__main__":
    main()
