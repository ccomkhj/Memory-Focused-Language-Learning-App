"""
Chat page for the language learning tutor feature.
This file contains the tutor chat interface for the language learning app.
"""

import streamlit as st
from datetime import datetime

from app.agents import LearningAgents, get_chat_history
from app.db import supabase


def initialize_chat_state():
    """Initialize session state for chat functionality."""
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "report" not in st.session_state:
        st.session_state.report = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "chat_deleted" not in st.session_state:
        st.session_state.chat_deleted = False
    if "debug_info" not in st.session_state:
        st.session_state.debug_info = None
    if "show_debug" not in st.session_state:
        st.session_state.show_debug = False


def display_chat_message(role, content):
    """Display a chat message with the appropriate styling."""
    if role == "user":
        st.chat_message("user").write(content)
    elif role == "assistant":
        st.chat_message("assistant").write(content)
    elif role == "system":
        st.chat_message("system").write(content)


def process_chat(user_id: str, target_language: str, user_query: str):
    """Process the chat interaction with the AI tutor."""
    try:
        # Initialize agents
        learning_agents = LearningAgents()

        # Run the tutoring session
        result = learning_agents.run_tutoring_session(
            user_id=user_id, target_language=target_language, user_query=user_query
        )

        # Add debug output
        st.session_state.debug_info = (
            f"Result type: {type(result)}\nResult structure: {str(result)[:200]}"
        )

        # Get the conversation and report
        conversation = result.get("conversation", "")
        report = result.get("report", "")

        # Store the report for display in a separate section
        st.session_state.report = report

        # Add assistant's response to chat
        st.session_state.chat_messages.append(
            {"role": "assistant", "content": conversation}
        )

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
        # Catch remaining exceptions as a fallback with proper error handling
        error_msg = f"Unexpected error: {str(e)}"
        st.session_state.chat_messages.append(
            {
                "role": "system",
                "content": f"An error occurred. Please try again later. {error_msg}",
            }
        )
        return error_msg


def display_learning_report():
    """Render the latest learning report."""
    if st.session_state.report:
        st.subheader("Learning Progress Report")
        st.markdown(st.session_state.report)


def delete_chat(chat_id: str, user_id: str) -> bool:
    """Delete a chat conversation from the database.

    Args:
        chat_id: The ID of the chat to delete
        user_id: The user ID for verification

    Returns:
        bool: True if deletion was successful, False otherwise
    """
    try:
        response = (
            supabase.table("chat_history")
            .delete()
            .eq("id", chat_id)
            .eq("user_id", user_id)
            .execute()
        )

        # Check if deletion was successful
        return len(response.data) > 0
    except Exception as e:
        st.error(f"Failed to delete conversation: {str(e)}")
        return False


def display_chat_history(user_id: str):
    """Render previous chat history."""
    st.subheader("Previous Conversations")

    # Get chat history if not already loaded or after deletion
    if not st.session_state.chat_history or st.session_state.chat_deleted:
        with st.spinner("Loading chat history..."):
            st.session_state.chat_history = get_chat_history(user_id)
            st.session_state.chat_deleted = False

    if not st.session_state.chat_history:
        st.info("No previous conversations found.")
        return

    # Display chat history as expandable sections
    for i, chat in enumerate(st.session_state.chat_history):
        chat_date = datetime.fromisoformat(chat["created_at"]).strftime(
            "%Y-%m-%d %H:%M"
        )

        col1, col2 = st.columns([0.9, 0.1])
        with col1:
            expander_label = f"Conversation {i+1} - {chat_date}"
        with col2:
            # Add delete button for each conversation
            if st.button(
                "❌", key=f"delete_{chat['id']}", help="Delete this conversation"
            ):
                if delete_chat(chat["id"], user_id):
                    st.session_state.chat_deleted = True
                    st.experimental_rerun()

        with st.expander(expander_label):
            st.markdown("#### Conversation")
            st.markdown(chat["conversation"])

            if chat["summary"]:
                st.markdown("#### Summary")
                st.markdown(chat["summary"])


def display_chat_page(user_id: str, target_language: str):
    """Display the chat page for the language learning tutor."""
    # Initialize session state
    initialize_chat_state()

    # Display chat interface
    st.subheader(f"{target_language} Language Tutor")

    # Display chat messages
    for message in st.session_state.chat_messages:
        display_chat_message(message["role"], message["content"])

    # Chat input - must be at the root level, not inside any container
    user_query = st.chat_input("Ask your language tutor a question...")

    if user_query:
        # Add user message to chat history
        st.session_state.chat_messages.append({"role": "user", "content": user_query})

        # Display user message
        display_chat_message("user", user_query)

        # Process with AI and display response
        with st.chat_message("assistant"):
            with st.spinner(f"Your {target_language} tutor is thinking..."):
                response = process_chat(user_id, target_language, user_query)
                st.write(response)

    # Display learning report and chat history in columns
    col1, col2 = st.columns(2)
    with col1:
        display_learning_report()
    with col2:
        display_chat_history(user_id)

    # Debug section (developer mode)
    st.sidebar.divider()
    with st.sidebar.expander("Developer Options"):
        show_debug = st.checkbox("Show Debug Info", value=st.session_state.show_debug)
        st.session_state.show_debug = show_debug

        if st.session_state.show_debug and st.session_state.debug_info:
            st.code(st.session_state.debug_info)
