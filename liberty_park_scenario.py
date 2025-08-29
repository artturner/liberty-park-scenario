import streamlit as st
import json
import os
from sheets_integration import save_reflection_to_sheets, initialize_google_sheet
from pathlib import Path

def load_scenarios():
    """Load all available scenarios from the scenarios folder and legacy data"""
    scenarios = {}
    
    
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
        
        st.markdown("---")
        if st.button("Continue to Outcome", key=f"conditional_{scene_id}"):
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