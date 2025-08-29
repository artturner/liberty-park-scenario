import streamlit as st
import json
import os
from pathlib import Path
from sheets_integration import save_reflection_to_sheets, initialize_google_sheet

class ScenarioEngine:
    def __init__(self, scenario_path):
        self.scenario_path = Path(scenario_path)
        self.config = self.load_config()
        self.metadata = self.config.get("metadata", {})
        self.scenes = self.config.get("scenes", {})
        self.reflection_questions = self.config.get("reflection_questions", [])
        self.reflection_prompts = self.config.get("reflection_prompts", [])
    
    def load_config(self):
        config_file = self.scenario_path / "config.json"
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")
        
        with open(config_file, 'r') as f:
            return json.load(f)
    
    def get_image_path(self, scene_id):
        return self.scenario_path / "images" / f"scene_{scene_id}.png"
    
    def initialize_session_state(self):
        if 'current_scene' not in st.session_state:
            st.session_state.current_scene = "1"
        if 'scene_history' not in st.session_state:
            st.session_state.scene_history = []
        if 'choices_made' not in st.session_state:
            st.session_state.choices_made = []
    
    def display_scene(self, scene_id):
        if scene_id not in self.scenes:
            st.error(f"Scene '{scene_id}' not found in scenario configuration")
            return None
            
        scene = self.scenes[scene_id]
        
        # Display title
        st.title(scene["title"])
        
        # Display image if available, otherwise fall back to text description
        image_path = self.get_image_path(scene_id)
        if image_path.exists():
            st.image(str(image_path), use_container_width=True)
        elif scene.get("description"):
            st.info(scene["description"])
        
        # Display narration
        st.markdown(scene.get('narration', ''))
        
        return scene
    
    def handle_choice(self, scene, scene_id):
        if scene["type"] == "choice":
            st.markdown("---")
            st.subheader("What will you do?")
            
            for i, choice in enumerate(scene["choices"]):
                if st.button(f"{chr(65+i)}. {choice['text']}", key=f"choice_{scene_id}_{i}"):
                    st.session_state.choices_made.append({
                        "scene": scene_id,
                        "choice": choice["text"],
                        "next": choice["next"]
                    })
                    st.session_state.scene_history.append(st.session_state.current_scene)
                    st.session_state.current_scene = choice["next"]
                    st.rerun()
        
        elif scene["type"] == "auto_advance":
            st.markdown("---")
            if st.button("Continue", key=f"continue_{scene_id}"):
                st.session_state.scene_history.append(st.session_state.current_scene)
                st.session_state.current_scene = scene["next"]
                st.rerun()
        
        elif scene["type"] == "end":
            self.handle_end_scene(scene, scene_id)
    
    def handle_end_scene(self, scene, scene_id):
        st.markdown("---")
        outcome_colors = {
            "failure": "🔴",
            "compromise": "🟡", 
            "success": "🟢"
        }
        
        outcome = scene.get("outcome", "unknown")
        outcome_message = scene.get("outcome_message", f"Scenario Complete - {outcome.title()}")
        outcome_color = outcome_colors.get(outcome, "⚪")
        
        st.markdown(f"### {outcome_color} {outcome_message}")
        
        # Add reflection form if completion tracking is enabled
        if self.metadata.get("completion_tracking", False):
            self.display_reflection_form(scene, scene_id, outcome)
        
        st.markdown("---")
        if st.button("Start Over", key="restart"):
            st.session_state.current_scene = "1"
            st.session_state.scene_history = []
            st.session_state.choices_made = []
            st.rerun()
    
    def display_reflection_form(self, scene, scene_id, outcome):
        st.markdown("---")
        st.subheader("📝 Complete Your Reflection")
        
        # Check if reflection already submitted
        reflection_key = f"reflection_submitted_{scene_id}"
        if st.session_state.get(reflection_key, False):
            st.success("✅ Reflection submitted successfully!")
            st.info(f"Thank you for completing the {self.metadata.get('title', 'scenario')} and sharing your thoughts!")
        else:
            # Student name input
            student_name = st.text_input(
                "Student Name:", 
                key=f"student_name_{scene_id}",
                help="Enter your name to receive completion credit"
            )
            
            # Dynamic reflection questions
            st.markdown("**Please reflect on your experience:**")
            
            reflections = {}
            for i, (question, prompt) in enumerate(zip(self.reflection_questions, self.reflection_prompts)):
                reflections[f"reflection_{i+1}"] = st.text_area(
                    f"{i+1}. {question}",
                    key=f"reflection_{i+1}_{scene_id}",
                    height=100,
                    help=prompt
                )
            
            # Submit button
            if st.button("Submit Reflection", key=f"submit_reflection_{scene_id}", type="primary"):
                if student_name and all(reflections.values()):
                    # Save to Google Sheets
                    success = save_reflection_to_sheets(
                        student_name=student_name,
                        outcome=outcome,
                        scenario_title=self.metadata.get('title', 'Unknown Scenario'),
                        choices_made=st.session_state.choices_made,
                        **reflections
                    )
                    
                    if success:
                        st.session_state[reflection_key] = True
                        st.rerun()
                    else:
                        st.error("There was an error submitting your reflection. Please try again.")
                else:
                    st.error("Please fill in all fields before submitting.")
    
    def display_progress(self):
        if st.session_state.choices_made:
            with st.sidebar:
                st.subheader("Your Journey")
                for i, choice in enumerate(st.session_state.choices_made):
                    st.write(f"**Step {i+1}:** {choice['choice']}")
    
    def display_navigation_controls(self):
        with st.sidebar:
            st.markdown("---")
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
                st.rerun()
    
    def run(self):
        # Set page config
        st.set_page_config(
            page_title=self.metadata.get("page_title", "Scenario"),
            page_icon=self.metadata.get("page_icon", "📖"),
            layout="wide"
        )
        
        # Initialize Google Sheets on first run if completion tracking is enabled
        if self.metadata.get("completion_tracking", False):
            initialize_google_sheet()
        
        self.initialize_session_state()
        
        # Main content
        current_scene_id = st.session_state.current_scene
        scene = self.display_scene(current_scene_id)
        
        if scene:
            self.handle_choice(scene, current_scene_id)
        
        # Sidebar content
        self.display_progress()
        self.display_navigation_controls()

def get_available_scenarios():
    """Get list of available scenarios from the scenarios directory"""
    scenarios_dir = Path("scenarios")
    if not scenarios_dir.exists():
        return []
    
    scenarios = []
    for scenario_dir in scenarios_dir.iterdir():
        if scenario_dir.is_dir() and (scenario_dir / "config.json").exists():
            try:
                with open(scenario_dir / "config.json", 'r') as f:
                    config = json.load(f)
                    metadata = config.get("metadata", {})
                    scenarios.append({
                        "id": scenario_dir.name,
                        "title": metadata.get("title", scenario_dir.name.replace("_", " ").title()),
                        "description": metadata.get("description", "No description available"),
                        "path": scenario_dir
                    })
            except (json.JSONDecodeError, FileNotFoundError):
                continue
    
    return scenarios