# Google Sheets API Setup Guide

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Sheets API and Google Drive API

## Step 2: Create Service Account

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **Service Account**
3. Name it "liberty-park-reflections"
4. Create and download the JSON key file
5. Save this file securely - you'll need it for Streamlit secrets

## Step 3: Create Google Sheet

1. Create a new Google Sheet
2. Name it "Liberty Park Reflections"
3. Copy the sheet URL (you'll need this)
4. **Share the sheet** with your service account email (found in the JSON file under `client_email`)
5. Give it **Editor** permissions

## Step 4: Configure Streamlit Secrets

### For Local Development:
Create `.streamlit/secrets.toml`:

```toml
google_sheet_url = "YOUR_GOOGLE_SHEET_URL_HERE"

[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "your-cert-url"
```

### For Streamlit Community Cloud:

1. Go to your app settings on share.streamlit.io
2. Click on **Secrets** tab
3. Add the same content as above
4. Save and redeploy

## Step 5: Test the Integration

The app will automatically:
- Initialize the sheet with headers on first run
- Collect student reflections
- Store data with timestamps
- Mark completion status

## Data Structure

The sheet will contain these columns:
- **Timestamp**: When submitted
- **Student Name**: Student identifier  
- **Scenario Outcome**: failure/compromise/success
- **Reflection 1**: Strategy analysis
- **Reflection 2**: Individual vs group comparison
- **Reflection 3**: What would you do differently
- **Choices Made**: Path taken through scenario
- **Completion Status**: "Completed"

## Security Notes

- Never commit the service account JSON file to Git
- Keep the Google Sheet private (only share with service account)
- The service account has minimal permissions (only Sheets/Drive access)
- Consider using a dedicated Google account for education projects

## Troubleshooting

**"Error connecting to Google Sheets"**
- Check that both Google Sheets API and Drive API are enabled
- Verify the service account JSON is correctly formatted in secrets
- Ensure the sheet is shared with the service account email

**"Google Sheet URL not configured"**
- Make sure `google_sheet_url` is set in your secrets
- Use the full URL from your browser address bar

**"Permission denied"**
- Share the Google Sheet with the service account email
- Give Editor permissions (not just Viewer)