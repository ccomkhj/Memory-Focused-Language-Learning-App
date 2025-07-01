import streamlit as st
import os
import sys

# Add the app directory to the path so we can import modules from it
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

# Import the main module from the app directory
from app.main import main

# Run the main function
if __name__ == "__main__":
    main()
