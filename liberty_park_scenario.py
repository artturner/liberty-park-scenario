import streamlit as st
import json
import os
from sheets_integration import save_reflection_to_sheets, initialize_google_sheet
from pathlib import Path

def load_scenarios():
    """Load all available scenarios from the scenarios folder and legacy data"""
    scenarios = {}
    
    # Legacy Liberty Park scenario
    scenarios['liberty_park'] = {
        'metadata': {
            'title': 'Liberty Park Under Threat',
            'description': 'A community engagement scenario about saving a local park',
            'page_title': 'Liberty Park Scenario',
            'page_icon': '🌳',
            'completion_tracking': True
        },
        'reflection_questions': [
            "Why do you think your chosen strategy led to this outcome?",
            "Compare the effectiveness of individual actions (like your first choice) versus coordinated group actions (your second choice).",
            "In a real-world situation, what is one thing you would do differently after this experience?"
        ],
        'reflection_prompts': [
            "Think about the specific actions you took and their consequences",
            "Consider the impact and reach of different engagement strategies",
            "What did you learn that would change your approach?"
        ],
        'scenes': {
            "1": {
                "title": "Liberty Park Under Threat",
                "description": "A sunny, vibrant image of \"Liberty Park.\" Kids are playing, people are walking dogs, and someone is reading on a bench. In the corner of the screen, a smartphone notification pops up.",
                "narration": "Liberty Park has been the heart of your neighborhood for generations. But a new proposal could change everything.\\n\\nEmail Notification Preview: From: City Council\\nSubject: Public Hearing on Liberty Park Rezoning...",
                "type": "auto_advance",
                "next": "1.1"
            },
            "1.1": {
                "title": "The Council Email",
                "description": "The screen shows a formal email from the city council. Key phrases are highlighted: \"Proposal from LuxCondo Inc.,\" \"rezone for commercial-residential use,\" and \"much-needed city revenue.\"",
                "narration": "You read the email. The city is seriously considering selling the park to a developer to build luxury condos. The public hearing is in four weeks. You feel you have to do something, but what's the first step?",
                "type": "choice",
                "choices": [
                    {"text": "Voice your opinion on social media", "next": "2.1"},
                    {"text": "Start an online petition", "next": "2.2"},
                    {"text": "Email your City Council representative directly", "next": "2.3"}
                ]
            },
            "2.1": {
                "title": "Social Media Response",
                "description": "A mock social media feed. The learner's post (\"The city wants to sell our park! #SaveLibertyPark\") is visible. It gets a few dozen likes and some angry-face emojis. A single comment reads, \"That's terrible! Someone should do something.\"",
                "narration": "Your post gets some attention from friends, but the conversation dies out by the next day. You've raised a little awareness, but it's not clear if anyone with influence has noticed.",
                "type": "auto_advance",
                "next": "3"
            },
            "2.2": {
                "title": "Online Petition",
                "description": "An online petition webpage. The signature count slowly ticks up to a few hundred over several days. A progress bar shows \"25% of goal.\"",
                "narration": "Your petition gains some traction online, with a few hundred signatures from around the city. You've created a list of concerned citizens, but the petition has no legal authority.",
                "type": "auto_advance",
                "next": "3"
            },
            "2.3": {
                "title": "Council Email Response",
                "description": "A polite, but generic, email response from the office of Councilmember Davis. It includes phrases like \"Thank you for your input,\" \"balancing the budget is a difficult task,\" and \"all perspectives will be considered.\"",
                "narration": "You receive a form letter response from your council member's office. Your concern has been noted, but you get the feeling your email is just one of hundreds they receive each week.",
                "type": "auto_advance",
                "next": "3"
            },
            "3": {
                "title": "Mid-Scenario Reflection",
                "description": "Mid-Scenario Reflection Point. The screen shows a local news website with a headline: \"LuxCondo Proposal for Liberty Park Moves to Final Vote.\" The article mentions the proposal is expected to pass easily.",
                "narration": "Your initial efforts made a small splash, but it wasn't enough to change the momentum. The final City Council vote is now just two weeks away. It's clear that a bigger, more organized effort is needed.",
                "type": "choice",
                "choices": [
                    {"text": "Organize a protest for the day of the vote", "next": "4.1"},
                    {"text": "Form a community action group to build a coalition and present an alternative plan", "next": "4.2"},
                    {"text": "It's hopeless. Give up.", "next": "5.3"}
                ]
            },
            "4.1": {
                "title": "Protest Organization",
                "description": "(Protest Path) A montage of images: designing posters, making calls, and a small but energetic crowd gathering outside City Hall on the day of the vote. A local TV news van is present. A reporter approaches you.",
                "narration": "Reporter: \"Can you tell us in 30 seconds why the council should reject this proposal?\"",
                "type": "choice",
                "choices": [
                    {"text": "\"This is about greedy developers destroying our community!\"", "next": "5.1A"},
                    {"text": "\"This park is a vital public good. We urge the council to explore other revenue options that don't sacrifice our green space.\"", "next": "5.1B"}
                ]
            },
            "4.2": {
                "title": "Community Action Group",
                "description": "(Community Action Path) A graphic showing a network of connections being built. Icons representing a local historical society, a youth sports league, and a neighborhood business association are linked to your \"Save Liberty Park Action Group.\"",
                "narration": "You spend the next week making calls and building a coalition of stakeholders. You discover the youth sports league relies on the park's fields, and the local business association fears the construction will hurt their sales. You have allies, but you need a concrete plan.",
                "type": "choice",
                "choices": [
                    {"text": "Focus on highlighting the negative impacts of the LuxCondo plan", "next": "5.2A"},
                    {"text": "Develop a counter-proposal to revitalize the park with a mix of community-funded programs and small business vendors to generate revenue", "next": "5.2B"}
                ]
            },
            "5.1A": {
                "title": "Fiery Protest Coverage",
                "description": "The 6 o'clock news plays. The news anchor describes the protest as \"fiery but divisive.\" Councilmember Davis is interviewed and says, \"We can't be swayed by angry rhetoric; we have to make tough financial choices.\"",
                "narration": "Your passionate message made the news, but it may have backfired by alienating potential allies on the council. The vote is about to happen.",
                "type": "auto_advance",
                "next": "5.4"
            },
            "5.1B": {
                "title": "Professional Protest Coverage",
                "description": "The 6 o'clock news plays. Your thoughtful soundbite is featured. The news anchor says, \"Protestors urged the council to find a balanced solution.\" Councilmember Davis looks thoughtful in a brief clip.",
                "narration": "Your professional message earned respect and put public pressure on the council to reconsider. The vote is about to happen, and the outcome is uncertain.",
                "type": "auto_advance",
                "next": "5.4"
            },
            "5.2A": {
                "title": "Opposition Presentation",
                "description": "At the council meeting, your group presents data on the negative impacts. The developer counters, stating your group has offered \"no viable solutions\" to the city's budget crisis. Some council members look torn.",
                "narration": "Your presentation was compelling, and you successfully highlighted the downsides of the developer's plan. However, you haven't solved the council's underlying financial problem. The vote is next.",
                "type": "auto_advance",
                "next": "5.4"
            },
            "5.2B": {
                "title": "Counter-Proposal Presentation",
                "description": "At the council meeting, your group presents your counter-proposal. You show a budget for a \"Liberty Park Revitalization Fund\" and letters of support from your coalition partners. Councilmember Davis looks impressed.",
                "narration": "Your counter-proposal has changed the entire debate. You've given the council a politically viable alternative to simply selling the park. They are impressed. The vote is next.",
                "type": "auto_advance",
                "next": "5.5"
            },
            "5.3": {
                "title": "End State: Failure",
                "description": "(End State: Failure) The screen shows an image of the park, which fades to a picture of a construction site with a \"Future Home of LuxCondo\" sign.",
                "narration": "Without organized opposition, the developer's proposal passed unanimously. Construction on the new condos will begin next month. Liberty Park is gone forever.",
                "type": "end",
                "outcome": "failure",
                "outcome_message": "Scenario Complete - Park Lost"
            },
            "5.4": {
                "title": "End State: Compromise",
                "description": "(End State: Compromise) The screen shows a news headline: \"Council Reaches Compromise on Liberty Park: Smaller Development, Public Green Space Preserved.\"",
                "narration": "Your public pressure campaign worked. The council was unwilling to ignore the protest and sent the developer back to the drawing board. It's not a total victory, but you saved half of the park.",
                "type": "end",
                "outcome": "compromise",
                "outcome_message": "Scenario Complete - Partial Success"
            },
            "5.5": {
                "title": "End State: Optimal Outcome",
                "description": "(End State: Optimal Outcome) The screen shows a news headline: \"City Council Rejects LuxCondo, Approves Community-Led Revitalization Plan for Liberty Park.\" The image shows a celebration in the park.",
                "narration": "Your well-researched and coalition-backed plan was too good to ignore. The council voted to support your community proposal. Liberty Park is not only saved—it's going to be better than ever.",
                "type": "end",
                "outcome": "success",
                "outcome_message": "Scenario Complete - Full Victory!"
            }
        }
    }
    
    # Load scenarios from scenarios folder
    scenarios_dir = Path("scenarios")
    if scenarios_dir.exists():
        for scenario_folder in scenarios_dir.iterdir():
            if scenario_folder.is_dir():
                config_file = scenario_folder / "config.json"
                if config_file.exists():
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            scenario_data = json.load(f)
                            scenarios[scenario_folder.name] = scenario_data
                    except Exception as e:
                        st.error(f"Error loading scenario {scenario_folder.name}: {e}")
    
    return scenarios

