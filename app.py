import streamlit as st
import os
from pathlib import Path
from scenario_engine import ScenarioEngine, get_available_scenarios

def main():
    # Check if we're running a specific scenario
    scenario_param = st.query_params.get("scenario")
    
    if scenario_param:
        # Run specific scenario
        scenario_path = Path(f"scenarios/{scenario_param}")
        if scenario_path.exists() and (scenario_path / "config.json").exists():
            engine = ScenarioEngine(scenario_path)
            engine.run()
        else:
            st.error(f"Scenario '{scenario_param}' not found")
            show_scenario_selector()
    else:
        # Show scenario selector
        show_scenario_selector()

def show_scenario_selector():
    st.set_page_config(
        page_title="Civic Engagement Scenarios",
        page_icon="🏛️",
        layout="wide"
    )
    
    st.title("🏛️ Civic Engagement Scenarios")
    st.markdown("Choose a scenario to begin your civic engagement learning experience.")
    
    scenarios = get_available_scenarios()
    
    if not scenarios:
        st.warning("No scenarios found. Please add scenario configurations to the 'scenarios' directory.")
        return
    
    # Display scenarios in a grid
    cols = st.columns(min(len(scenarios), 3))
    
    for i, scenario in enumerate(scenarios):
        with cols[i % 3]:
            st.subheader(scenario["title"])
            st.write(scenario["description"])
            
            # Create scenario URL
            scenario_url = f"?scenario={scenario['id']}"
            
            if st.button(f"Start {scenario['title']}", key=f"start_{scenario['id']}"):
                st.query_params.scenario = scenario['id']
                st.rerun()
    
    # Add information about the platform
    st.markdown("---")
    st.markdown("""
    ### About These Scenarios
    
    These interactive scenarios are designed to teach civic engagement through branching narratives.
    Each scenario presents you with choices that demonstrate different approaches to civic participation
    and their potential outcomes.
    
    **Features:**
    - Interactive decision-making
    - Multiple pathways and outcomes
    - Reflection questions for deeper learning
    - Progress tracking throughout your journey
    """)

if __name__ == "__main__":
    main()