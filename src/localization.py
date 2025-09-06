# localization.py
import streamlit as st
import os
from pathlib import Path
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

def get_language_options():
    """Return comprehensive list of languages for localization"""
    languages = {
        # Indian Languages
        "Hindi": "Hindi (हिंदी) - India",
        "Bengali": "Bengali (বাংলা) - India/Bangladesh", 
        "Telugu": "Telugu (తెలుగు) - India",
        "Tamil": "Tamil (தமிழ்) - India/Sri Lanka",
        "Marathi": "Marathi (मराठी) - India",
        "Gujarati": "Gujarati (ગુજરાતી) - India",
        "Kannada": "Kannada (ಕನ್ನಡ) - India",
        "Malayalam": "Malayalam (മലയാളം) - India",
        "Punjabi": "Punjabi (ਪੰਜਾਬੀ) - India/Pakistan",
        "Urdu": "Urdu (اردو) - India/Pakistan",
        "Sanskrit": "Sanskrit (संस्कृम्) - India",
        "Odia": "Odia (ଓଡ଼ିଆ) - India",
        "Assamese": "Assamese (অসমীয়া) - India",
        "Nepali": "Nepali (नेपाली) - Nepal/India",
        
        # Major Global Languages
        "English": "English - Global",
        "Spanish": "Spanish (Español) - Spain/Latin America",
        "French": "French (Français) - France/Global",
        "German": "German (Deutsch) - Germany/Austria/Switzerland",
        "Italian": "Italian (Italiano) - Italy",
        "Portuguese": "Portuguese (Português) - Brazil/Portugal",
        "Russian": "Russian (Русский) - Russia/CIS",
        "Chinese": "Chinese (中文) - China/Taiwan/Singapore",
        "Japanese": "Japanese (日本語) - Japan",
        "Korean": "Korean (한국어) - South Korea",
        "Arabic": "Arabic (العربية) - Middle East/North Africa",
        "Turkish": "Turkish (Türkçe) - Turkey",
        "Persian": "Persian (فارسی) - Iran/Afghanistan",
        "Hebrew": "Hebrew (ברית) - Israel",
        "Dutch": "Dutch (Nederlands) - Netherlands/Belgium",
        "Swedish": "Swedish (Svenska) - Sweden",
        "Norwegian": "Norwegian (Norsk) - Norway",
        "Danish": "Danish (Dansk) - Denmark",
        "Finnish": "Finnish (Suomi) - Finland",
        "Polish": "Polish (Polski) - Poland",
        "Czech": "Czech (Čeština) - Czech Republic",
        "Hungarian": "Hungarian (Magyar) - Hungary",
        "Romanian": "Romanian (Română) - Romania",
        "Greek": "Greek (Ελληνικά) - Greece",
        
        # Southeast Asian Languages
        "Thai": "Thai (ไทย) - Thailand",
        "Vietnamese": "Vietnamese (Tiếng Việt) - Vietnam",
        "Indonesian": "Indonesian (Bahasa Indonesia) - Indonesia",
        "Malay": "Malay (Bahasa Melayu) - Malaysia/Singapore",
        "Filipino": "Filipino (Tagalog) - Philippines",
        
        # African Languages
        "Swahili": "Swahili (Kiswahili) - East Africa",
        "Amharic": "Amharic (አማርኛ) - Ethiopia",
        "Yoruba": "Yoruba - Nigeria/West Africa",
        "Zulu": "Zulu - South Africa",
        
        # Others
        "Welsh": "Welsh (Cymraeg) - Wales",
        "Irish": "Irish (Gaeilge) - Ireland",
        "Catalan": "Catalan (Català) - Catalonia/Spain",
        "Basque": "Basque (Euskera) - Basque Country",
        "Estonian": "Estonian (Eesti) - Estonia",
        "Latvian": "Latvian (Latviešu) - Latvia",
        "Lithuanian": "Lithuanian (Lietuvių) - Lithuania"
    }
    return languages