def initialize_session_state():
    if 'selected_scenario' not in st.session_state:
        st.session_state.selected_scenario = None
    if 'current_scene' not in st.session_state:
        st.session_state.current_scene = "1"
    if 'scene_history' not in st.session_state:
        st.session_state.scene_history = []
    if 'choices_made' not in st.session_state:
        st.session_state.choices_made = []
    if 'scenario_variables' not in st.session_state:
        st.session_state.scenario_variables = {}

def display_scene(scene_id, scenario_data, scenario_key):
    scene = scenario_data['scenes'][scene_id]
    
    # Display title
    st.title(scene["title"])
    
    # Display image if available, otherwise fall back to text description
    if 'image' in scene:
        if scenario_key == 'liberty_park':
            image_path = f"images/scene_{scene_id}.png"
        else:
            image_path = f"scenarios/{scenario_key}/images/{scene['image']}"
        
        if os.path.exists(image_path):
            st.image(image_path, use_container_width=True)
        elif scene.get("description"):
            st.info(scene["description"])
    elif scene.get("description"):
        st.info(scene["description"])
    
    # Display narration
    st.markdown(scene['narration'])
    
    return scene

def evaluate_condition(condition, variables):
    """Evaluate a condition string using scenario variables"""
    try:
        # Replace variable names in condition with their values
        for var_name, var_value in variables.items():
            condition = condition.replace(var_name, str(var_value))
        return eval(condition)
    except:
        return False

