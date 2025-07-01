import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List, Callable

from app.db import FlashcardDB


def render_flashcard(
    flashcard: Dict,
    on_update: Callable[[int, str], None],
    on_delete: Callable[[int], None],
):
    """
    Render a flashcard with interaction buttons.

    Args:
        flashcard: The flashcard data
        on_update: Function to call when updating the flashcard status
        on_delete: Function to call when deleting the flashcard
    """
    with st.container():
        col1, col2 = st.columns([3, 1])

        with col1:
            st.subheader(flashcard["content"])

            # Show status and last checked time
            status = flashcard["status"].replace("-", " ").title()
            last_checked = "Never"
            if flashcard.get("last_checked_at"):
                last_checked_dt = datetime.fromisoformat(
                    flashcard["last_checked_at"].replace("Z", "+00:00")
                )
                last_checked = last_checked_dt.strftime("%Y-%m-%d %H:%M")

            st.caption(f"Status: {status} | Last checked: {last_checked}")

        with col2:
            # Display appropriate buttons based on current status
            current_status = flashcard["status"]

            if current_status == "to-learn":
                st.button(
                    "Mark as Checked",
                    key=f"once_{flashcard['id']}",
                    on_click=lambda: on_update(flashcard["id"], "once-checked"),
                )

            elif current_status == "once-checked":
                # Check if 24 hours have passed
                if flashcard.get("status_once_checked_at"):
                    checked_at = datetime.fromisoformat(
                        flashcard["status_once_checked_at"].replace("Z", "+00:00")
                    )
                    time_passed = datetime.now(timezone.utc) - checked_at

                    if time_passed.total_seconds() >= 24 * 3600:
                        st.button(
                            "Mark as Twice Checked",
                            key=f"twice_{flashcard['id']}",
                            on_click=lambda: on_update(
                                flashcard["id"], "twice-checked"
                            ),
                        )
                    else:
                        hours_left = 24 - (time_passed.total_seconds() / 3600)
                        st.write(f"⏳ {hours_left:.1f} hours left")

            elif current_status == "twice-checked":
                # Check if 48 hours have passed
                if flashcard.get("status_twice_checked_at"):
                    checked_at = datetime.fromisoformat(
                        flashcard["status_twice_checked_at"].replace("Z", "+00:00")
                    )
                    time_passed = datetime.now(timezone.utc) - checked_at

                    if time_passed.total_seconds() >= 48 * 3600:
                        st.button(
                            "Mark as Memorized",
                            key=f"memo_{flashcard['id']}",
                            on_click=lambda: on_update(
                                flashcard["id"], "fully-memorized"
                            ),
                        )
                    else:
                        hours_left = 48 - (time_passed.total_seconds() / 3600)
                        st.write(f"⏳ {hours_left:.1f} hours left")

            # Delete button for all cards
            st.button(
                "🗑️",
                key=f"del_{flashcard['id']}",
                on_click=lambda: on_delete(flashcard["id"]),
            )

        st.divider()


def render_add_flashcard_form(user_id: str, on_add: Callable[[], None]):
    """
    Render a form for adding new flashcards.

    Args:
        user_id: The user's ID
        on_add: Function to call after adding a flashcard
    """
    with st.form("add_flashcard", clear_on_submit=True):
        st.subheader("Add New Vocabulary/Phrase")
        content = st.text_area(
            "Enter vocabulary, sentence, or phrase to learn:",
            placeholder="e.g., Guten Tag - Good day",
        )

        submitted = st.form_submit_button("Add Flashcard")

        if submitted and content:
            FlashcardDB.add_flashcard(user_id, content.strip())
            st.success("Flashcard added successfully!")
            on_add()


def render_flashcard_stats(flashcards: List[Dict]):
    """
    Render statistics about flashcards.

    Args:
        flashcards: List of all flashcards
    """
    if not flashcards:
        st.info("No flashcards added yet. Add some to start learning!")
        return

    total = len(flashcards)

    # Count flashcards by status
    to_learn = sum(1 for card in flashcards if card["status"] == "to-learn")
    once_checked = sum(1 for card in flashcards if card["status"] == "once-checked")
    twice_checked = sum(1 for card in flashcards if card["status"] == "twice-checked")
    fully_memorized = sum(
        1 for card in flashcards if card["status"] == "fully-memorized"
    )

    # Create a progress bar for overall progress
    progress = (
        (once_checked * 0.33 + twice_checked * 0.67 + fully_memorized) / total
        if total > 0
        else 0
    )

    st.subheader("Learning Progress")
    st.progress(progress)

    # Create columns for the stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("To Learn", to_learn)
    with col2:
        st.metric("Once Checked", once_checked)
    with col3:
        st.metric("Twice Checked", twice_checked)
    with col4:
        st.metric("Memorized", fully_memorized)

    # Show a pie chart of the distribution
    data = {
        "Status": ["To Learn", "Once Checked", "Twice Checked", "Memorized"],
        "Count": [to_learn, once_checked, twice_checked, fully_memorized],
    }
    df = pd.DataFrame(data)

    if sum(df["Count"]) > 0:  # Only show chart if there's data
        st.subheader("Distribution")
        # Use bar chart instead of pie chart for compatibility with Streamlit 1.25.0
        st.bar_chart(df.set_index("Status"))


def render_auth_forms():
    """Render login and registration forms."""
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        with st.form("login_form"):
            st.subheader("Login")
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Log in")

            return submitted, email, password, "login" if submitted else None

    with tab2:
        with st.form("register_form"):
            st.subheader("Register")
            email = st.text_input("Email", key="register_email")
            password = st.text_input(
                "Password", type="password", key="register_password"
            )
            confirm_password = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Register")

            if submitted and password != confirm_password:
                st.error("Passwords don't match!")
                return False, None, None, None

            return submitted, email, password, "register" if submitted else None

    return False, None, None, None
