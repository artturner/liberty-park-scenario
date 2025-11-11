# Liberty Park Scenario Engine

An interactive educational platform built with Streamlit that delivers branching narrative scenarios to teach civic engagement, constitutional law, American history, and political decision-making through realistic, consequence-rich simulations.

## Overview

The Liberty Park Scenario Engine is a flexible, data-driven platform that enables students to experience complex decision-making in historical and civic contexts. Through interactive branching narratives, students make choices that shape their learning journey and explore the real-world consequences of political, legal, and civic decisions.

The platform includes six complete scenarios covering topics from constitutional compromises to civil rights legislation, each with multiple possible outcomes based on student choices.

## Features

### Core Functionality
- **Scenario Engine**: Flexible state machine that executes JSON-defined branching narratives
- **Variable-Driven Logic**: Tracks player alignment and choices using dynamic variables
- **Conditional Branching**: Sophisticated branching based on accumulated choices and state
- **Multiple Ending Types**: Success, failure, and compromise outcomes based on player decisions
- **Student Tracking**: Integration with Google Sheets for completion tracking and reflection collection

### User Experience
- **Multi-Scenario Selector**: Choose from six different scenarios
- **Progress Tracking**: Sidebar displays journey and choices made
- **Navigation Controls**: Back button, restart, and scenario switching
- **Rich Media**: Images for every scene with text fallbacks
- **Reflection Questions**: Customizable reflection prompts for each scenario

### Educational Features
- **Student Roster Integration**: Autocomplete for student names from CSV
- **Reflection Collection**: Captures student responses with customizable questions
- **Automatic Data Export**: Saves completions and reflections to Google Sheets
- **Progress Visualization**: Shows decision tree as students navigate

## Tech Stack

- **Streamlit** (>=1.48.0) - Web framework
- **Python 3.x** - Core language
- **pandas** (>=1.4.0) - Data processing
- **gspread** (>=5.0.0) - Google Sheets integration
- **google-auth** (>=2.0.0) - Authentication

## Project Structure

```
liberty-park/
├── app.py                         # Multi-scenario launcher
├── scenario_engine.py             # Core scenario execution engine
├── sheets_integration.py          # Google Sheets data collection
├── roster_loader.py               # Student roster CSV handling
├──
├── scenarios/                     # Scenario definitions
│   ├── liberty_park/              # Civic engagement scenario
│   ├── probable_cause/            # Fourth Amendment law
│   ├── convention_1787/           # Constitutional Convention
│   ├── party_realignment/         # 1960s Civil Rights Act
│   ├── rio_grande/                # Immigration policy
│   └── cherokee_nation/           # Indian Removal Act
│       ├── config.json            # Scenario definition
│       └── images/                # Scene images
├──
├── requirements.txt               # Python dependencies
├── fall25roster.csv              # Student roster
├── render.yaml                    # Deployment configuration
└── GOOGLE_SHEETS_SETUP.md        # Integration guide
```

## Available Scenarios

| Scenario | Topic | Learning Objectives |
|----------|-------|---------------------|
| **Liberty Park** | Civic Engagement | Community organizing, coalition building, local government |
| **Probable Cause** | Fourth Amendment Law | Search & seizure, constitutional rights, legal reasoning |
| **Convention 1787** | Constitutional Compromise | Federalism, separation of powers, political negotiation |
| **Party Realignment** | 1960s Civil Rights | Party politics, civil rights legislation, political realignment |
| **Rio Grande** | Immigration Policy | Multi-stakeholder decision-making, policy trade-offs |
| **Cherokee Nation** | Indian Removal Act | Sovereignty, Worcester v. Georgia, executive power limits |

## How the Scenario Engine Works

### Scenario Definition

Each scenario is defined by a `config.json` file that specifies:

- **Metadata**: Title, description, author, version
- **Variables**: Dynamic state tracking (e.g., faction favor scores)
- **Scenes**: Story nodes with narration, images, and choices
- **Reflection Questions**: Post-scenario student reflections

### Scene Types

The engine supports four scene types:

1. **Choice Scenes**: Present multiple options with different consequences
2. **Auto-Advance Scenes**: Linear progression with "Continue" button
3. **Conditional Scenes**: Branching based on accumulated variable state
4. **End Scenes**: Scenario conclusion with reflection form

### Variable System

Scenarios can track numeric variables that change based on player choices:

```json
"choices": [
  {
    "text": "Support the large state plan",
    "next": "3",
    "effects": {"LargeStateFavor": 1, "SmallStateFavor": -1}
  }
]
```

### Conditional Branching

Scenes can branch based on variable conditions:

```json
"conditions": [
  {
    "condition": "LargeStateFavor >= 2 && SouthernStateFavor < -1",
    "next": "ending_failure"
  },
  {
    "condition": "LargeStateFavor >= -2 && LargeStateFavor <= 2",
    "next": "ending_compromise"
  }
],
"default": "ending_success"
```

## Setup Instructions

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd liberty-park
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run app.py
   ```

4. **Access in browser**
   - The app will open automatically at `http://localhost:8501`

### Google Sheets Integration (Optional)

For student completion tracking:

1. Follow the setup guide in `GOOGLE_SHEETS_SETUP.md`
2. Create a Google Cloud service account
3. Share your target Google Sheet with the service account email
4. Add credentials to `.streamlit/secrets.toml`:
   ```toml
   [google_credentials]
   type = "service_account"
   project_id = "your-project-id"
   # ... other credentials
   ```
5. Set the `GOOGLE_SHEET_URL` environment variable

### Student Roster (Optional)

To enable student name autocomplete:

1. Create a CSV file with student names (e.g., `fall25roster.csv`)
2. Format: First column = Last Name, Second column = First Name
3. Update `roster_loader.py` if using a different filename

## Deployment

### Render

The application is configured for deployment on Render:

1. Connect your repository to Render
2. Render will use `render.yaml` for configuration
3. Set environment variables:
   - `GOOGLE_SHEET_URL` (if using tracking)
   - Add Google credentials as secret file or environment variable

### Streamlit Community Cloud

Alternative deployment option:

1. Connect repository to Streamlit Community Cloud
2. Configure secrets in the Streamlit dashboard
3. App will deploy automatically

## Creating New Scenarios

To add a new scenario:

1. **Create scenario directory**
   ```bash
   mkdir scenarios/your_scenario_name
   mkdir scenarios/your_scenario_name/images
   ```

2. **Create config.json**
   - Use an existing scenario as a template
   - Define metadata, variables, scenes, and reflections

3. **Add images**
   - Name images: `scene_1.png`, `scene_2.png`, etc.
   - Place in the `images/` directory

4. **Update app.py**
   - Add scenario to the selector UI

### Config.json Template

```json
{
  "metadata": {
    "title": "Your Scenario Title",
    "description": "Brief description for selector",
    "page_title": "Browser Title",
    "page_icon": "🎯",
    "author": "Your Name",
    "version": "1.0",
    "completion_tracking": true
  },
  "variables": {
    "VariableName": 0
  },
  "reflection_questions": [
    "Question 1?",
    "Question 2?",
    "Question 3?"
  ],
  "reflection_prompts": [
    "Guidance for question 1",
    "Guidance for question 2",
    "Guidance for question 3"
  ],
  "scenes": {
    "1": {
      "title": "Scene Title",
      "image": "scene_1.png",
      "description": "Text fallback",
      "narration": "Story text with **markdown**",
      "type": "choice",
      "choices": [
        {
          "text": "Option A",
          "next": "2",
          "effects": {"VariableName": 1}
        },
        {
          "text": "Option B",
          "next": "3"
        }
      ]
    }
  }
}
```

## Usage

### For Students

1. Visit the application URL
2. Select a scenario from the menu
3. Read each scene and make choices
4. Navigate using the buttons:
   - **Choice buttons**: Make your decision
   - **Back**: Return to previous scene
   - **Restart**: Start the scenario over
5. At the end, complete the reflection questions
6. Submit your responses

### For Educators

1. Review scenario content and learning objectives
2. Assign specific scenarios to students
3. Monitor completion via Google Sheets
4. Use reflection responses for class discussion
5. Create custom scenarios using the JSON format

## Contributing

To contribute new scenarios or improvements:

1. Fork the repository
2. Create a feature branch
3. Add your scenario or make changes
4. Test thoroughly
5. Submit a pull request

## License

[Add your license information here]

## Support

For setup help, see `GOOGLE_SHEETS_SETUP.md`

For issues or questions, please open a GitHub issue.

## Acknowledgments

Built with Streamlit for educational purposes in civic engagement and American history education.