def handle_choice(scene, scene_id, scenario_data, scenario_key):
    if scene["type"] == "choice":
        st.markdown("---")
        st.subheader("What will you do?")
        
        for i, choice in enumerate(scene["choices"]):
            if st.button(f"{chr(65+i)}. {choice['text']}", key=f"choice_{scene_id}_{i}"):
                # Apply effects if present
                if 'effects' in choice:
                    for var_name, effect_value in choice['effects'].items():
                        if var_name in st.session_state.scenario_variables:
                            st.session_state.scenario_variables[var_name] += effect_value
                        else:
                            st.session_state.scenario_variables[var_name] = effect_value
                
                st.session_state.choices_made.append({
                    "scene": scene_id,
                    "choice": choice["text"],
                    "next": choice["next"]
                })
                st.session_state.scene_history.append(st.session_state.current_scene)
                st.session_state.current_scene = choice["next"]
                st.rerun()
    
    elif scene["type"] == "conditional":
        # Handle conditional branching
        next_scene = scene.get("default", "1")
        
        if 'conditions' in scene:
            for condition_obj in scene['conditions']:
                if evaluate_condition(condition_obj['condition'], st.session_state.scenario_variables):
                    next_scene = condition_obj['next']
                    break
        
        st.session_state.scene_history.append(st.session_state.current_scene)
        st.session_state.current_scene = next_scene
        st.rerun()
    
    elif scene["type"] == "auto_advance":
        st.markdown("---")
        if st.button("Continue", key=f"continue_{scene_id}"):
            st.session_state.scene_history.append(st.session_state.current_scene)
            st.session_state.current_scene = scene["next"]
            st.rerun()
    
    elif scene["type"] == "end":
        st.markdown("---")
        outcome_colors = {
            "failure": "🔴",
            "compromise": "🟡", 
            "success": "🟢"
        }
        
        outcome = scene["outcome"]
        outcome_message = scene.get("outcome_message", f"Scenario Complete - {outcome.title()}")
        st.markdown(f"### {outcome_colors[outcome]} {outcome_message}")
        
        # Add reflection form
        if scenario_data['metadata'].get('completion_tracking', False):
            st.markdown("---")
            st.subheader("📝 Complete Your Reflection")
            
            # Check if reflection already submitted
            reflection_key = f"reflection_submitted_{scenario_key}_{scene_id}"
            if st.session_state.get(reflection_key, False):
                st.success("✅ Reflection submitted successfully!")
                st.info(f"Thank you for completing the {scenario_data['metadata']['title']} scenario and sharing your thoughts!")
            else:
                # Student name input
                student_name = st.text_input(
                    "Student Name:", 
                    key=f"student_name_{scenario_key}_{scene_id}",
                    help="Enter your name to receive completion credit"
                )
                
                # Reflection questions
                st.markdown("**Please reflect on your experience:**")
                
                questions = scenario_data.get('reflection_questions', [])
                prompts = scenario_data.get('reflection_prompts', [])
                
                reflections = []
                for i, question in enumerate(questions):
                    help_text = prompts[i] if i < len(prompts) else None
                    reflection = st.text_area(
                        f"{i+1}. {question}",
                        key=f"reflection_{i+1}_{scenario_key}_{scene_id}",
                        height=100,
                        help=help_text
                    )
                    reflections.append(reflection)
                
                # Submit button
                if st.button("Submit Reflection", key=f"submit_reflection_{scenario_key}_{scene_id}", type="primary"):
                    if student_name and all(reflections):
                        # Save to Google Sheets with dynamic reflection data
                        reflection_data = {
                            "student_name": student_name,
                            "scenario": scenario_data['metadata']['title'],
                            "outcome": outcome,
                            "choices_made": st.session_state.choices_made
                        }
                        
                        # Add individual reflections
                        for i, reflection in enumerate(reflections):
                            reflection_data[f"reflection_{i+1}"] = reflection
                        
                        success = save_reflection_to_sheets(**reflection_data)
                        
                        if success:
                            st.session_state[reflection_key] = True
                            st.rerun()
                        else:
                            st.error("There was an error submitting your reflection. Please try again.")
                    else:
                        st.error("Please fill in all fields before submitting.")
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start Over", key="restart"):
                st.session_state.current_scene = "1"
                st.session_state.scene_history = []
                st.session_state.choices_made = []
                st.session_state.scenario_variables = scenario_data.get('variables', {}).copy()
                st.rerun()
        with col2:
            if st.button("Choose Different Scenario", key="change_scenario"):
                st.session_state.selected_scenario = None
                st.session_state.current_scene = "1"
                st.session_state.scene_history = []
                st.session_state.choices_made = []
                st.session_state.scenario_variables = {}
                st.rerun()

