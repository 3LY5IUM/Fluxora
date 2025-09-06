# src/quiz.py
from pathlib import Path
from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from .config import Config
from .pdf_processor import PDF_processor
from .vectors import add_documents, query
import os
import json
import random
import re

class QuizGenerator:
    def __init__(self):
        self.config = Config()
        self.pdf_processor = PDF_processor()
        self.llm = ChatGoogleGenerativeAI(
            model=self.config.CHAT_MODEL_BEST,
            temperature=0.3,  # Lower temperature for more consistent JSON
            google_api_key=self.config.GEMINI_API_KEY,
            transport="rest"
        )
    
    def extract_topics_from_pdf(self, pdf_elements: List[Dict[str, Any]]) -> List[str]:
        """Extract main topics from processed PDF elements"""
        try:
            # Combine all text content
            all_text = ""
            for element in pdf_elements:
                if element.get("content_type") == "text":
                    all_text += element["content"] + "\n"
                elif element.get("content_type") == "table":
                    all_text += f"Table content: {element['content']}\n"
                elif element.get("content_type") == "image" and element.get("image_desc"):
                    all_text += f"Image description: {element['image_desc']}\n"
            
            # Limit text length to avoid token limits
            if len(all_text) > 8000:
                all_text = all_text[:8000] + "..."
            
            prompt = f"""
            Analyze the following document content and extract 5-7 main topics that could be used for quiz questions.
            
            Content: {all_text}
            
            Return only a numbered list of topics, each topic should be 2-5 words describing a key concept, subject, or theme.
            
            Example format:
            1. Data Structures
            2. Algorithm Complexity  
            3. Memory Management
            4. Network Protocols
            5. Database Design
            
            Topics:
            """
            
            result = self.llm.invoke(prompt)
            topics_text = result.content.strip()
            
            # Parse topics from numbered list
            topics = []
            for line in topics_text.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    # Remove numbering and clean up
                    topic = line.split('.', 1)[-1].split('-', 1)[-1].strip()
                    if topic and len(topic) > 2:
                        topics.append(topic)
            
            return topics[:7]  # Limit to 7 topics
            
        except Exception as e:
            print(f"Error extracting topics: {str(e)}")
            return ["General Content", "Key Concepts", "Main Ideas"]
    
    def generate_quiz_questions(self, topic: str, pdf_elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate 5 mixed-type questions on a specific topic"""
        try:
            # Find relevant content for the topic
            topic_content = self._get_topic_relevant_content(topic, pdf_elements)
            
            if not topic_content:
                topic_content = "No specific content found for this topic."
            
            # Use a simpler approach - generate one question at a time
            questions = []
            question_types = ["multiple_choice", "multiple_choice", "true_false", "fill_blank", "short_answer"]
            
            for i, q_type in enumerate(question_types):
                question = self._generate_single_question(topic, topic_content, q_type, i+1)
                if question:
                    questions.append(question)
            
            return {"questions": questions}
                
        except Exception as e:
            print(f"Error generating questions: {str(e)}")
            return self._create_fallback_questions(topic, pdf_elements)
    
    def _generate_single_question(self, topic: str, content: str, question_type: str, question_num: int) -> Dict[str, Any]:
        """Generate a single question of specified type"""
        try:
            if question_type == "multiple_choice":
                prompt = f"""
                Based on the following content about "{topic}", create 1 multiple choice question.
                
                Content: {content[:3000]}
                
                Create a question with 4 realistic options where only one is correct.
                
                Respond in this exact format:
                QUESTION: [Your question here]
                A) [First option]
                B) [Second option] 
                C) [Third option]
                D) [Fourth option]
                CORRECT: [A, B, C, or D]
                EXPLANATION: [Why the answer is correct]
                REVIEW: [What section to review if wrong]
                """
            
            elif question_type == "true_false":
                prompt = f"""
                Based on the following content about "{topic}", create 1 true/false question.
                
                Content: {content[:3000]}
                
                Create a statement that is either clearly true or clearly false based on the content.
                
                Respond in this exact format:
                QUESTION: [Your statement here]
                CORRECT: [True or False]
                EXPLANATION: [Why this is the correct answer]
                REVIEW: [What section to review if wrong]
                """
            
            elif question_type == "fill_blank":
                prompt = f"""
                Based on the following content about "{topic}", create 1 fill-in-the-blank question.
                
                Content: {content[:3000]}
                
                Create a sentence with one important word or phrase replaced with "______".
                
                Respond in this exact format:
                QUESTION: [Your sentence with ______ for the missing part]
                CORRECT: [The word/phrase that goes in the blank]
                EXPLANATION: [Why this is the correct answer]
                REVIEW: [What section to review if wrong]
                """
            
            else:  # short_answer
                prompt = f"""
                Based on the following content about "{topic}", create 1 short answer question.
                
                Content: {content[:3000]}
                
                Create a question that requires a 1-2 sentence answer.
                
                Respond in this exact format:
                QUESTION: [Your question here]
                CORRECT: [A good 1-2 sentence answer]
                EXPLANATION: [Additional explanation]
                REVIEW: [What section to review if wrong]
                """
            
            result = self.llm.invoke(prompt)
            response = result.content.strip()
            
            return self._parse_question_response(response, question_type)
            
        except Exception as e:
            print(f"Error generating {question_type} question: {str(e)}")
            return None
    
    def _parse_question_response(self, response: str, question_type: str) -> Dict[str, Any]:
        """Parse the LLM response into a structured question"""
        try:
            lines = response.split('\n')
            question_text = ""
            options = []
            correct_answer = ""
            explanation = ""
            review_section = ""
            
            for line in lines:
                line = line.strip()
                if line.startswith("QUESTION:"):
                    question_text = line.replace("QUESTION:", "").strip()
                elif line.startswith(("A)", "B)", "C)", "D)")):
                    options.append(line)
                elif line.startswith("CORRECT:"):
                    correct_answer = line.replace("CORRECT:", "").strip()
                elif line.startswith("EXPLANATION:"):
                    explanation = line.replace("EXPLANATION:", "").strip()
                elif line.startswith("REVIEW:"):
                    review_section = line.replace("REVIEW:", "").strip()
            
            question_dict = {
                "type": question_type,
                "question": question_text,
                "correct_answer": correct_answer,
                "explanation": explanation or "Answer explanation not available",
                "review_section": review_section or "Review the relevant content"
            }
            
            if question_type == "multiple_choice" and options:
                question_dict["options"] = options
            
            return question_dict
            
        except Exception as e:
            print(f"Error parsing question response: {str(e)}")
            return None
    
    def _get_topic_relevant_content(self, topic: str, pdf_elements: List[Dict[str, Any]]) -> str:
        """Extract content relevant to the specific topic"""
        relevant_content = ""
        topic_lower = topic.lower()
        
        for element in pdf_elements:
            content = element.get("content", "")
            if any(word in content.lower() for word in topic_lower.split()):
                if element.get("content_type") == "text":
                    relevant_content += content + "\n"
                elif element.get("content_type") == "table":
                    relevant_content += f"Table: {content}\n"
                elif element.get("content_type") == "image" and element.get("image_desc"):
                    relevant_content += f"Image: {element['image_desc']}\n"
        
        # If no specific content found, use general content
        if not relevant_content.strip():
            for element in pdf_elements[:5]:  # Use first 5 elements as general content
                content = element.get("content", "")
                if element.get("content_type") == "text":
                    relevant_content += content + "\n"
                elif element.get("content_type") == "table":
                    relevant_content += f"Table: {content}\n"
        
        # Limit content length
        if len(relevant_content) > 6000:
            relevant_content = relevant_content[:6000] + "..."
        
        return relevant_content or "General content from the document"
    
    def _create_fallback_questions(self, topic: str, pdf_elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create fallback questions if generation fails"""
        # Try to create a simple question from the actual content
        content_sample = ""
        for element in pdf_elements[:3]:
            if element.get("content_type") == "text" and element.get("content"):
                content_sample += element["content"][:200] + " "
        
        return {
            "questions": [
                {
                    "type": "multiple_choice",
                    "question": f"Based on the document content about {topic}, which statement is most accurate?",
                    "options": [
                        "A) The document provides comprehensive information on this topic",
                        "B) The topic is not covered in the document", 
                        "C) The information is incomplete",
                        "D) No relevant details are provided"
                    ],
                    "correct_answer": "A",
                    "explanation": "The document contains relevant information about the topic.",
                    "review_section": f"Review the main content about {topic}"
                }
            ]
        }
    
    def evaluate_answer(self, question: Dict[str, Any], user_answer: str) -> bool:
        """Evaluate if the user's answer is correct"""
        if not user_answer:
            return False
            
        correct_answer = question["correct_answer"].lower().strip()
        user_answer = user_answer.lower().strip()
        
        if question["type"] in ["multiple_choice", "true_false"]:
            return user_answer == correct_answer
        elif question["type"] in ["fill_blank", "short_answer"]:
            # Use fuzzy matching for text answers
            return self._fuzzy_match(user_answer, correct_answer)
        
        return False
    
    def _fuzzy_match(self, user_answer: str, correct_answer: str) -> bool:
        """Simple fuzzy matching for text answers"""
        if not user_answer or not correct_answer:
            return False
        
        # Check if key words match
        user_words = set(user_answer.lower().split())
        correct_words = set(correct_answer.lower().split())
        
        if len(correct_words) == 0:
            return False
        
        # If 60% of key words match, consider it correct
        matches = len(user_words.intersection(correct_words))
        return matches >= max(1, len(correct_words) * 0.6)

