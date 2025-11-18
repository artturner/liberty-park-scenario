"""
Generate grade CSV files from Google Sheets student activity data.

This program:
1. Reads student activity from a Google Sheet
2. Matches student names to roster to get OrgDefinedId
3. Creates separate CSV files for each unique scenario completed
4. Each CSV contains: OrgDefinedId, scenario name, grade (100), EOL indicator
"""

import gspread
from google.oauth2.service_account import Credentials
import csv
import json
import os
from datetime import datetime
from difflib import get_close_matches
from pathlib import Path


def get_google_sheets_client():
    """Initialize Google Sheets client using service account credentials."""
    try:
        credentials_dict = None

        # Check for credential file locations
        secret_file_paths = [
            "/etc/secrets/google_credentials.json",
            "google_credentials.json",
        ]

        for file_path in secret_file_paths:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    credentials_dict = json.load(f)
                print(f"Using credentials from: {file_path}")
                break

        # Fallback to Streamlit secrets if available
        if not credentials_dict:
            try:
                import streamlit as st
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
                print("Using credentials from Streamlit secrets")
            except (ImportError, KeyError, FileNotFoundError):
                pass

        if not credentials_dict:
            raise FileNotFoundError(
                "Google credentials not found. Please ensure one of the following:\n"
                "  1. google_credentials.json file exists in the project directory\n"
                "  2. Streamlit secrets are configured (.streamlit/secrets.toml)\n"
                "  3. Credentials file exists at /etc/secrets/google_credentials.json"
            )

        credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )

        return gspread.authorize(credentials)
    except Exception as e:
        print(f"Error connecting to Google Sheets: {str(e)}")
        return None