def get_cultural_context_options():
    """Return cultural/regional context options"""
    contexts = {
        "India - General": "Indian business practices, cultural norms, and regulatory environment",
        "India - North": "North Indian cultural context, Hindi business terminology",
        "India - South": "South Indian cultural context, regional business practices",
        "India - West": "Western Indian business hub context (Mumbai, Gujarat, Maharashtra)",
        "India - East": "Eastern Indian context (Bengal, Odisha business culture)",
        "USA - General": "American business culture, legal frameworks, market practices",
        "USA - Corporate": "Corporate America, Silicon Valley tech culture",
        "UK - General": "British business etiquette, regulatory environment",
        "Europe - EU": "European Union regulatory context, continental business practices",
        "China - Mainland": "Chinese business culture, regulatory environment",
        "Japan - Corporate": "Japanese business culture, formal protocols",
        "Southeast Asia": "ASEAN business context, multicultural considerations",
        "Middle East": "Middle Eastern business practices, cultural sensitivities",
        "Latin America": "Latin American business culture, regional variations",
        "Australia/NZ": "Australian/New Zealand business context",
        "Global/International": "International business context, cross-cultural neutral",
        "Academic/Research": "Academic and research institutional context",
        "Government/Public": "Government and public sector context",
        "Healthcare": "Healthcare industry specific context",
        "Financial Services": "Banking, finance, and investment context",
        "Technology": "Tech industry culture and practices",
        "Legal/Compliance": "Legal and regulatory compliance context"
    }
    return contexts

def detect_document_type(elements: List[Dict[str, Any]]) -> str:
    """Analyze document content to determine type for appropriate localization strategy"""
    
    # Combine all text content
    all_text = ""
    for element in elements:
        if element.get("content_type") in ["text", "table"]:
            all_text += " " + element.get("content", "")
        elif element.get("content_type") == "image":
            all_text += " " + element.get("image_desc", "")
    
    all_text = all_text.lower()
    
    # Keywords for different document types
    business_keywords = ["business", "market", "revenue", "profit", "sales", "customer", "strategy", "management", "company", "corporate", "finance", "investment", "contract", "agreement", "proposal"]
    
    legal_keywords = ["legal", "law", "regulation", "compliance", "contract", "agreement", "terms", "conditions", "liability", "jurisdiction", "court", "statute", "clause"]
    
    technical_keywords = ["technical", "specification", "algorithm", "system", "software", "hardware", "engineering", "protocol", "implementation", "architecture"]
    
    scientific_keywords = ["research", "study", "analysis", "method", "experiment", "data", "results", "conclusion", "hypothesis", "theory", "scientific", "academic"]
    
    medical_keywords = ["medical", "health", "patient", "treatment", "diagnosis", "clinical", "therapeutic", "pharmaceutical", "healthcare", "medicine"]
    
    educational_keywords = ["education", "learning", "student", "teacher", "curriculum", "academic", "school", "university", "course", "training"]
    
    # Count keyword matches
    business_count = sum(1 for word in business_keywords if word in all_text)
    legal_count = sum(1 for word in legal_keywords if word in all_text)
    technical_count = sum(1 for word in technical_keywords if word in all_text)
    scientific_count = sum(1 for word in scientific_keywords if word in all_text)
    medical_count = sum(1 for word in medical_keywords if word in all_text)
    educational_count = sum(1 for word in educational_keywords if word in all_text)
    
    # Determine document type based on highest count
    counts = {
        "business": business_count,
        "legal": legal_count,
        "technical": technical_count,
        "scientific": scientific_count,
        "medical": medical_count,
        "educational": educational_count
    }
    
    doc_type = max(counts, key=counts.get)
    return doc_type if counts[doc_type] > 2 else "general"