def render_quiz_ui():
    """Streamlit UI for the quiz functionality"""
    import streamlit as st
    
    st.header("PDF Quiz Generator")
    st.write("Upload a PDF document and test your knowledge with AI-generated questions")
    
    # Initialize quiz generator
    if 'quiz_generator' not in st.session_state:
        st.session_state.quiz_generator = QuizGenerator()
    
    # Step 1: Upload PDF
    st.subheader("Step 1: Upload PDF Document")
    uploaded_file = st.file_uploader(
        "Upload a PDF for quiz generation",
        type="pdf",
        help="Upload the PDF document you want to be quizzed on"
    )
    
    if uploaded_file is not None:
        # Process PDF
        if st.button("Process PDF & Extract Topics", type="primary"):
            with st.spinner("Processing PDF and extracting topics..."):
                try:
                    # Save uploaded file temporarily
                    temp_path = f"temp_quiz_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Process PDF using existing pipeline
                    pdf_elements = st.session_state.quiz_generator.pdf_processor.process_pdf(temp_path)
                    
                    # Extract topics
                    topics = st.session_state.quiz_generator.extract_topics_from_pdf(pdf_elements)
                    
                    # Store in session state
                    st.session_state.pdf_elements = pdf_elements
                    st.session_state.quiz_topics = topics
                    st.session_state.pdf_processed = True
                    
                    # Clean up temp file
                    os.remove(temp_path)
                    
                    st.success(f"PDF processed successfully! Found {len(topics)} topics.")
                    
                except Exception as e:
                    st.error(f"Error processing PDF: {str(e)}")
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
    
    # Step 2: Select Topic (only show if PDF is processed)
    if st.session_state.get('pdf_processed', False):
        st.subheader("Step 2: Choose Quiz Topic")
        topics = st.session_state.get('quiz_topics', [])
        
        if topics:
            selected_topic = st.selectbox(
                "Select a topic for your quiz:",
                topics,
                help="Choose the topic you want to be quizzed on"
            )
            
            if st.button("Generate Quiz Questions", type="primary"):
                with st.spinner("Generating quiz questions..."):
                    try:
                        quiz_data = st.session_state.quiz_generator.generate_quiz_questions(
                            selected_topic, st.session_state.pdf_elements
                        )
                        
                        st.session_state.quiz_data = quiz_data
                        st.session_state.selected_topic = selected_topic
                        st.session_state.quiz_ready = True
                        st.session_state.quiz_started = False
                        st.session_state.current_question = 0
                        st.session_state.user_answers = {}
                        st.session_state.quiz_completed = False
                        
                        questions_count = len(quiz_data.get('questions', []))
                        st.success(f"Generated {questions_count} questions on {selected_topic}!")
                        
                        # Debug info
                        if questions_count > 0:
                            st.info("Click 'Start Quiz' below to begin!")
                        else:
                            st.warning("No questions were generated. Try a different topic.")
                        
                    except Exception as e:
                        st.error(f"Error generating quiz: {str(e)}")
        else:
            st.warning("No topics found. Try processing a different PDF.")
    
    # Step 3: Take Quiz (only show if quiz is ready)
    if st.session_state.get('quiz_ready', False) and not st.session_state.get('quiz_completed', False):
        st.subheader(f"Step 3: Quiz on {st.session_state.get('selected_topic', 'Topic')}")
        
        if not st.session_state.get('quiz_started', False):
            if st.button("Start Quiz", type="primary"):
                st.session_state.quiz_started = True
                st.rerun()
        
        if st.session_state.get('quiz_started', False):
            quiz_data = st.session_state.quiz_data
            questions = quiz_data.get('questions', [])
            
            if questions:
                # Display all questions at once
                st.write("Answer all questions below, then submit your quiz:")
                
                user_answers = {}
                
                for i, question in enumerate(questions):
                    st.markdown(f"**Question {i+1}**: {question['question']}")
                    
                    if question['type'] == 'multiple_choice':
                        options = question.get('options', [])
                        if options:
                            answer = st.radio(
                                "Choose your answer:",
                                options,
                                key=f"q_{i}",
                                index=None
                            )
                            if answer:
                                user_answers[i] = answer[0]  # Get just the letter (A, B, C, D)
                        else:
                            st.error(f"No options available for question {i+1}")
                    
                    elif question['type'] == 'true_false':
                        answer = st.radio(
                            "Choose your answer:",
                            ["True", "False"],
                            key=f"q_{i}",
                            index=None
                        )
                        if answer:
                            user_answers[i] = answer
                    
                    elif question['type'] in ['fill_blank', 'short_answer']:
                        answer = st.text_input(
                            "Your answer:",
                            key=f"q_{i}",
                            placeholder="Type your answer here..."
                        )
                        if answer.strip():
                            user_answers[i] = answer.strip()
                    
                    st.markdown("---")
                
                # Submit quiz
                if st.button("Submit Quiz", type="primary"):
                    if len(user_answers) == len(questions):
                        # Evaluate answers
                        st.session_state.user_answers = user_answers
                        st.session_state.quiz_completed = True
                        st.rerun()
                    else:
                        st.warning("Please answer all questions before submitting.")
                        missing = len(questions) - len(user_answers)
                        st.info(f"You have {missing} unanswered question(s).")
            else:
                st.error("No questions available. Please generate quiz questions first.")
    
    # Step 4: Show Results (only show if quiz is completed)
    if st.session_state.get('quiz_completed', False):
        st.subheader("Quiz Results")
        
        quiz_data = st.session_state.quiz_data
        questions = quiz_data.get('questions', [])
        user_answers = st.session_state.user_answers
        
        # Calculate score
        correct_count = 0
        results = []
        
        for i, question in enumerate(questions):
            user_answer = user_answers.get(i, "")
            is_correct = st.session_state.quiz_generator.evaluate_answer(question, user_answer)
            
            if is_correct:
                correct_count += 1
            
            results.append({
                'question': question,
                'user_answer': user_answer,
                'is_correct': is_correct,
                'index': i
            })
        
        # Display score
        score = correct_count / len(questions) * 100 if questions else 0
        pass_threshold = 60  # 60% to pass
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Score", f"{score:.1f}%")
        with col2:
            st.metric("Correct", f"{correct_count}/{len(questions)}")
        with col3:
            if score >= pass_threshold:
                st.success("PASSED")
            else:
                st.error("FAILED")
        
        # Show detailed results
        st.subheader("Detailed Results")
        
        for result in results:
            question = result['question']
            is_correct = result['is_correct']
            user_answer = result['user_answer']
            
            if is_correct:
                st.success(f"Question {result['index']+1}: Correct!")
            else:
                st.error(f"Question {result['index']+1}: Incorrect")
            
            st.write(f"**Question**: {question['question']}")
            st.write(f"**Your answer**: {user_answer}")
            st.write(f"**Correct answer**: {question['correct_answer']}")
            st.write(f"**Explanation**: {question['explanation']}")
            
            if not is_correct:
                st.info(f"**Review**: {question.get('review_section', 'Review the relevant content')}")
            
            st.markdown("---")
        
        # Recommendations
        if score < pass_threshold:
            st.subheader("Study Recommendations")
            
            incorrect_questions = [r for r in results if not r['is_correct']]
            review_sections = [q['question'].get('review_section', 'General content') for q in incorrect_questions]
            
            st.write("Based on your incorrect answers, focus on these areas:")
            for i, section in enumerate(set(review_sections), 1):
                st.write(f"{i}. {section}")
        
        # Reset button
        if st.button("Take Another Quiz"):
            # Clear quiz-related session state
            for key in ['quiz_ready', 'quiz_started', 'quiz_completed', 'quiz_data', 'user_answers']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

