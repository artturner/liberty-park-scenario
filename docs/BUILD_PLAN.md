# Liberty Park SaaS - Step-by-Step Build Plan

## Overview

This document provides a detailed, actionable build plan for transforming the Liberty Park Scenario Engine into a commercial SaaS product. The plan is organized into 14-week sprints with specific deliverables.

---

## Prerequisites

Before starting development, ensure the following are in place:

- [ ] Development environment setup (Python 3.11+, Node.js 18+)
- [ ] PostgreSQL database (local or cloud)
- [ ] Redis instance (local or cloud)
- [ ] Cloud storage account (Cloudflare R2 or AWS S3)
- [ ] Auth0 or Clerk account (authentication)
- [ ] Stripe account (payments)
- [ ] GitHub repository with CI/CD enabled

---

## Phase 1: Foundation (Weeks 1-3)

### Week 1: Project Setup & Database

#### Day 1-2: Project Structure

```bash
# Create new project structure
liberty-park-saas/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Settings/configuration
│   │   ├── database.py          # Database connection
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── routers/             # API routes
│   │   ├── services/            # Business logic
│   │   └── utils/               # Helpers
│   ├── migrations/              # Alembic migrations
│   ├── tests/
│   ├── requirements.txt
│   └── alembic.ini
├── frontend/
│   ├── app.py                   # Main Streamlit app
│   ├── pages/
│   │   ├── 1_🏠_Home.py
│   │   ├── 2_📚_Scenarios.py
│   │   ├── 3_📊_Dashboard.py
│   │   └── 4_⚙️_Settings.py
│   ├── components/              # Reusable components
│   ├── utils/                   # Frontend utilities
│   └── requirements.txt
├── shared/                      # Shared types/utilities
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
└── README.md
```

**Tasks:**
- [ ] Create project directory structure
- [ ] Initialize Git repository with .gitignore
- [ ] Set up Python virtual environments
- [ ] Create requirements.txt files

**Deliverable:** Empty project structure ready for development

#### Day 3-4: Database Setup

**File: `backend/app/database.py`**
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Tasks:**
- [ ] Install SQLAlchemy, Alembic, asyncpg
- [ ] Create database connection module
- [ ] Set up Alembic for migrations
- [ ] Create initial migration with all tables

**Deliverable:** Working PostgreSQL connection with all tables created

#### Day 5: Core Models

**File: `backend/app/models/tenant.py`**
```python
from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.database import Base

class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    plan_type = Column(String(50), default='free')
    stripe_customer_id = Column(String(255), nullable=True)
    settings = Column(JSON, default={})
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

**Tasks:**
- [ ] Create Tenant model
- [ ] Create User model with role enum
- [ ] Create Class and Enrollment models
- [ ] Create Scenario and ScenarioImage models
- [ ] Create Session and Reflection models
- [ ] Create Subscription model

**Deliverable:** Complete SQLAlchemy models matching architecture design

---

### Week 2: Authentication & API Foundation

#### Day 1-2: FastAPI Setup

**File: `backend/app/main.py`**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import auth, tenants, users, scenarios, classes, sessions

app = FastAPI(
    title="Liberty Park API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(tenants.router, prefix="/api/tenants", tags=["tenants"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(scenarios.router, prefix="/api/scenarios", tags=["scenarios"])
app.include_router(classes.router, prefix="/api/classes", tags=["classes"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**Tasks:**
- [ ] Create FastAPI application
- [ ] Configure CORS for frontend
- [ ] Set up router structure
- [ ] Create health check endpoint
- [ ] Add API documentation

**Deliverable:** Running FastAPI server with basic structure

#### Day 3-4: Authentication Implementation

**File: `backend/app/routers/auth.py`**
```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.auth import AuthService
from app.schemas.auth import Token, UserCreate, UserResponse

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    return AuthService.create_user(db, user_data)

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return AuthService.authenticate_user(db, form_data.username, form_data.password)

@router.get("/me", response_model=UserResponse)
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return AuthService.get_current_user(db, token)
```

**Tasks:**
- [ ] Implement password hashing (bcrypt)
- [ ] Create JWT token generation
- [ ] Create registration endpoint
- [ ] Create login endpoint
- [ ] Create get current user endpoint
- [ ] Add Google OAuth integration

**Deliverable:** Working authentication system with JWT tokens

#### Day 5: Authorization Middleware

**File: `backend/app/utils/auth.py`**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.services.auth import AuthService
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    user = AuthService.verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    return user

async def get_current_teacher(user: User = Depends(get_current_user)) -> User:
    if user.role not in ['teacher', 'admin']:
        raise HTTPException(status_code=403, detail="Teachers only")
    return user

async def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admins only")
    return user

def get_tenant_user(user: User = Depends(get_current_user)) -> User:
    if not user.tenant_id:
        raise HTTPException(status_code=403, detail="No organization")
    return user
```