def load_roster(roster_file="fall25roster.csv"):
    """Load student roster and create lookup dictionaries."""
    roster = {}
    roster_by_lastname_firstname = {}
    roster_by_firstname_lastname = {}
    all_names = []

    with open(roster_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            org_id = row['OrgDefinedId'].strip()
            last_name = row['Last Name'].strip()
            first_name = row['First Name'].strip()

            # Create different name format lookups
            lastname_firstname = f"{last_name}, {first_name}"
            firstname_lastname = f"{first_name} {last_name}"

            roster_by_lastname_firstname[lastname_firstname.lower()] = org_id
            roster_by_firstname_lastname[firstname_lastname.lower()] = org_id

            # Store for fuzzy matching
            all_names.append((lastname_firstname, org_id))
            all_names.append((firstname_lastname, org_id))

    return roster_by_lastname_firstname, roster_by_firstname_lastname, all_names


def match_student_name(student_name, cutoff_date, entry_date,
                      roster_lastname_first, roster_firstname_last, all_names):
    """
    Match student name to roster entry.

    Args:
        student_name: Name from Google Sheet
        cutoff_date: Date when format changed (2025-10-09)
        entry_date: Date of the sheet entry
        roster_lastname_first: Dict with "LastName, FirstName" format
        roster_firstname_last: Dict with "FirstName LastName" format
        all_names: List of all name variations for fuzzy matching

    Returns:
        OrgDefinedId or None if no match found
    """
    student_name_lower = student_name.strip().lower()

    # After cutoff date, use exact "LastName, FirstName" matching
    if entry_date >= cutoff_date:
        return roster_lastname_first.get(student_name_lower)

    # Before cutoff date, try multiple approaches
    # 1. Try exact match with both formats
    if student_name_lower in roster_lastname_first:
        return roster_lastname_first[student_name_lower]
    if student_name_lower in roster_firstname_last:
        return roster_firstname_last[student_name_lower]

    # 2. Try fuzzy matching
    name_strings = [name for name, _ in all_names]
    matches = get_close_matches(student_name, name_strings, n=1, cutoff=0.85)
    if matches:
        # Find the org_id for the matched name
        for name, org_id in all_names:
            if name == matches[0]:
                return org_id

    return None


def read_google_sheet(sheet_url):
    """Read all student activity data from Google Sheet."""
    client = get_google_sheets_client()
    if not client:
        return None

    try:
        spreadsheet = client.open_by_url(sheet_url)
        sheet = spreadsheet.sheet1

        # Get all values
        all_values = sheet.get_all_values()
        if not all_values:
            print("Google Sheet is empty")
            return None

        # Expected headers based on sheets_integration.py
        expected_headers = [
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

        # Check if first row contains headers or data
        # If first cell looks like a timestamp, there are no headers
        first_cell = all_values[0][0] if all_values and all_values[0] else ""
        has_headers = not (first_cell and ("-" in first_cell or "/" in first_cell) and ":" in first_cell)

        if has_headers:
            # Standard case: first row is headers
            print("   Detected header row in sheet")
            headers = all_values[0]
            data_rows = all_values[1:]
        else:
            # No headers: use expected headers and treat all rows as data
            print("   No headers detected - using expected column order")
            headers = expected_headers
            data_rows = all_values

        # Parse records
        records = []
        for row in data_rows:
            if row and any(row):  # Skip completely empty rows
                # Pad row if needed
                while len(row) < len(headers):
                    row.append("")
                record = dict(zip(headers, row))
                records.append(record)

        return records
    except Exception as e:
        print(f"Error reading Google Sheet: {str(e)}")
        return None


def generate_grade_csvs(records, roster_lastname_first, roster_firstname_last, all_names, output_dir="grade_outputs", debug=False):
    """Generate grade CSV files for each unique scenario."""
    Path(output_dir).mkdir(exist_ok=True)

    cutoff_date = datetime(2025, 10, 9)

    # Group completions by scenario
    scenario_completions = {}  # scenario_name -> list of (org_id, student_name)
    unmatched_students = []

    if debug:
        print("\n[DEBUG] First few records:")
        for i, record in enumerate(records[:3]):
            print(f"\nRecord {i+1}:")
            for key, value in record.items():
                print(f"  {key}: {value}")

    # Track statistics
    status_counts = {}
    completed_count = 0

    for record in records:
        student_name = record.get('Student Name', '').strip()
        scenario_name = record.get('Scenario Title', '').strip()
        completion_status = record.get('Completion Status', '').strip()
        timestamp_str = record.get('Timestamp', '').strip()

        # Track statuses
        status_key = completion_status if completion_status else '(empty)'
        status_counts[status_key] = status_counts.get(status_key, 0) + 1

        # Skip if not completed or missing data
        if completion_status.lower() != 'completed' or not student_name or not scenario_name:
            continue

        completed_count += 1

        # Parse timestamp
        try:
            entry_date = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        except:
            # Default to before cutoff if can't parse (use fuzzy matching)
            entry_date = datetime(2025, 1, 1)

        # Match student to roster
        org_id = match_student_name(
            student_name, cutoff_date, entry_date,
            roster_lastname_first, roster_firstname_last, all_names
        )

        if org_id:
            if scenario_name not in scenario_completions:
                scenario_completions[scenario_name] = []

            # Avoid duplicates
            if org_id not in [oid for oid, _ in scenario_completions[scenario_name]]:
                scenario_completions[scenario_name].append((org_id, student_name))
        else:
            unmatched_students.append((student_name, scenario_name, timestamp_str))

    # Generate CSV for each scenario
    csv_files_created = []
    for scenario_name, completions in scenario_completions.items():
        # Create safe filename from scenario name
        safe_filename = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in scenario_name)
        safe_filename = safe_filename.replace(' ', '_')
        csv_filename = f"{output_dir}/{safe_filename}_grades.csv"

        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Write header (append "Points Grade" to scenario name)
            writer.writerow(['OrgDefinedId', f'{scenario_name} Points Grade', 'End-of-Line Indicator'])

            # Write student grades
            for org_id, student_name in completions:
                # Strip the "#" from OrgDefinedId
                clean_org_id = org_id.lstrip('#')
                writer.writerow([clean_org_id, '20', '#'])

        csv_files_created.append((csv_filename, len(completions)))
        print(f"Created: {csv_filename} ({len(completions)} students)")

    # Print statistics
    if debug:
        print(f"\n[DEBUG] Statistics:")
        print(f"  Total records processed: {len(records)}")
        print(f"  Completion Status breakdown:")
        for status, count in status_counts.items():
            print(f"    '{status}': {count}")
        print(f"  Records with 'Completed' status: {completed_count}")
        print(f"  Successfully matched students: {sum(len(comps) for comps in scenario_completions.values())}")
        print(f"  Unmatched students: {len(unmatched_students)}")

    # Report unmatched students
    if unmatched_students:
        print(f"\n[WARNING] {len(unmatched_students)} entries could not be matched to roster:")
        for student_name, scenario, timestamp in unmatched_students:
            print(f"  - {student_name} ({scenario}) at {timestamp}")

    return csv_files_created


def main():
    """Main function to generate grade CSV files."""
    print("Grade CSV Generator")
    print("=" * 60)

    # Get Google Sheet URL from environment variable
    sheet_url = os.getenv("GOOGLE_SHEET_URL")
    if not sheet_url:
        print("Error: GOOGLE_SHEET_URL environment variable not set")
        print("Please set it with: export GOOGLE_SHEET_URL='your_sheet_url'")
        return

    # Load roster
    print("\n1. Loading student roster...")
    roster_lastname_first, roster_firstname_last, all_names = load_roster()
    print(f"   Loaded {len(roster_lastname_first)} students from roster")

    # Read Google Sheet
    print("\n2. Reading Google Sheet data...")
    records = read_google_sheet(sheet_url)
    if not records:
        print("   Error: Could not read Google Sheet")
        return
    print(f"   Found {len(records)} total records")

    # Generate grade CSVs
    print("\n3. Generating grade CSV files...")
    csv_files = generate_grade_csvs(records, roster_lastname_first, roster_firstname_last, all_names, debug=True)

    print("\n" + "=" * 60)
    print(f"[SUCCESS] Created {len(csv_files)} grade CSV files")
    print("\nSummary:")
    for filename, count in csv_files:
        print(f"  - {filename}: {count} students")


if __name__ == "__main__":
    main()