def generate_localized_summary(elements: List[Dict[str, Any]], target_language: str, cultural_context: str, model: ChatGoogleGenerativeAI) -> str:
    """Generate a culturally localized summary of the document"""
    
    # Combine all content
    full_content = ""
    for element in elements:
        if element.get("content_type") == "text":
            full_content += f"\n\nText Section:\n{element.get('content', '')}"
        elif element.get("content_type") == "table":
            full_content += f"\n\nTable:\n{element.get('content', '')}"
            if element.get("html_content"):
                full_content += f"\n(HTML: {element.get('html_content', '')})"
        elif element.get("content_type") == "image":
            full_content += f"\n\nImage Description:\n{element.get('image_desc', '')}"
    
    # Detect document type for appropriate localization strategy
    doc_type = detect_document_type(elements)
    
    # Create localization prompt based on document type
    localization_strategies = {
        "business": """
        Focus on:
        - Local business practices and etiquette
        - Market-specific terminology and concepts
        - Regional business culture nuances
        - Local regulatory and compliance considerations
        - Currency, units, and measurement adaptations
        - Cultural business relationship dynamics
        """,
        "legal": """
        Focus on:
        - Legal system differences and terminology
        - Regional regulatory frameworks
        - Cultural interpretations of legal concepts
        - Local compliance requirements
        - Jurisdiction-specific considerations
        - Note: Mention when local legal consultation is recommended
        """,
        "technical": """
        Focus on:
        - Technical terminology in target language
        - Regional technical standards and practices
        - Local technology adoption patterns
        - Cultural approach to technical implementation
        - Keep core technical concepts accurate
        """,
        "scientific": """
        Focus on:
        - Scientific terminology in target language
        - Regional research practices and standards
        - Cultural context for scientific concepts
        - Local academic and research frameworks
        - Maintain scientific accuracy above cultural adaptation
        """,
        "medical": """
        Focus on:
        - Medical terminology in target language
        - Regional healthcare systems and practices
        - Cultural health beliefs and approaches
        - Local medical regulations and standards
        - Emphasize consulting local medical professionals
        """,
        "educational": """
        Focus on:
        - Educational terminology and concepts
        - Regional educational systems and practices
        - Cultural learning approaches and preferences
        - Local academic standards and frameworks
        - Age-appropriate cultural considerations
        """,
        "general": """
        Focus on:
        - General cultural adaptation
        - Language-appropriate explanations
        - Regional context and relevance
        - Cultural sensitivity and appropriateness
        """
    }
    
    strategy = localization_strategies.get(doc_type, localization_strategies["general"])
    
    prompt = f"""
    You are an expert localization specialist. Please provide a comprehensive, culturally localized summary of this document.

    TARGET LANGUAGE: {target_language}
    CULTURAL CONTEXT: {cultural_context}
    DETECTED DOCUMENT TYPE: {doc_type.title()}

    LOCALIZATION STRATEGY:
    {strategy}

    DOCUMENT CONTENT:
    {full_content}

    Please provide:
    1. A comprehensive summary in {target_language}
    2. Cultural context and relevance for {cultural_context}
    3. Key points adapted for the target culture
    4. Any important cultural considerations or differences
    5. Practical implications for the target audience
    6. Regional variations or adaptations needed

    Make the summary detailed and culturally relevant while maintaining accuracy. If certain concepts don't translate well culturally, explain the differences and provide local equivalents or context.

    Write the entire response in {target_language} unless specifically explaining cultural differences that require comparison.
    """
    
    try:
        messages = [
            SystemMessage(f"You are an expert localization specialist fluent in {target_language} with deep knowledge of {cultural_context}. Provide culturally appropriate and linguistically accurate localization."),
            HumanMessage(prompt)
        ]
        
        response = model.invoke(messages)
        return response.content
        
    except Exception as e:
        return f"Error generating localized summary: {str(e)}"