**Tasks:**
- [ ] Create role-based dependencies
- [ ] Create tenant isolation middleware
- [ ] Add permission checking utilities
- [ ] Write authentication tests

**Deliverable:** Complete authorization system with role checks

---

### Week 3: Scenario Engine Migration

#### Day 1-2: Extract Scenario Engine

**File: `backend/app/services/scenario_engine.py`**
```python
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from app.models.scenario import Scenario, Session as GameSession
import json

class ScenarioEngine:
    def __init__(self, scenario: Scenario):
        self.scenario = scenario
        self.config = scenario.config
        self.metadata = self.config.get("metadata", {})
        self.scenes = self.config.get("scenes", {})
        self.variables = self.config.get("variables", {})
    
    def get_initial_state(self) -> Dict[str, Any]:
        return {
            "current_scene": "1",
            "scene_history": [],
            "choices_made": [],
            "variables": self.variables.copy()
        }
    
    def process_choice(self, state: Dict, scene_id: str, choice_index: int) -> Dict:
        scene = self.scenes.get(scene_id)
        if not scene or scene["type"] != "choice":
            return state
        
        choice = scene["choices"][choice_index]
        
        # Apply effects
        if "effects" in choice:
            for var_name, change in choice["effects"].items():
                if var_name in state["variables"]:
                    state["variables"][var_name] += change
        
        # Update state
        state["scene_history"].append(scene_id)
        state["choices_made"].append({
            "scene": scene_id,
            "choice": choice["text"],
            "next": choice["next"]
        })
        state["current_scene"] = choice["next"]
        
        return state
    
    def evaluate_condition(self, condition_str: str, variables: Dict) -> bool:
        try:
            python_condition = condition_str.replace("&&", " and ").replace("||", " or ")
            return eval(python_condition, {"__builtins__": {}}, variables)
        except:
            return False
    
    def get_next_scene_conditional(self, scene: Dict, state: Dict) -> str:
        for condition in scene.get("conditions", []):
            if self.evaluate_condition(condition["condition"], state["variables"]):
                return condition["next"]
        return scene.get("default")
    
    def is_terminal(self, scene_id: str) -> bool:
        scene = self.scenes.get(scene_id)
        return scene and scene.get("type") == "end"
    
    def get_outcome(self, scene_id: str) -> Optional[str]:
        scene = self.scenes.get(scene_id)
        return scene.get("outcome") if scene else None
```

**Tasks:**
- [ ] Extract scenario logic from Streamlit to service class
- [ ] Create stateless engine (no session_state dependency)
- [ ] Add JSON validation for scenario configs
- [ ] Create scenario parsing utilities
- [ ] Write unit tests for engine

**Deliverable:** Platform-agnostic scenario engine service

#### Day 3-4: Scenario API Endpoints

**File: `backend/app/routers/scenarios.py`**
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.scenario import Scenario
from app.schemas.scenario import ScenarioResponse, ScenarioCreate, ScenarioUpdate
from app.utils.auth import get_current_user, get_current_teacher
from app.services.scenario_engine import ScenarioEngine

router = APIRouter()

