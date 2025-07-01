import streamlit as st
import pandas as pd

from app.auth import Auth
from app.db import FlashcardDB
from app.components import (
    render_flashcard,
    render_add_flashcard_form,
    render_flashcard_stats,
    render_auth_forms,
)
from app.chat_components import (
    render_tutor_chat,
    render_learning_report,
    render_chat_history,
)

# Page configuration
st.set_page_config(
    page_title="Language Learning App",
    page_icon="🇩🇪",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    # Initialize session state
    Auth.initialize_session_state()

    # Initialize app state variables
    if "update_flashcard" not in st.session_state:
        st.session_state.update_flashcard = False
    if "delete_flashcard" not in st.session_state:
        st.session_state.delete_flashcard = False

    # Application header
    st.title("Language Learning App")

    # Check if user is authenticated
    if not Auth.check_user_authenticated():
        # If not authenticated, show login/register forms
        submitted, email, password, form_type = render_auth_forms()

        if submitted and form_type == "login":
            success, user, error = Auth.sign_in(email, password)
            if success:
                st.session_state.authenticated = True
                st.session_state.user = user
                st.experimental_rerun()
            else:
                st.error(f"Login failed: {error}")

        elif submitted and form_type == "register":
            success, user, error = Auth.sign_up(email, password)
            if success:
                st.session_state.authenticated = True
                st.session_state.user = user
                st.success("Registration successful! Welcome to the app.")
                st.experimental_rerun()
            else:
                st.error(f"Registration failed: {error}")
    else:
        # User is authenticated
        user = st.session_state.user
        user_id = user.id

        # Sidebar with user info and logout option
        with st.sidebar:
            st.write(f"👤 Logged in as: {user.email}")
            if st.button("Logout"):
                Auth.sign_out()
                st.session_state.authenticated = False
                st.session_state.user = None
                st.experimental_rerun()

            st.divider()

            # Filter options
            st.subheader("Filter Cards")
            status_filter = st.multiselect(
                "Status",
                ["to-learn", "once-checked", "twice-checked", "fully-memorized"],
                default=["to-learn", "once-checked", "twice-checked"],
            )

        # Main content area - create tabs for flashcard related functions
        tab1, tab2, tab3 = st.tabs(
            ["Due for Review", "All Flashcards", "Add New"]
        )

        with tab1:
            st.subheader("Flashcards Due for Review")

            # Get cards due for review
            due_cards = FlashcardDB.get_due_flashcards(user_id)

            # Check if we need to refresh the page
            if st.session_state.update_flashcard or st.session_state.delete_flashcard:
                st.session_state.update_flashcard = False
                st.session_state.delete_flashcard = False
                st.experimental_rerun()

            if due_cards:
                for card in due_cards:
                    render_flashcard(
                        card,
                        on_update=lambda id, status: [
                            FlashcardDB.update_flashcard_status(id, status),
                            setattr(st.session_state, "update_flashcard", True),
                        ],
                        on_delete=lambda id: [
                            FlashcardDB.delete_flashcard(id),
                            setattr(st.session_state, "delete_flashcard", True),
                        ],
                    )
            else:
                st.info("No cards due for review! 🎉")
                st.write(
                    "Add more cards or wait until your existing cards are ready for review."
                )

        with tab2:
            st.subheader("All Flashcards")

            # Get all flashcards with filter applied
            all_cards = FlashcardDB.get_flashcards(user_id)
            filtered_cards = [
                card for card in all_cards if card["status"] in status_filter
            ]

            if filtered_cards:
                # Convert to DataFrame for better display
                df = pd.DataFrame(filtered_cards)

                # Format the data for display
                display_df = df[["id", "content", "status", "created_at"]].copy()
                display_df["status"] = display_df["status"].apply(
                    lambda x: x.replace("-", " ").title()
                )
                display_df["created_at"] = pd.to_datetime(
                    display_df["created_at"]
                ).dt.strftime("%Y-%m-%d")
                display_df.columns = ["ID", "Content", "Status", "Created At"]

                st.dataframe(display_df, use_container_width=True)

                # Select a flashcard to update
                selected_id = st.selectbox(
                    "Select flashcard ID to update:",
                    options=[card["id"] for card in filtered_cards],
                    format_func=lambda x: next(
                        (c["content"] for c in filtered_cards if c["id"] == x), ""
                    ),
                )

                if selected_id:
                    selected_card = next(
                        (c for c in filtered_cards if c["id"] == selected_id), None
                    )
                    if selected_card:
                        col1, col2 = st.columns(2)
                        with col1:
                            new_status = st.selectbox(
                                "Update status to:",
                                options=[
                                    "to-learn",
                                    "once-checked",
                                    "twice-checked",
                                    "fully-memorized",
                                ],
                                index=[
                                    "to-learn",
                                    "once-checked",
                                    "twice-checked",
                                    "fully-memorized",
                                ].index(selected_card["status"]),
                            )
                        with col2:
                            if st.button("Update Status"):
                                FlashcardDB.update_flashcard_status(
                                    selected_id, new_status
                                )
                                st.session_state.update_flashcard = True
                                st.success(f"Updated status to {new_status}")

                        if st.button("Delete This Flashcard"):
                            FlashcardDB.delete_flashcard(selected_id)
                            st.session_state.delete_flashcard = True
                            st.success("Flashcard deleted")
            else:
                st.info("No flashcards found with the selected filters.")

        with tab3:
            # Add new flashcards
            render_add_flashcard_form(user_id, lambda: None)

            # Show statistics
            st.divider()
            all_cards = FlashcardDB.get_flashcards(user_id)
            render_flashcard_stats(all_cards)
        
        # Add page navigation in sidebar
        st.sidebar.divider()
        page = st.sidebar.selectbox(
            "Navigation",
            ["Flashcards", "Tutor Chat"],
            index=0,
            key="navigation"
        )
        
        # Hide flashcard tabs if we're on the Tutor Chat page
        if page == "Tutor Chat":
            # Clear the main area
            st.empty()
            
            # Create a new container for the tutor chat page
            # This ensures we're at the top level for chat_input
            st.header("Language Learning Tutor")
            
            # Target language selection
            language_options = ["German", "French", "Spanish", "Italian", "Japanese", "Chinese", "Korean"]
            selected_language = st.selectbox("Select Language", language_options, index=0)
            
            # Initialize session state for language if not already set
            if "selected_lang" not in st.session_state:
                st.session_state.selected_lang = selected_language
            else:
                # Only update if changed
                if selected_language != st.session_state.selected_lang:
                    st.session_state.selected_lang = selected_language
            
            # Create a separate function for displaying chat outside of any containers
            from app.chat_page import display_chat_page
            display_chat_page(user_id, st.session_state.selected_lang)


if __name__ == "__main__":
    main()
