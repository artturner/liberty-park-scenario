import streamlit as st
import os
from pathlib import Path
from scenario_engine import ScenarioEngine, get_available_scenarios

def get_scenario_icon(scenario_id):
    """Get appropriate icon for each scenario"""
    icons = {
        'probable_cause': '🚔',
        'liberty_park': '🌳',
        'convention_1787': '🏛️',
        'rio_grande': '🏛️'
    }
    return icons.get(scenario_id, '📚')

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
        page_title="Interactive Learning Scenarios",
        page_icon="📚",
        layout="wide"
    )

    # Header section with improved styling
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 2rem 0 3rem 0;
    }
    .scenario-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: none;
    }
    .scenario-title {
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: white;
    }
    .scenario-description {
        font-size: 0.95rem;
        line-height: 1.5;
        color: rgba(255,255,255,0.9);
        margin-bottom: 1.5rem;
    }
    .stButton > button {
        width: 100%;
        background: rgba(255,255,255,0.2);
        color: white;
        border: 2px solid rgba(255,255,255,0.3);
        border-radius: 10px;
        padding: 0.75rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background: rgba(255,255,255,0.3);
        border-color: rgba(255,255,255,0.5);
        transform: translateY(-2px);
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="main-header">
        <h1>📚 Interactive Learning Scenarios</h1>
        <p style="font-size: 1.2rem; color: #666; margin-top: 1rem;">
            Choose a scenario to begin your learning experience:
        </p>
    </div>
    """, unsafe_allow_html=True)

    scenarios = get_available_scenarios()

    if not scenarios:
        st.warning("No scenarios found. Please add scenario configurations to the 'scenarios' directory.")
        return

    # Display scenarios in a responsive grid with better spacing
    num_cols = min(len(scenarios), 2) if len(scenarios) <= 4 else 3
    cols = st.columns(num_cols, gap="large")

    for i, scenario in enumerate(scenarios):
        with cols[i % num_cols]:
            # Create attractive scenario card
            st.markdown(f"""
            <div class="scenario-card">
                <div class="scenario-title">{get_scenario_icon(scenario['id'])} {scenario['title']}</div>
                <div class="scenario-description">{scenario['description']}</div>
            </div>
            """, unsafe_allow_html=True)

            # Create scenario URL
            scenario_url = f"?scenario={scenario['id']}"

            if st.button(f"Start {scenario['title']}", key=f"start_{scenario['id']}"):
                st.query_params.scenario = scenario['id']
                st.rerun()
    
    # Add information about the platform
    st.markdown("<br><br>", unsafe_allow_html=True)

    st.markdown("""
    <div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                padding: 2rem; border-radius: 15px; margin-top: 3rem; text-align: center;">
        <h3 style="color: #333; margin-bottom: 1rem;">✨ About These Learning Scenarios</h3>
        <p style="color: #555; font-size: 1.1rem; margin-bottom: 2rem;">
            Interactive learning experiences designed to develop critical thinking through realistic decision-making
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Use Streamlit columns for better compatibility
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("### 🎯")
        st.markdown("**Interactive Choices**")
        st.markdown("Make decisions that shape your learning journey")

    with col2:
        st.markdown("### 🌟")
        st.markdown("**Multiple Pathways**")
        st.markdown("Explore different outcomes based on your choices")

    with col3:
        st.markdown("### 🤔")
        st.markdown("**Deep Reflection**")
        st.markdown("Thoughtful questions to enhance learning")

    with col4:
        st.markdown("### 📊")
        st.markdown("**Progress Tracking**")
        st.markdown("Monitor your journey and completion")

if __name__ == "__main__":
    main()