@router.get("/", response_model=List[ScenarioResponse])
async def list_scenarios(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """List scenarios available to the user's tenant"""
    query = db.query(Scenario).filter(
        (Scenario.tenant_id == user.tenant_id) | (Scenario.is_public == True)
    )
    return query.all()

@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(
    scenario_id: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Get a specific scenario with full config"""
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario

@router.post("/", response_model=ScenarioResponse)
async def create_scenario(
    scenario_data: ScenarioCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_teacher)
):
    """Create a new scenario (teachers only)"""
    scenario = Scenario(
        tenant_id=user.tenant_id,
        created_by=user.id,
        **scenario_data.dict()
    )
    db.add(scenario)
    db.commit()
    return scenario
```

**Tasks:**
- [ ] Create scenario CRUD endpoints
- [ ] Add tenant filtering
- [ ] Implement scenario validation
- [ ] Add image upload handling
- [ ] Create scenario import from JSON

**Deliverable:** Complete scenario API

#### Day 5: Session Management API

**File: `backend/app/routers/sessions.py`**
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.session import Session as GameSession
from app.schemas.session import SessionCreate, SessionUpdate, SessionResponse
from app.utils.auth import get_current_user
from app.services.scenario_engine import ScenarioEngine

router = APIRouter()

@router.post("/start", response_model=SessionResponse)
async def start_session(
    data: SessionCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Start a new scenario session"""
    scenario = db.query(Scenario).filter(Scenario.id == data.scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    engine = ScenarioEngine(scenario)
    initial_state = engine.get_initial_state()
    
    session = GameSession(
        student_id=user.id,
        scenario_id=data.scenario_id,
        class_id=data.class_id,
        **initial_state
    )
    db.add(session)
    db.commit()
    return session

@router.post("/{session_id}/choice", response_model=SessionResponse)
async def make_choice(
    session_id: str,
    choice_data: ChoiceRequest,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Process a choice and update session state"""
    session = db.query(GameSession).filter(
        GameSession.id == session_id,
        GameSession.student_id == user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    scenario = db.query(Scenario).filter(Scenario.id == session.scenario_id).first()
    engine = ScenarioEngine(scenario)
    
    state = {
        "current_scene": session.current_scene,
        "scene_history": session.scene_history,
        "choices_made": session.choices_made,
        "variables": session.variables
    }
    
    updated_state = engine.process_choice(state, session.current_scene, choice_data.choice_index)
    
    # Update session
    session.current_scene = updated_state["current_scene"]
    session.scene_history = updated_state["scene_history"]
    session.choices_made = updated_state["choices_made"]
    session.variables = updated_state["variables"]
    
    if engine.is_terminal(updated_state["current_scene"]):
        session.completed_at = datetime.utcnow()
        session.outcome = engine.get_outcome(updated_state["current_scene"])
    
    db.commit()
    return session
```

**Tasks:**
- [ ] Create session start endpoint
- [ ] Create choice processing endpoint
- [ ] Add session state retrieval
- [ ] Implement completion tracking
- [ ] Add reflection submission

**Deliverable:** Complete session management API

---

## Phase 2: Frontend Development (Weeks 4-6)

### Week 4: Streamlit Frontend Restructure

#### Day 1-2: Multi-Page App Structure

**File: `frontend/app.py`**
```python
import streamlit as st
import requests
from utils.auth import check_auth, login_page, logout

st.set_page_config(
    page_title="Liberty Park",
    page_icon="🌳",
    layout="wide"
)

# Initialize session state
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None

# Check authentication
if not check_auth():
    login_page()
    st.stop()

# Sidebar navigation
with st.sidebar:
    st.title(f"Welcome, {st.session_state.user['first_name']}!")
    st.write(f"Role: {st.session_state.user['role'].title()}")
    st.divider()
    
    if st.button("🚪 Logout"):
        logout()
        st.rerun()

# Main content
st.title("🌳 Liberty Park")
st.write("Interactive Learning Scenarios")

# Role-based dashboard
if st.session_state.user['role'] == 'student':
    st.markdown("### Your Assigned Scenarios")
    # Show student dashboard
elif st.session_state.user['role'] == 'teacher':
    st.markdown("### Teacher Dashboard")
    # Show teacher dashboard
```

**Tasks:**
- [ ] Create main app with auth check
- [ ] Implement login page UI
- [ ] Create registration page
- [ ] Set up session state management
- [ ] Add API client utilities

**Deliverable:** Working authentication flow in Streamlit

#### Day 3-4: Scenario Player Component

**File: `frontend/components/scenario_player.py`**
```python
import streamlit as st
import requests
from utils.api import api_client

def render_scenario_player(scenario_id: str, session_id: str):
    """Render the interactive scenario player"""
    
    # Get current session state
    session = api_client.get(f"/sessions/{session_id}")
    scenario = api_client.get(f"/scenarios/{scenario_id}")
    
    config = scenario["config"]
    current_scene_id = session["current_scene"]
    scene = config["scenes"][current_scene_id]
    
    # Display scene title
    st.title(scene["title"])
    
    # Display image
    if scene.get("image"):
        image_url = api_client.get_image_url(scenario_id, scene["image"])
        st.image(image_url, use_container_width=True)
    
    # Display narration
    st.markdown(scene.get("narration", ""))
    
    # Handle scene type
    if scene["type"] == "choice":
        st.markdown("---")
        st.subheader("What will you do?")
        
        for i, choice in enumerate(scene["choices"]):
            if st.button(f"{chr(65+i)}. {choice['text']}", key=f"choice_{i}"):
                # Submit choice to API
                api_client.post(f"/sessions/{session_id}/choice", {
                    "choice_index": i
                })
                st.rerun()
    
    elif scene["type"] == "auto_advance":
        if st.button("Continue"):
            # Auto-advance to next scene
            api_client.post(f"/sessions/{session_id}/advance")
            st.rerun()
    
    elif scene["type"] == "end":
        render_end_scene(scene, session, scenario)
    
    # Display progress in sidebar
    with st.sidebar:
        st.subheader("Your Journey")
        for i, choice in enumerate(session.get("choices_made", [])):
            st.write(f"**Step {i+1}:** {choice['choice']}")

def render_end_scene(scene, session, scenario):
    """Render the end scene with reflection form"""
    outcome_colors = {
        "failure": "🔴",
        "compromise": "🟡",
        "success": "🟢"
    }
    
    outcome = scene.get("outcome", "unknown")
    st.markdown(f"### {outcome_colors.get(outcome, '⚪')} {scene.get('outcome_message', 'Complete')}")
    
    # Reflection form
    st.markdown("---")
    st.subheader("📝 Complete Your Reflection")
    
    questions = scenario["config"].get("reflection_questions", [])
    prompts = scenario["config"].get("reflection_prompts", [])
    
    responses = {}
    for i, (question, prompt) in enumerate(zip(questions, prompts)):
        responses[f"reflection_{i+1}"] = st.text_area(
            f"{i+1}. {question}",
            height=100,
            help=prompt,
            key=f"reflection_{i}"
        )
    
    if st.button("Submit Reflection", type="primary"):
        api_client.post(f"/sessions/{session['id']}/reflection", responses)
        st.success("Reflection submitted!")
```

**Tasks:**
- [ ] Create scenario player component
- [ ] Implement scene rendering
- [ ] Add choice handling with API calls
- [ ] Create reflection form
- [ ] Add progress tracking display

**Deliverable:** Working scenario player in Streamlit

#### Day 5: Student Dashboard

**File: `frontend/pages/1_📚_My_Scenarios.py`**
```python
import streamlit as st
from utils.api import api_client
from components.scenario_player import render_scenario_player

st.set_page_config(page_title="My Scenarios", page_icon="📚")

st.title("📚 My Scenarios")

# Get student's classes and assigned scenarios
classes = api_client.get("/classes/my-classes")
assignments = api_client.get("/assignments/my-assignments")

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["Assigned", "In Progress", "Completed"])

with tab1:
    st.subheader("Assigned Scenarios")
    for assignment in assignments:
        if assignment["status"] == "assigned":
            with st.container(border=True):
                st.write(f"**{assignment['scenario_title']}**")
                st.write(f"Class: {assignment['class_name']}")
                if assignment.get("due_date"):
                    st.write(f"Due: {assignment['due_date']}")
                if st.button("Start", key=f"start_{assignment['id']}"):
                    session = api_client.post("/sessions/start", {
                        "scenario_id": assignment["scenario_id"],
                        "class_id": assignment["class_id"]
                    })
                    st.session_state.current_session = session["id"]
                    st.rerun()

with tab2:
    st.subheader("In Progress")
    for session in api_client.get("/sessions/in-progress"):
        with st.container(border=True):
            st.write(f"**{session['scenario_title']}**")
            st.write(f"Started: {session['started_at']}")
            if st.button("Continue", key=f"continue_{session['id']}"):
                st.session_state.current_session = session["id"]
                st.rerun()

with tab3:
    st.subheader("Completed")
    for session in api_client.get("/sessions/completed"):
        with st.container(border=True):
            st.write(f"**{session['scenario_title']}**")
            st.write(f"Outcome: {session['outcome']}")
            st.write(f"Completed: {session['completed_at']}")

# If a session is active, show the player
if st.session_state.get("current_session"):
    st.divider()
    render_scenario_player(
        st.session_state.current_scenario,
        st.session_state.current_session
    )
```

**Tasks:**
- [ ] Create student dashboard page
- [ ] Implement assignment listing
- [ ] Add session management
- [ ] Create scenario browser
- [ ] Add completion history

**Deliverable:** Complete student experience

---

### Week 5: Teacher Dashboard

#### Day 1-2: Class Management

**File: `frontend/pages/2_👥_Classes.py`**
```python
import streamlit as st
from utils.api import api_client

st.set_page_config(page_title="Class Management", page_icon="👥")

st.title("👥 Class Management")

# Create new class
with st.expander("➕ Create New Class"):
    with st.form("create_class"):
        name = st.text_input("Class Name")
        description = st.text_area("Description")
        submitted = st.form_submit_button("Create Class")
        
        if submitted and name:
            new_class = api_client.post("/classes", {
                "name": name,
                "description": description
            })
            st.success(f"Created class: {new_class['name']}")
            st.write(f"**Class Code:** `{new_class['class_code']}`")
            st.info("Share this code with students to enroll")

# List existing classes
st.divider()
st.subheader("Your Classes")

classes = api_client.get("/classes")

for cls in classes:
    with st.container(border=True):
        col1, col2, col3 = st.columns([3, 2, 1])
        
        with col1:
            st.write(f"**{cls['name']}**")
            st.write(f"Code: `{cls['class_code']}`")
        
        with col2:
            st.write(f"Students: {cls['student_count']}")
            st.write(f"Active assignments: {cls['assignment_count']}")
        
        with col3:
            if st.button("📋", key=f"copy_{cls['id']}"):
                st.code(cls['class_code'])
            if st.button("⚙️", key=f"settings_{cls['id']}"):
                st.session_state.editing_class = cls['id']
```

**Tasks:**
- [ ] Create class management page
- [ ] Implement class creation form
- [ ] Add class code generation
- [ ] Create student roster view
- [ ] Add student enrollment management

**Deliverable:** Complete class management interface

#### Day 3-4: Assignment Management

**File: `frontend/pages/3_📝_Assignments.py`**
```python
import streamlit as st
from utils.api import api_client
from datetime import datetime

st.set_page_config(page_title="Assignments", page_icon="📝")

st.title("📝 Scenario Assignments")

# Select class
classes = api_client.get("/classes")
class_options = {cls['name']: cls['id'] for cls in classes}
selected_class = st.selectbox("Select Class", options=list(class_options.keys()))

if selected_class:
    class_id = class_options[selected_class]
    
    # Create assignment
    with st.expander("➕ Assign Scenario"):
        scenarios = api_client.get("/scenarios")
        scenario_options = {s['title']: s['id'] for s in scenarios}
        
        with st.form("create_assignment"):
            scenario = st.selectbox("Scenario", options=list(scenario_options.keys()))
            due_date = st.date_input("Due Date (optional)")
            due_time = st.time_input("Due Time (optional)")
            notes = st.text_area("Instructions for students")
            
            if st.form_submit_button("Assign"):
                assignment_data = {
                    "class_id": class_id,
                    "scenario_id": scenario_options[scenario],
                    "notes": notes
                }
                if due_date:
                    assignment_data["due_date"] = datetime.combine(due_date, due_time).isoformat()
                
                api_client.post("/assignments", assignment_data)
                st.success("Scenario assigned!")
    
    # View assignments
    st.divider()
    st.subheader("Current Assignments")
    
    assignments = api_client.get(f"/classes/{class_id}/assignments")
    
    for assignment in assignments:
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.write(f"**{assignment['scenario_title']}**")
                if assignment.get('due_date'):
                    st.write(f"Due: {assignment['due_date']}")
            
            with col2:
                completion = assignment['completion_rate']
                st.progress(completion / 100)
                st.write(f"{completion}% complete")
            
            with col3:
                if st.button("📊 View Progress", key=f"progress_{assignment['id']}"):
                    st.session_state.viewing_assignment = assignment['id']
```

**Tasks:**
- [ ] Create assignment creation form
- [ ] Implement scenario selection
- [ ] Add due date handling
- [ ] Create assignment list view
- [ ] Add progress indicators

**Deliverable:** Complete assignment management

#### Day 5: Progress Dashboard

**File: `frontend/pages/4_📊_Progress.py`**
```python
import streamlit as st
import pandas as pd
from utils.api import api_client

st.set_page_config(page_title="Progress Dashboard", page_icon="📊")

st.title("📊 Student Progress")

# Filters
col1, col2 = st.columns(2)
with col1:
    classes = api_client.get("/classes")
    class_options = {"All Classes": None} | {cls['name']: cls['id'] for cls in classes}
    selected_class = st.selectbox("Class", options=list(class_options.keys()))

with col2:
    scenarios = api_client.get("/scenarios")
    scenario_options = {"All Scenarios": None} | {s['title']: s['id'] for s in scenarios}
    selected_scenario = st.selectbox("Scenario", options=list(scenario_options.keys()))

# Get progress data
params = {}
if class_options[selected_class]:
    params["class_id"] = class_options[selected_class]
if scenario_options[selected_scenario]:
    params["scenario_id"] = scenario_options[selected_scenario]

progress_data = api_client.get("/analytics/progress", params=params)

# Summary metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Students", progress_data["total_students"])
with col2:
    st.metric("Completed", progress_data["completed"])
with col3:
    st.metric("In Progress", progress_data["in_progress"])
with col4:
    st.metric("Not Started", progress_data["not_started"])

# Outcome distribution
st.subheader("Outcome Distribution")
outcomes = progress_data["outcomes"]
st.bar_chart(pd.DataFrame({
    "Outcome": ["Success", "Compromise", "Failure"],
    "Count": [outcomes["success"], outcomes["compromise"], outcomes["failure"]]
}).set_index("Outcome"))

# Student detail table
st.subheader("Student Details")
df = pd.DataFrame(progress_data["students"])
st.dataframe(
    df,
    column_config={
        "name": "Student",
        "scenario": "Scenario",
        "status": "Status",
        "outcome": "Outcome",
        "completed_at": "Completed"
    },
    use_container_width=True
)

# Export button
if st.button("📥 Export to CSV"):
    csv = df.to_csv(index=False)
    st.download_button(
        "Download CSV",
        csv,
        "student_progress.csv",
        "text/csv"
    )
```

**Tasks:**
- [ ] Create progress dashboard
- [ ] Implement filtering
- [ ] Add summary metrics
- [ ] Create outcome charts
- [ ] Add CSV export

**Deliverable:** Complete analytics dashboard

---

### Week 6: Integration & Polish

#### Day 1-2: API Client & Error Handling

**File: `frontend/utils/api.py`**
```python
import streamlit as st
import requests
from typing import Optional, Dict, Any

class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if st.session_state.get("token"):
            headers["Authorization"] = f"Bearer {st.session_state.token}"
        return headers
    
    def _handle_error(self, response: requests.Response):
        if response.status_code == 401:
            st.session_state.token = None
            st.session_state.user = None
            st.error("Session expired. Please log in again.")
            st.rerun()
        elif response.status_code == 403:
            st.error("You don't have permission to perform this action.")
        elif response.status_code == 404:
            st.error("Resource not found.")
        else:
            st.error(f"An error occurred: {response.json().get('detail', 'Unknown error')}")
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        response = requests.get(
            f"{self.base_url}{endpoint}",
            headers=self._get_headers(),
            params=params
        )
        if response.ok:
            return response.json()
        self._handle_error(response)
        return None
    
    def post(self, endpoint: str, data: Dict) -> Any:
        response = requests.post(
            f"{self.base_url}{endpoint}",
            headers=self._get_headers(),
            json=data
        )
        if response.ok:
            return response.json()
        self._handle_error(response)
        return None
    
    def get_image_url(self, scenario_id: str, image_name: str) -> str:
        return f"{self.base_url}/scenarios/{scenario_id}/images/{image_name}"

api_client = APIClient(st.secrets["API_BASE_URL"])
```

**Tasks:**
- [ ] Create robust API client
- [ ] Add error handling
- [ ] Implement token refresh
- [ ] Add request retry logic
- [ ] Create loading states

**Deliverable:** Reliable API integration

#### Day 3-4: Image Storage Migration

**File: `backend/app/services/storage.py`**
```python
import boto3
from botocore.client import Config
from app.config import settings
import uuid
from typing import Optional

class StorageService:
    def __init__(self):
        self.client = boto3.client(
            's3',
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            config=Config(signature_version='s3v4')
        )
        self.bucket = settings.S3_BUCKET
    
    async def upload_image(self, file_data: bytes, scenario_id: str, scene_id: str) -> str:
        """Upload an image and return its key"""
        key = f"scenarios/{scenario_id}/{scene_id}_{uuid.uuid4().hex[:8]}.png"
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=file_data,
            ContentType='image/png'
        )
        return key
    
    def get_image_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate a presigned URL for an image"""
        return self.client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': key},
            ExpiresIn=expires_in
        )
    
    async def delete_image(self, key: str) -> bool:
        """Delete an image"""
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except:
            return False

storage_service = StorageService()
```

**Tasks:**
- [ ] Set up Cloudflare R2 or S3
- [ ] Create storage service
- [ ] Migrate existing images
- [ ] Create image upload endpoint
- [ ] Add image optimization

**Deliverable:** Working cloud storage integration

#### Day 5: Testing & Bug Fixes

**Tasks:**
- [ ] Write API endpoint tests
- [ ] Write frontend component tests
- [ ] Perform integration testing
- [ ] Fix identified bugs
- [ ] Performance optimization

**Deliverable:** Tested and stable MVP

---

## Phase 3: Monetization (Weeks 7-10)

### Week 7: Stripe Integration

#### Day 1-2: Stripe Setup

**File: `backend/app/services/payments.py`**
```python
import stripe
from app.config import settings
from sqlalchemy.orm import Session
from app.models.tenant import Tenant
from app.models.subscription import Subscription

stripe.api_key = settings.STRIPE_SECRET_KEY

PLAN_PRICES = {
    "starter": "price_starter_monthly",
    "school": "price_school_monthly"
}

class PaymentService:
    @staticmethod
    async def create_customer(tenant: Tenant) -> str:
        """Create a Stripe customer for a tenant"""
        customer = stripe.Customer.create(
            email=tenant.admin_email,
            name=tenant.name,
            metadata={"tenant_id": str(tenant.id)}
        )
        return customer.id
    
    @staticmethod
    async def create_subscription(tenant: Tenant, plan: str) -> dict:
        """Create a subscription for a tenant"""
        if not tenant.stripe_customer_id:
            tenant.stripe_customer_id = await PaymentService.create_customer(tenant)
        
        subscription = stripe.Subscription.create(
            customer=tenant.stripe_customer_id,
            items=[{"price": PLAN_PRICES[plan]}],
            payment_behavior="default_incomplete",
            expand=["latest_invoice.payment_intent"]
        )
        
        return {
            "subscription_id": subscription.id,
            "client_secret": subscription.latest_invoice.payment_intent.client_secret
        }
    
    @staticmethod
    async def handle_webhook(payload: bytes, sig_header: str) -> dict:
        """Handle Stripe webhook events"""
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        
        if event["type"] == "checkout.session.completed":
            # Handle successful payment
            pass
        elif event["type"] == "customer.subscription.updated":
            # Handle subscription update
            pass
        elif event["type"] == "customer.subscription.deleted":
            # Handle cancellation
            pass
        
        return {"status": "success"}
```

**Tasks:**
- [ ] Create Stripe account and products
- [ ] Implement customer creation
- [ ] Create subscription flow
- [ ] Set up webhook handling
- [ ] Add invoice generation

**Deliverable:** Working Stripe integration

#### Day 3-4: Subscription UI

**File: `frontend/pages/5_💳_Subscription.py`**
```python
import streamlit as st
from utils.api import api_client

st.title("💳 Subscription Management")

current_plan = api_client.get("/subscription/current")

if current_plan:
    st.write(f"Current Plan: **{current_plan['plan_type'].title()}**")
    st.write(f"Status: {current_plan['status']}")
    st.write(f"Renews: {current_plan['current_period_end']}")
    
    if st.button("Manage Subscription"):
        portal_url = api_client.post("/subscription/portal")["url"]
        st.markdown(f"[Click here to manage your subscription]({portal_url})")
else:
    st.write("You're on the **Free** plan")
    st.write("Upgrade to unlock more features!")

st.divider()

# Plan comparison
st.subheader("Available Plans")

plans = api_client.get("/subscription/plans")

for plan in plans:
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"### {plan['name']}")
            st.write(f"**${plan['price']}/month**")
            for feature in plan['features']:
                st.write(f"✅ {feature}")
        
        with col2:
            if plan['id'] != current_plan.get('plan_type'):
                if st.button("Select", key=f"plan_{plan['id']}"):
                    checkout = api_client.post("/subscription/checkout", {
                        "plan": plan['id']
                    })
                    st.markdown(f"[Complete checkout]({checkout['url']})")
```

**Tasks:**
- [ ] Create subscription page
- [ ] Implement plan comparison
- [ ] Add checkout flow
- [ ] Create customer portal link
- [ ] Add plan upgrade/downgrade

**Deliverable:** Complete subscription UI

#### Day 5: Plan Enforcement

**File: `backend/app/utils/limits.py`**
```python
from functools import wraps
from fastapi import HTTPException
from app.models.tenant import Tenant

PLAN_LIMITS = {
    "free": {
        "teachers": 1,
        "classes": 1,
        "students": 30,
        "scenarios": 3,
        "custom_scenarios": False
    },
    "starter": {
        "teachers": 5,
        "classes": 10,
        "students": 150,
        "scenarios": 999,
        "custom_scenarios": False
    },
    "school": {
        "teachers": 999,
        "classes": 999,
        "students": 500,
        "scenarios": 999,
        "custom_scenarios": True
    }
}

def check_limit(resource: str):
    """Decorator to check plan limits"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get tenant from kwargs or args
            tenant = kwargs.get('tenant') or args[0].tenant
            
            limit = PLAN_LIMITS.get(tenant.plan_type, PLAN_LIMITS['free'])[resource]
            current = await get_current_count(tenant, resource)
            
            if current >= limit:
                raise HTTPException(
                    status_code=402,
                    detail=f"Plan limit reached for {resource}. Please upgrade."
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

**Tasks:**
- [ ] Create limit checking utilities
- [ ] Add middleware for plan enforcement
- [ ] Implement feature gating
- [ ] Add upgrade prompts
- [ ] Create limit warnings

**Deliverable:** Working plan enforcement

---

### Week 8-10: Additional Features

#### Week 8: Custom Scenarios
- [ ] Scenario builder UI
- [ ] JSON schema validation
- [ ] Image upload interface
- [ ] Preview functionality
- [ ] Publish/share options

#### Week 9: LMS Integration
- [ ] LTI 1.3 implementation
- [ ] Deep linking
- [ ] Grade passback
- [ ] Roster sync
- [ ] Canvas/Google Classroom

#### Week 10: Polish & Launch Prep
- [ ] UI/UX improvements
- [ ] Performance optimization
- [ ] Documentation
- [ ] Marketing pages
- [ ] Support system

---

## Phase 4: Launch (Weeks 11-14)

### Week 11: Testing & QA
- [ ] End-to-end testing
- [ ] Load testing
- [ ] Security audit
- [ ] Bug fixes
- [ ] Performance tuning

### Week 12: Documentation
- [ ] User documentation
- [ ] API documentation
- [ ] Admin guide
- [ ] Video tutorials
- [ ] FAQ

### Week 13: Beta Launch
- [ ] Soft launch to beta users
- [ ] Collect feedback
- [ ] Iterate on feedback
- [ ] Monitor performance
- [ ] Support readiness

### Week 14: Public Launch
- [ ] Marketing launch
- [ ] Product Hunt submission
- [ ] Social media campaign
- [ ] Press outreach
- [ ] Monitor and respond

---

## Development Environment Setup

### Local Development

```bash
# Clone repository
git clone https://github.com/your-org/liberty-park-saas.git
cd liberty-park-saas

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings
alembic upgrade head
uvicorn app.main:app --reload

# Frontend setup (new terminal)
cd frontend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py

# Docker setup (alternative)
docker-compose up
```

### Environment Variables

```bash
# Backend (.env)
DATABASE_URL=postgresql://user:pass@localhost/liberty_park
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
S3_ACCESS_KEY=xxx
S3_SECRET_KEY=xxx
S3_BUCKET=liberty-park-images
S3_ENDPOINT_URL=https://xxx.r2.cloudflarestorage.com

# Frontend (.streamlit/secrets.toml)
API_BASE_URL = "http://localhost:8000"
```

---

## CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install -r frontend/requirements.txt
      - name: Run tests
        run: pytest backend/tests

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Render
        run: |
          curl ${{ secrets.RENDER_DEPLOY_HOOK }}
```

---

## Monitoring & Observability

### Recommended Tools
- **Logging**: Sentry for error tracking
- **Metrics**: Render metrics + custom dashboards
- **Uptime**: UptimeRobot or Pingdom
- **Analytics**: PostHog or Mixpanel

### Key Metrics to Track
- API response times
- Database query performance
- Error rates
- User engagement
- Conversion rates

---

## Success Criteria

### MVP Launch Criteria
- [ ] All Phase 1-2 features working
- [ ] Payment processing functional
- [ ] At least 10 beta users
- [ ] Zero critical bugs
- [ ] Documentation complete

### Success Metrics (3 months post-launch)
- 100+ registered organizations
- $5,000+ MRR
- < 5% churn rate
- 4.5+ star rating
- 50+ scenarios completed per day

---

## Conclusion

This build plan provides a clear roadmap from the current prototype to a commercial SaaS product. The phased approach allows for iterative development and early market validation while maintaining code quality and user experience standards.

**Estimated Timeline:** 14 weeks
**Estimated Team Size:** 2-3 developers
**Estimated Budget:** $15,000-25,000 (infrastructure, tools, services)