def render_localization_ui():
    """Render the localization tab UI"""
    st.header("📍 Document Localization & Cultural Adaptation")
    st.markdown("Upload a PDF document and get a culturally localized summary in your target language and cultural context.")
    
    # Language and cultural context selection
    col1, col2 = st.columns(2)
    
    with col1:
        languages = get_language_options()
        selected_language = st.selectbox(
            "Select Target Language:",
            options=list(languages.keys()),
            format_func=lambda x: languages[x],
            index=0  # Default to Hindi
        )
    
    with col2:
        contexts = get_cultural_context_options()
        selected_context = st.selectbox(
            "Select Cultural/Regional Context:",
            options=list(contexts.keys()),
            format_func=lambda x: contexts[x],
            index=0  # Default to India - General
        )
    
    st.markdown("---")
    
    # PDF Upload section
    st.subheader("Upload PDF Document")
    uploaded_file = st.file_uploader(
        "Choose a PDF file for localization",
        type="pdf",
        help="Upload a PDF document that you want to localize and culturally adapt."
    )
    
    # Process button
    if uploaded_file:
        st.info(f"File selected: {uploaded_file.name}")
        
        process_localization = st.button("Generate Localized Summary", type="primary")
        
        if process_localization:
            with st.spinner(f"Processing document and generating localized summary in {selected_language}..."):
                try:
                    # Save uploaded file temporarily
                    safe_name = Path(uploaded_file.name).name
                    temp_path = f"temp_localization_{safe_name}"
                    
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Process PDF using existing pdf_processor
                    elements = st.session_state.pdf_processor.process_pdf(temp_path)
                    
                    # Store in vector database for potential future queries
                    from src.vectors import add_documents
                    add_documents(st.session_state.vector_store, elements)
                    
                    # Initialize model for localization (reuse config)
                    localization_model = ChatGoogleGenerativeAI(
                        model=st.session_state.config.VISION_MODEL,
                        api_key=st.session_state.config.GEMINI_API_KEY,
                        temperature=0.3,  # Lower temperature for more consistent localization
                        max_tokens=None,
                        timeout=None,
                        max_retries=2
                    )
                    
                    # Generate localized summary
                    localized_summary = generate_localized_summary(
                        elements, 
                        selected_language, 
                        selected_context, 
                        localization_model
                    )
                    
                    # Clean up temp file
                    os.remove(temp_path)
                    
                    # Display results
                    st.success(f"Successfully processed and localized document with {len(elements)} elements")
                    
                    st.markdown("---")
                    st.subheader(f"Localized Summary ({selected_language})")
                    st.markdown(f"**Cultural Context:** {contexts[selected_context]}")
                    st.markdown("---")
                    
                    # Display the localized summary
                    st.markdown(localized_summary)
                    
                    # Optional: Download functionality
                    # if st.button("Download Summary"):
                        # Create downloadable text file
#                         summary_text = f"""
# Document Localization Summary
#
# Original Document: {uploaded_file.name}
# Target Language: {languages[selected_language]}
# Cultural Context: {contexts[selected_context]}
# Generated on: {st.session_state.get('current_time', 'N/A')}
#
# ---
#
# {localized_summary}
#                         """
#
#                         st.download_button( label="Download Localized Summary", data=summary_text, file_name=f"localized_summary_{selected_language.lower()}_{uploaded_file.name.replace('.pdf', '.txt')}",
#                             mime="text/plain"
#                         )
                    
                    # Store in session state for potential follow-up questions
                    st.session_state.last_localized_elements = elements
                    st.session_state.last_localization_language = selected_language
                    st.session_state.last_localization_context = selected_context
                    
                except Exception as e:
                    st.error(f"Error processing document: {str(e)}")
                    # Clean up temp file if it exists
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
    
    # Additional features section
    st.markdown("---")
    st.subheader("About Document Localization")
    
    with st.expander("What does localization include?"):
        st.markdown("""
        **Cultural Adaptation:**
        - Business practices and etiquette
        - Regional terminology and concepts
        - Cultural context and relevance
        - Local regulations and standards
        
        **Language Features:**
        - Native language translation
        - Cultural idioms and expressions
        - Appropriate formality levels
        - Regional variations
        
        **Content Types Supported:**
        - Business documents and contracts
        - Technical specifications and manuals
        - Legal documents and agreements
        - Academic and research papers
        - Medical and healthcare documents
        - Educational materials
        """)
    
    with st.expander("Supported Languages & Regions"):
        st.markdown("**Indian Languages:** Hindi, Bengali, Telugu, Tamil, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Urdu, and more...")
        st.markdown("**Global Languages:** English, Spanish, French, German, Chinese, Japanese, Arabic, Russian, and 40+ others...")
        st.markdown("**Cultural Contexts:** India (North/South/East/West), USA, UK, EU, Asia-Pacific, Middle East, Latin America, and specialized industry contexts...")

# Session state initialization for localization
def init_localization_session_state():
    """Initialize session state variables for localization"""
    if "last_localized_elements" not in st.session_state:
        st.session_state.last_localized_elements = None
    if "last_localization_language" not in st.session_state:
        st.session_state.last_localization_language = None
    if "last_localization_context" not in st.session_state:
        st.session_state.last_localization_context = None
