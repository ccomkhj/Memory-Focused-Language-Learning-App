import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from supabase.client import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)


class FlashcardDB:
    """Handles all database operations for flashcards."""

    @staticmethod
    def add_flashcard(user_id: str, content: str) -> Dict:
        """
        Add a new flashcard to the database.

        Args:
            user_id: The user's ID
            content: The content of the flashcard

        Returns:
            The created flashcard
        """
        # Set next_review_at to current time so it's immediately available for review
        data = {
            "user_id": user_id,
            "content": content,
            "status": "to-learn",
            "next_review_at": datetime.now(timezone.utc).isoformat(),
        }

        response = supabase.table("flashcards").insert(data).execute()
        return response.data[0] if response.data else None

    @staticmethod
    def get_flashcards(user_id: str) -> List[Dict]:
        """
        Get all flashcards for a user.

        Args:
            user_id: The user's ID

        Returns:
            List of flashcards
        """
        response = (
            supabase.table("flashcards")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data if response.data else []

    @staticmethod
    def get_due_flashcards(user_id: str, limit: int = 10) -> List[Dict]:
        """
        Get flashcards that are due for review.

        Args:
            user_id: The user's ID
            limit: Maximum number of flashcards to return

        Returns:
            List of flashcards due for review
        """
        now = datetime.now(timezone.utc).isoformat()
        response = (
            supabase.table("flashcards")
            .select("*")
            .eq("user_id", user_id)
            .neq("status", "fully-memorized")
            .lte("next_review_at", now)
            .order("next_review_at")
            .limit(limit)
            .execute()
        )
        return response.data if response.data else []

    @staticmethod
    def update_flashcard_status(flashcard_id: int, new_status: str) -> Dict:
        """
        Update the learning status of a flashcard.

        Args:
            flashcard_id: ID of the flashcard to update
            new_status: New learning status

        Returns:
            Updated flashcard data
        """
        now = datetime.now(timezone.utc)

        # Get current flashcard data to determine the next review time
        # Get current flashcard data
        (supabase.table("flashcards").select("*").eq("id", flashcard_id).execute())

        # Calculate next review time based on the new status
        next_review_at = now

        if new_status == "once-checked":
            # Set next review time to 24 hours from now
            next_review_at = now + timedelta(hours=24)
            data = {
                "status": new_status,
                "status_once_checked_at": now.isoformat(),
                "last_checked_at": now.isoformat(),
                "next_review_at": next_review_at.isoformat(),
            }
        elif new_status == "twice-checked":
            # Set next review time to 48 hours from now
            next_review_at = now + timedelta(hours=48)
            data = {
                "status": new_status,
                "status_twice_checked_at": now.isoformat(),
                "last_checked_at": now.isoformat(),
                "next_review_at": next_review_at.isoformat(),
            }
        elif new_status == "fully-memorized":
            data = {
                "status": new_status,
                "status_fully_memorized_at": now.isoformat(),
                "last_checked_at": now.isoformat(),
                "next_review_at": None,  # No more reviews needed
            }
        else:  # to-learn
            data = {
                "status": new_status,
                "last_checked_at": now.isoformat(),
                "next_review_at": now.isoformat(),  # Available immediately
            }

        response = (
            supabase.table("flashcards").update(data).eq("id", flashcard_id).execute()
        )
        return response.data[0] if response.data else None

    @staticmethod
    def delete_flashcard(flashcard_id: int) -> bool:
        """
        Delete a flashcard.

        Args:
            flashcard_id: ID of the flashcard to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        response = (
            supabase.table("flashcards").delete().eq("id", flashcard_id).execute()
        )
        return len(response.data) > 0
