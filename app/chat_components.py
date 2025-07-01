"""
UI components for the tutor chat feature.
"""

import streamlit as st
from datetime import datetime

from app.agents import LearningAgents, get_chat_history

def initialize_chat_state():
    """Initialize session state for chat functionality."""
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "processing" not in st.session_state:
        st.session_state.processing = False
    if "report" not in st.session_state:
        st.session_state.report = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "user_query" not in st.session_state:
        st.session_state.user_query = ""


def display_chat_message(role, content):
    """Display a chat message with the appropriate styling."""
    if role == "user":
        st.chat_message("user").write(content)
    elif role == "assistant":
        st.chat_message("assistant").write(content)
    elif role == "system":
        st.chat_message("system").write(content)


def process_chat(user_id: str, target_language: str):
    """Process the chat interaction with the AI tutor."""
    try:
        # Initialize agents
        learning_agents = LearningAgents()
        
        # Run the tutoring session
        result = learning_agents.run_tutoring_session(
            user_id=user_id,
            target_language=target_language,
            user_query=st.session_state.user_query
        )
        
        # Get the conversation and report
        conversation = result.get("conversation", "")
        report = result.get("report", "")
        
        # Store the report for display in a separate section
        st.session_state.report = report
        
        # Add assistant's response to chat
        st.session_state.chat_messages.append({"role": "assistant", "content": conversation})
        
        # Update chat history in session state
        st.session_state.chat_history = get_chat_history(user_id)
        
        return conversation
    
    except ImportError as e:
        error_msg = f"Required module not found: {str(e)}"
        st.session_state.chat_messages.append({"role": "system", "content": error_msg})
        return error_msg
    except ValueError as e:
        error_msg = f"Invalid input: {str(e)}"
        st.session_state.chat_messages.append({"role": "system", "content": error_msg})
        return error_msg
    except KeyError as e:
        error_msg = f"Missing key in configuration: {str(e)}"
        st.session_state.chat_messages.append({"role": "system", "content": error_msg})
        return error_msg
    except ConnectionError as e:
        error_msg = f"Connection failed: {str(e)}"
        st.session_state.chat_messages.append({"role": "system", "content": error_msg})
        return error_msg
    except Exception as e:
        # Catch remaining exceptions as a fallback
        error_msg = f"Unexpected error: {str(e)}"
        st.session_state.chat_messages.append({"role": "system", "content": f"An error occurred. Please try again later. {error_msg}"})
        return error_msg


def render_tutor_chat(user_id: str):
    """Render the language learning tutor chat interface."""
    # Initialize session state for chat
    initialize_chat_state()
    
    # Display existing chat messages
    for message in st.session_state.chat_messages:
        display_chat_message(message["role"], message["content"])
    
    # Chat input must be at the top level of the app, not inside any container
    user_query = st.chat_input("Ask your language tutor a question...")
    
    if user_query:
        # Add user message to chat
        st.session_state.user_query = user_query
        st.session_state.chat_messages.append({"role": "user", "content": user_query})
        
        # Get the target language
        target_language = st.session_state.target_language
        
        # Process user query with AI tutor
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = process_chat(user_id, target_language)
                st.write(response)
        
        # Reset the user query
        st.session_state.user_query = ""


def render_learning_report():
    """Render the latest learning report."""
    if st.session_state.report:
        st.subheader("Learning Progress Report")
        st.markdown(st.session_state.report)


def render_chat_history(user_id: str):
    """Render previous chat history."""
    st.subheader("Previous Conversations")
    
    # Get chat history if not already loaded
    if not st.session_state.chat_history:
        with st.spinner("Loading chat history..."):
            st.session_state.chat_history = get_chat_history(user_id)
    
    if not st.session_state.chat_history:
        st.info("No previous conversations found.")
        return
    
    # Display chat history as expandable sections
    for i, chat in enumerate(st.session_state.chat_history):
        chat_date = datetime.fromisoformat(chat["created_at"]).strftime("%Y-%m-%d %H:%M")
        
        with st.expander(f"Conversation {i+1} - {chat_date}"):
            st.markdown("#### Conversation")
            st.markdown(chat["conversation"])
            
            if chat["summary"]:
                st.markdown("#### Summary")
                st.markdown(chat["summary"])
