# Grade CSV Generation from Google Sheets

This tool generates grade import CSV files from student scenario completion data stored in Google Sheets.

## Overview

The `generate_grades.py` script:
1. Reads student activity from your Google Sheet
2. Matches student names to `fall25roster.csv` to obtain `OrgDefinedId`
3. Creates separate CSV files for each unique scenario
4. Each CSV contains students who completed that scenario with a grade of 100

## Setup

### Prerequisites

Install required Python packages:
```bash
pip install gspread google-auth
```

### Configuration

1. **Google Credentials**: The script will automatically use credentials from one of these sources (in order):
   - `google_credentials.json` in the project directory
   - `/etc/secrets/google_credentials.json` (for deployed environments)
   - Streamlit secrets (`.streamlit/secrets.toml`) - **same as your scenario engine uses**

   If you're already running scenarios successfully, the credentials are already configured!

2. **Set Google Sheet URL** as an environment variable:
   ```bash
   # Windows (Command Prompt)
   set GOOGLE_SHEET_URL=https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit

   # Windows (PowerShell)
   $env:GOOGLE_SHEET_URL="https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"

   # Linux/Mac
   export GOOGLE_SHEET_URL="https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
   ```

## Usage

Run the script:
```bash
python generate_grades.py
```

## Output

The script creates a `grade_outputs/` directory containing CSV files for each scenario:

### Example Output File: `Liberty_Park_Scenario_grades.csv`
```csv
OrgDefinedId,Liberty Park Scenario,End-of-Line Indicator
#50434962,100,#
#50435552,100,#
#50426581,100,#
```

### CSV Format

Each generated CSV contains:
- **OrgDefinedId**: Student ID from roster (with # prefix)
- **Scenario Name**: Used as the column header (grade item name)
- **Grade**: Always 100 for completed scenarios
- **End-of-Line Indicator**: `#` symbol

## Name Matching Logic

The script uses intelligent name matching:

- **Before October 9, 2025**: Uses fuzzy matching to handle free-form names
  - Tries exact match with "LastName, FirstName" format
  - Tries exact match with "FirstName LastName" format
  - Falls back to fuzzy matching (85% similarity threshold)

- **After October 9, 2025**: Uses exact "LastName, FirstName" matching only

## Troubleshooting

### Unmatched Students

If students cannot be matched to the roster, the script will report:
```
⚠️  Warning: 3 entries could not be matched to roster:
  - John Doe (Liberty Park Scenario) at 2025-09-15 14:30:00
```

**Common causes:**
- Name spelling differences between Google Sheet and roster
- Student not in the roster file
- Unusual name formatting

**Solutions:**
- Manually verify the student name in both files
- Update the roster if student is missing
- For pre-October entries, the fuzzy matcher may need name adjustments

### No CSV Files Generated

If no files are created:
- Verify Google Sheet has "Completed" entries
- Check that `Completion Status` column contains "Completed" (case-insensitive)
- Ensure student names exist in the roster

### Google Sheets Connection Issues

If you see credential errors:
- Verify `google_credentials.json` exists and is valid
- Ensure the service account has access to your Google Sheet
- Check that `GOOGLE_SHEET_URL` environment variable is set correctly

## Files

- **Input Files:**
  - `fall25roster.csv` - Student roster with OrgDefinedId
  - Google Sheet (URL via environment variable) - Student completion data
  - `google_credentials.json` - Google service account credentials

- **Output Files:**
  - `grade_outputs/[Scenario_Name]_grades.csv` - One file per unique scenario

## Expected Google Sheet Format

The script expects these columns in your Google Sheet:
- `Timestamp` - When the scenario was completed
- `Student Name` - Student's name
- `Scenario Title` - Name of the scenario
- `Completion Status` - Must contain "Completed"

(Additional columns like Scenario Outcome, Choices Made, Reflections are ignored)
