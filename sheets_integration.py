import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import json
from datetime import datetime

def get_google_sheets_client():
    """Initialize Google Sheets client using service account credentials from file or Streamlit secrets."""
    try:
        import os
        
        # Try to read from secret file (Render) first, then fallback to Streamlit secrets
        credentials_dict = None
        
        # Check for Render secret file locations
        secret_file_paths = [
            "/etc/secrets/google_credentials.json",  # Render secret file location
            "google_credentials.json",               # Local/root directory
        ]
        
        for file_path in secret_file_paths:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    credentials_dict = json.load(f)
                break
        
        # Fallback to Streamlit secrets if no file found
        if not credentials_dict:
            credentials_dict = {
                "type": st.secrets["gcp_service_account"]["type"],
                "project_id": st.secrets["gcp_service_account"]["project_id"],
                "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
                "private_key": st.secrets["gcp_service_account"]["private_key"],
                "client_email": st.secrets["gcp_service_account"]["client_email"],
                "client_id": st.secrets["gcp_service_account"]["client_id"],
                "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
                "token_uri": st.secrets["gcp_service_account"]["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
                "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"]
            }
        
        credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {str(e)}")
        return None

def get_or_create_sheet():
    """Get or create worksheet, shared helper function"""
    try:
        client = get_google_sheets_client()
        if not client:
            return None
        
        import os
        sheet_url = os.getenv("GOOGLE_SHEET_URL") or st.secrets.get("google_sheet_url", "")
        if not sheet_url:
            st.error("Google Sheet URL not configured in environment or secrets.")
            return None
            
        spreadsheet = client.open_by_url(sheet_url)
        return spreadsheet.sheet1
        
    except Exception as e:
        st.error(f"Error accessing Google Sheets: {str(e)}")
        return None

def save_reflection_to_sheets(student_name, outcome, scenario=None, choices_made=None, **reflections):
    """Save reflection data to Google Sheets with flexible reflection fields"""
    try:
        sheet = get_or_create_sheet()
        if not sheet:
            return False
        
        # Prepare the row data
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        choices_summary = " → ".join([choice["choice"] for choice in choices_made]) if choices_made else "No choices recorded"
        
        # Start with basic fields
        row_data = [
            timestamp,
            student_name,
            scenario or "Unknown Scenario",
            outcome,
            choices_summary
        ]
        
        # Add reflection responses in order
        reflection_keys = sorted([k for k in reflections.keys() if k.startswith('reflection_')])
        for key in reflection_keys:
            row_data.append(reflections[key])
        
        # Add completion status
        row_data.append("Completed")
        
        # Append the row
        sheet.append_row(row_data)
        return True
        
    except Exception as e:
        st.error(f"Error saving to Google Sheets: {str(e)}")
        return False

def initialize_google_sheet():
    """Initialize the Google Sheet with headers if it's empty."""
    try:
        sheet = get_or_create_sheet()
        if not sheet:
            return False
        
        # Check if headers exist
        if not sheet.get_all_values():
            headers = [
                "Timestamp",
                "Student Name",
                "Scenario Title",
                "Scenario Outcome",
                "Choices Made",
                "Reflection 1",
                "Reflection 2", 
                "Reflection 3",
                "Completion Status"
            ]
            sheet.append_row(headers)
            return True
            
    except Exception as e:
        st.error(f"Error initializing Google Sheet: {str(e)}")
        return False