def display_progress():
    if st.session_state.choices_made:
        with st.sidebar:
            st.subheader("Your Journey")
            for i, choice in enumerate(st.session_state.choices_made):
                st.write(f"**Step {i+1}:** {choice['choice']}")

def scenario_selection():
    """Display scenario selection interface"""
    st.title("🎦 Interactive Learning Scenarios")
    st.markdown("Choose a scenario to begin your learning experience:")
    
    scenarios = load_scenarios()
    
    cols = st.columns(len(scenarios))
    
    for i, (scenario_key, scenario_data) in enumerate(scenarios.items()):
        with cols[i]:
            metadata = scenario_data['metadata']
            st.markdown(f"### {metadata['page_icon']} {metadata['title']}")
            st.write(metadata['description'])
            
            if st.button(f"Start {metadata['title']}", key=f"select_{scenario_key}"):
                st.session_state.selected_scenario = scenario_key
                st.session_state.current_scene = "1"
                st.session_state.scene_history = []
                st.session_state.choices_made = []
                st.session_state.scenario_variables = scenario_data.get('variables', {}).copy()
                st.rerun()

def main():
    initialize_session_state()
    
    # Load scenarios
    scenarios = load_scenarios()
    
    # If no scenario selected, show selection interface
    if not st.session_state.selected_scenario:
        scenario_selection()
        return
    
    # Get current scenario data
    scenario_key = st.session_state.selected_scenario
    if scenario_key not in scenarios:
        st.error("Selected scenario not found!")
        st.session_state.selected_scenario = None
        st.rerun()
        return
    
    scenario_data = scenarios[scenario_key]
    metadata = scenario_data['metadata']
    
    # Set page config based on scenario
    st.set_page_config(
        page_title=metadata['page_title'], 
        page_icon=metadata['page_icon'],
        layout="wide"
    )
    
    # Initialize Google Sheets on first run if completion tracking enabled
    if metadata.get('completion_tracking', False):
        initialize_google_sheet()
    
    # Main content
    current_scene_id = st.session_state.current_scene
    
    # Check if scene exists
    if current_scene_id not in scenario_data['scenes']:
        st.error(f"Scene '{current_scene_id}' not found in scenario!")
        return
    
    scene = display_scene(current_scene_id, scenario_data, scenario_key)
    handle_choice(scene, current_scene_id, scenario_data, scenario_key)
    
    # Sidebar progress
    display_progress()
    
    # Navigation controls
    with st.sidebar:
        st.markdown("---")
        st.subheader(f"{metadata['page_icon']} {metadata['title']}")
        
        if st.session_state.scene_history and st.button("Go Back"):
            previous_scene = st.session_state.scene_history.pop()
            st.session_state.current_scene = previous_scene
            if st.session_state.choices_made:
                st.session_state.choices_made.pop()
            st.rerun()
        
        if st.button("Restart Scenario"):
            st.session_state.current_scene = "1"
            st.session_state.scene_history = []
            st.session_state.choices_made = []
            st.session_state.scenario_variables = scenario_data.get('variables', {}).copy()
            st.rerun()
            
        if st.button("Choose Different Scenario"):
            st.session_state.selected_scenario = None
            st.rerun()

if __name__ == "__main__":
    main()