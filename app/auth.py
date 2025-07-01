import streamlit as st
from typing import Dict, Optional, Tuple

from db import supabase

class Auth:
    """Handles user authentication with Supabase."""

    @staticmethod
    def sign_up(email: str, password: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Register a new user.
        
        Args:
            email: User's email
            password: User's password
            
        Returns:
            Tuple of (success, user_data, error_message)
        """
        try:
            response = supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            if response.user:
                return True, response.user, None
            return False, None, "Failed to register user"
        except Exception as e:
            return False, None, str(e)

    @staticmethod
    def sign_in(email: str, password: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Sign in an existing user.
        
        Args:
            email: User's email
            password: User's password
            
        Returns:
            Tuple of (success, user_data, error_message)
        """
        try:
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            if response.user:
                return True, response.user, None
            return False, None, "Failed to log in"
        except Exception as e:
            return False, None, str(e)

    @staticmethod
    def sign_out() -> bool:
        """
        Sign out the current user.
        
        Returns:
            True if sign out was successful, False otherwise
        """
        try:
            supabase.auth.sign_out()
            return True
        except Exception:
            return False

    @staticmethod
    def get_current_user() -> Optional[Dict]:
        """
        Get the current logged-in user.
        
        Returns:
            User data if a user is logged in, None otherwise
        """
        try:
            response = supabase.auth.get_user()
            return response.user
        except Exception:
            return None

    @staticmethod
    def initialize_session_state():
        """Initialize session state for authentication."""
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False
        if "user" not in st.session_state:
            st.session_state.user = None

    @staticmethod
    def check_user_authenticated() -> bool:
        """
        Check if user is authenticated.
        
        Returns:
            True if user is authenticated, False otherwise
        """
        # If we already have an authenticated user in session state
        if st.session_state.get("authenticated", False):
            return True
            
        # Otherwise, check with Supabase
        user = Auth.get_current_user()
        if user:
            st.session_state.authenticated = True
            st.session_state.user = user
            return True
            
        return False
