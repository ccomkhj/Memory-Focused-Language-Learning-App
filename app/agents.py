"""
Language Learning Tutor and Report Generator agents using CrewAI.
"""

import os
from typing import Dict, List, Optional
from datetime import datetime

from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from app.db import supabase, FlashcardDB

# Load environment variables
load_dotenv()


class LearningAgents:
    """Class for managing language learning AI agents."""

    def __init__(self):
        """Initialize the learning agents."""
        self.llm = ChatOpenAI(
            model="gpt-4.1",
            temperature=0.7,
            api_key=os.environ.get("OPENAI_API_KEY"),
        )

    def _get_user_flashcards_tool(self, user_id: str):
        """Create a tool to fetch user's flashcards."""

        @tool("Fetch user flashcards")
        def get_user_flashcards():
            """Fetches all flashcards for the user with their current learning status."""
            flashcards = FlashcardDB.get_flashcards(user_id)
            return flashcards

        return get_user_flashcards

    def _save_chat_history_tool(self, user_id: str):
        """Create a tool to save chat history to database."""

        @tool("Save chat history")
        def save_chat(conversation: str, summary: str = None):
            """Saves the chat conversation and summary to the database."""
            data = {
                "user_id": user_id,
                "conversation": conversation,
                "summary": summary,
                "created_at": datetime.now().isoformat(),
            }
            response = supabase.table("chat_history").insert(data).execute()
            return response.data[0] if response.data else None

        return save_chat

    def create_language_tutor_agent(self, user_id: str, target_language: str) -> Agent:
        """Create a language tutor agent that teaches based on user's flashcards."""
        return Agent(
            role="Language Tutor",
            goal=f"Help the student learn {target_language} by casually talking using the unchecked flashcards.",
            backstory=f"You are an expert {target_language} teacher with years of experience. "
            "You reuse and rephrase flashcards to help the student learn.",
            verbose=True,
            allow_delegation=True,
            tools=[self._get_user_flashcards_tool(user_id)],
            llm=self.llm,
        )

    def create_report_generator_agent(self, user_id: str) -> Agent:
        """Create an agent that generates learning reports after conversations."""
        return Agent(
            role="Learning Progress Analyst",
            goal="Create insightful reports on the student's learning progress",
            backstory="You are an expert in language acquisition who can analyze conversations "
            "and identify patterns, strengths, weaknesses, and provide recommendations.",
            verbose=True,
            allow_delegation=False,
            tools=[
                self._get_user_flashcards_tool(user_id),
                self._save_chat_history_tool(user_id),
            ],
            llm=self.llm,
        )

    def create_tutor_crew(self, user_id: str, target_language: str) -> Crew:
        """Create a crew with both tutor and analyst agents."""
        tutor = self.create_language_tutor_agent(user_id, target_language)
        analyst = self.create_report_generator_agent(user_id)

        tutor_task = Task(
            description=(
                "Engage in a conversation with the student to teach them "
                f"{target_language} vocabulary and phrases. Focus on their "
                "current knowledge gaps based on their flashcard data. "
                "Provide examples, ask questions, and correct mistakes."
            ),
            expected_output="A helpful and educational conversation that teaches new concepts.",
            agent=tutor,
        )

        analyst_task = Task(
            description=(
                "After the tutoring session, analyze the conversation and the student's responses. "
                "Identify strengths, weaknesses, and areas for improvement. "
                "Generate a concise report with key insights and recommendations for future study."
            ),
            expected_output="A detailed learning progress report with actionable recommendations.",
            agent=analyst,
        )

        crew = Crew(
            agents=[tutor, analyst],
            tasks=[tutor_task, analyst_task],
            verbose=True,
            process=Process.sequential,
        )

        return crew

    def run_tutoring_session(
        self, user_id: str, target_language: str, user_query: str
    ) -> Dict[str, str]:
        """Run a tutoring session and generate a report."""
        crew = self.create_tutor_crew(user_id, target_language)
        result = crew.kickoff(inputs={"user_query": user_query})

        # Extract conversation and report from the result
        # In newer versions of CrewAI, the result is a CrewOutput object
        # Access the task outputs directly using task names as attributes
        try:
            # First try using the task attributes
            if hasattr(result, "tutor_task") and hasattr(result, "analyst_task"):
                conversation = result.tutor_task.output
                report = result.analyst_task.output
            # Fallback to dictionary access for older versions
            elif hasattr(result, "get"):
                conversation = result.get("tutor_task", {}).get("output", "")
                report = result.get("analyst_task", {}).get("output", "")
            # Direct access to results dict in newest versions
            elif hasattr(result, "tasks_outputs"):
                conversation = result.tasks_outputs.get("tutor_task", "")
                report = result.tasks_outputs.get("analyst_task", "")
            else:
                # Last resort - try to extract any string content
                conversation = str(result)
                report = "Unable to generate report due to output format change."
        except Exception as e:
            conversation = f"Error extracting conversation: {str(e)}\nRaw result type: {type(result)}"
            report = "Unable to generate report due to error."

        # Save to database
        chat_data = {
            "user_id": user_id,
            "conversation": conversation,
            "summary": report,
            "created_at": datetime.now().isoformat(),
        }
        supabase.table("chat_history").insert(chat_data).execute()

        return {"conversation": conversation, "report": report}


# Function to retrieve chat history for a user
def get_chat_history(user_id: str) -> List[Dict]:
    """Get chat history for a user."""
    response = (
        supabase.table("chat_history")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data if response.data else []
