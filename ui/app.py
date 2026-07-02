# app.py
import streamlit as st
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# App Configuration
st.set_page_config(
    page_title="D.A.M.I. | Discovery & Autonomous Migration Intelligence",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Ethereal Architect CSS Injection
def inject_custom_css():
    st.markdown('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">', unsafe_allow_html=True)
    st.markdown("""<style>
        /* ===== DARK MODE (default) ===== */
        .stApp {
            background-color: #07070d;
            color: #e2e8f0;
            font-family: 'Inter', sans-serif;
        }
        html { scroll-behavior: smooth; }

        section[data-testid="stSidebar"] {
            background-color: #0f0f1a !important;
            border-right: 1px solid #1e1e2f;
        }

        /* Gradient Titles */
        .gradient-text {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #22d3ee 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
            animation: gradientShift 6s ease infinite;
            background-size: 200% 200%;
        }
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        /* Metric Cards */
        div[data-testid="metric-container"] {
            background: rgba(30, 30, 47, 0.4);
            border: 1px solid rgba(99, 102, 241, 0.2);
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }
        div[data-testid="metric-container"]:hover {
            border-color: rgba(99, 102, 241, 0.5);
            box-shadow: 0 4px 25px rgba(99, 102, 241, 0.2);
            transform: translateY(-2px);
        }

        /* Buttons */
        .stButton>button {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
            color: white !important;
            border: none !important;
            padding: 8px 20px !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
            transition: all 0.3s ease !important;
        }
        .stButton>button:hover {
            box-shadow: 0 4px 20px rgba(99, 102, 241, 0.5) !important;
            transform: translateY(-1px) !important;
        }
        .stDownloadButton>button {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3) !important;
        }

        /* DataFrames */
        div[data-testid="stDataFrame"] {
            border-radius: 10px;
            overflow: hidden;
            border: 1px solid rgba(99, 102, 241, 0.15);
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] { gap: 4px; }
        .stTabs [data-baseweb="tab"] { border-radius: 8px 8px 0 0; padding: 8px 16px; }

        /* Sidebar Nav */
        div[data-testid="stSidebar"] .stRadio > div { gap: 0px !important; }
        div[data-testid="stSidebar"] .stRadio label {
            transition: all 0.2s ease;
            padding: 6px 10px;
            border-radius: 6px;
            margin: 1px 0;
            font-size: 0.88rem;
        }
        div[data-testid="stSidebar"] .stRadio label:hover {
            background: rgba(99, 102, 241, 0.1);
            color: #a78bfa;
        }
        /* Hide radio label header */
        div[data-testid="stSidebar"] .stRadio > label { display: none !important; }

        /* Expanders */
        details { border: 1px solid rgba(99, 102, 241, 0.15) !important; border-radius: 8px !important; }

        /* Status Badges */
        .status-badge { padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 600; }
        .status-success { background-color: rgba(52, 168, 83, 0.2); color: #34a853; border: 1px solid #34a853; }
        .status-warning { background-color: rgba(251, 188, 4, 0.2); color: #fbbc04; border: 1px solid #fbbc04; }
        .status-danger { background-color: rgba(234, 67, 53, 0.2); color: #ea4335; border: 1px solid #ea4335; }
        .status-info { background-color: rgba(66, 133, 244, 0.2); color: #4285f4; border: 1px solid #4285f4; }

        hr { border-color: rgba(99, 102, 241, 0.12) !important; }
        .stProgress > div > div {
            background: linear-gradient(90deg, #6366f1, #8b5cf6, #22d3ee) !important;
            border-radius: 10px;
        }

        /* Sidebar Nav - text visibility */
        div[data-testid="stSidebar"] .stRadio label span {
            color: #cbd5e1 !important;
        }
        div[data-testid="stSidebar"] .stRadio label[data-checked="true"] span {
            color: #a78bfa !important;
            font-weight: 600;
        }
        /* Hide "Navigation Menu" header */
        div[data-testid="stSidebar"] .stRadio > label,
        div[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

# Main Application Frame
def main():
    inject_custom_css()
    
    # Initialize session states
    if "project_id" not in st.session_state:
        st.session_state["project_id"] = "proj-migration-001"
    if "api_url" not in st.session_state:
        st.session_state["api_url"] = "http://localhost:8000"
        
    st.sidebar.markdown("""<div style='text-align:center; padding: 8px 0 4px 0;'>
        <h2 class='gradient-text' style='margin:0; font-size:1.6rem;'>D.A.M.I.</h2>
        <p style='margin:2px 0 0 0; font-size:0.7rem; color:#94a3b8; letter-spacing:0.5px;'>Discovery & Autonomous Migration Intelligence</p>
    </div>""", unsafe_allow_html=True)
    st.sidebar.write("---")
    
    menu_options = [
        "🏠 Dashboard",
        "📤 Upload Center",
        "📋 Server Inventory",
        "🔗 Dependency Map",
        "⚠️ Risk Assessment",
        "🌊 Wave Gantt Chart",
        "🏗️ Target Architecture",
        "💻 IaC & Runbooks",
        "💰 TCO & FinOps",
        "🛡️ Compliance & Security",
        "🔌 Integrations",
        "🔬 Agent Trace",
        "🧠 Self-Learning",
        "💬 Conversational Assistant"
    ]
    
    selection = st.sidebar.radio("Navigation Menu", menu_options, label_visibility="collapsed")
    
    # Render the selected page
    try:
        if selection == "🏠 Dashboard":
            from ui.pages import dashboard
            dashboard.render()
        elif selection == "📤 Upload Center":
            from ui.pages import upload
            upload.render()
        elif selection == "📋 Server Inventory":
            from ui.pages import inventory
            inventory.render()
        elif selection == "🔗 Dependency Map":
            from ui.pages import dependencies
            dependencies.render()
        elif selection == "⚠️ Risk Assessment":
            from ui.pages import risk
            risk.render()
        elif selection == "🌊 Wave Gantt Chart":
            from ui.pages import wave_plan
            wave_plan.render()
        elif selection == "🏗️ Target Architecture":
            from ui.pages import architecture
            architecture.render()
        elif selection == "💻 IaC & Runbooks":
            from ui.pages import iac_runbooks
            iac_runbooks.render()
        elif selection == "💰 TCO & FinOps":
            from ui.pages import finops
            finops.render()
        elif selection == "🛡️ Compliance & Security":
            from ui.pages import compliance
            compliance.render()
        elif selection == "🔌 Integrations":
            from ui.pages import integrations
            integrations.render()
        elif selection == "🔬 Agent Trace":
            from ui.pages import agent_trace
            agent_trace.render()
        elif selection == "🧠 Self-Learning":
            from ui.pages import self_learning
            self_learning.render()
        elif selection == "💬 Conversational Assistant":
            from ui.pages import chat
            chat.render()
    except ImportError as e:
        # If imports fail because pip install is still running, show dynamic placeholder
        st.warning(f"Libraries are currently initializing in the background. Please wait a moment. (Import Error: {e})")
        st.info("D.A.M.I environment setup is currently installing python dependencies via pip. Table creation, seeding, and UI components are compiling.")
        st.spinner("Installing packages...")

if __name__ == "__main__":
    main()
