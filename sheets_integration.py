import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import json
from datetime import datetime

def get_google_sheets_client():
    """Initialize Google Sheets client using service account credentials from Streamlit secrets."""
    try:
        # Get credentials from Streamlit secrets
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

def save_reflection_to_sheets(student_name, outcome, reflection_1, reflection_2, reflection_3, choices_made):
    """Save reflection data to Google Sheets."""
    try:
        client = get_google_sheets_client()
        if not client:
            return False
        
        # Open the spreadsheet (you'll need to create this and share it with the service account)
        sheet_url = st.secrets.get("google_sheet_url", "")
        if not sheet_url:
            st.error("Google Sheet URL not configured in secrets.")
            return False
            
        spreadsheet = client.open_by_url(sheet_url)
        worksheet = spreadsheet.sheet1  # Use the first sheet
        
        # Prepare the data row
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        choices_summary = " → ".join([choice["choice"] for choice in choices_made])
        
        row_data = [
            timestamp,
            student_name,
            outcome,
            reflection_1,
            reflection_2,
            reflection_3,
            choices_summary,
            "Completed"
        ]
        
        # Add the row to the sheet
        worksheet.append_row(row_data)
        return True
        
    except Exception as e:
        st.error(f"Error saving to Google Sheets: {str(e)}")
        return False

def initialize_google_sheet():
    """Initialize the Google Sheet with headers if it's empty."""
    try:
        client = get_google_sheets_client()
        if not client:
            return False
        
        sheet_url = st.secrets.get("google_sheet_url", "")
        if not sheet_url:
            return False
            
        spreadsheet = client.open_by_url(sheet_url)
        worksheet = spreadsheet.sheet1
        
        # Check if headers exist
        if not worksheet.get_all_values():
            headers = [
                "Timestamp",
                "Student Name", 
                "Scenario Outcome",
                "Reflection 1: Strategy Analysis",
                "Reflection 2: Individual vs Group Actions",
                "Reflection 3: What Would You Do Differently",
                "Choices Made",
                "Completion Status"
            ]
            worksheet.append_row(headers)
            return True
            
    except Exception as e:
        st.error(f"Error initializing Google Sheet: {str(e)}")
        return False