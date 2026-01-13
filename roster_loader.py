import pandas as pd
import streamlit as st

@st.cache_data
def load_student_roster():
    """Load student names from the roster CSV file and return formatted list."""
    try:
        df = pd.read_csv('spring26roster.csv')
        # Format as "Last Name, First Name"
        names = df.apply(lambda row: f"{row['Last Name']}, {row['First Name']}", axis=1).tolist()
        # Sort alphabetically
        names.sort()
        return names
    except Exception as e:
        st.error(f"Error loading roster: {str(e)}")
        return []
