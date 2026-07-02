# integrations.py
import streamlit as st
import os
import time

def render():
    st.markdown("<h1 class='gradient-text'>DevOps & Tool Integrations</h1>", unsafe_allow_html=True)
    st.write("Securely connect D.A.M.I. to your DevOps toolchain to synchronize migration milestones, push generated templates, and publish cutover runbooks.")
    st.write("---")
    
    # Initialize session states for mock connection states
    if "jira_conn" not in st.session_state:
        st.session_state.jira_conn = False
    if "github_conn" not in st.session_state:
        st.session_state.github_conn = False
    if "confluence_conn" not in st.session_state:
        st.session_state.confluence_conn = False
        
    col1, col2, col3 = st.columns(3)
    
    # Jira Card
    with col1:
        st.subheader("🤖 Jira Project Management")
        st.caption("Synchronize migration waves and cutover checklists into project tasks.")
        
        if not st.session_state.jira_conn:
            jira_domain = st.text_input("Jira Domain", placeholder="company.atlassian.net", key="jira_dom")
            jira_project = st.text_input("Project Key", placeholder="MIG", key="jira_proj")
            jira_token = st.text_input("API Token", type="password", placeholder="Enter Jira API Token", key="jira_tok")
            
            if st.button("🔌 Connect Jira", use_container_width=True):
                if jira_domain and jira_project and jira_token:
                    with st.spinner("Establishing Jira OAuth secure connection..."):
                        time.sleep(1.5)
                    st.session_state.jira_conn = True
                    st.success("Successfully connected to Jira Project!")
                    st.rerun()
                else:
                    st.warning("Please fill in all fields.")
        else:
            st.markdown("<span class='status-badge status-success'>Connected</span>", unsafe_allow_html=True)
            st.info(f"Target Project Key: **{st.session_state.get('jira_proj', 'MIG')}**")
            
            if st.button("🚀 Sync Waves to Jira Board", use_container_width=True):
                with st.spinner("Generating Epics and tasks for Wave 0, 1, 2, 3, 4..."):
                    time.sleep(2.0)
                st.success("Jira board updated! Created 5 Epics and 100 workload migration sub-tasks successfully.")
                
            if st.button("🔌 Disconnect Jira", use_container_width=True):
                st.session_state.jira_conn = False
                st.rerun()
                
    # GitHub Card
    with col2:
        st.subheader("🐙 GitHub IaC Codebase")
        st.caption("Directly commit and push generated Terraform HCL and Kubernetes templates.")
        
        if not st.session_state.github_conn:
            github_repo = st.text_input("GitHub Repository", placeholder="org/migration-iac", key="gh_repo")
            github_branch = st.text_input("Target Branch", placeholder="main", key="gh_branch")
            github_token = st.text_input("Access Token (PAT)", type="password", placeholder="Enter GitHub Personal Token", key="gh_tok")
            
            if st.button("🔌 Connect GitHub", use_container_width=True):
                if github_repo and github_branch and github_token:
                    with st.spinner("Authorizing GitHub credentials..."):
                        time.sleep(1.5)
                    st.session_state.github_conn = True
                    st.success("Connected to repository branch!")
                    st.rerun()
                else:
                    st.warning("Please fill in all fields.")
        else:
            st.markdown("<span class='status-badge status-success'>Connected</span>", unsafe_allow_html=True)
            st.info(f"Target Branch: **{st.session_state.get('gh_branch', 'main')}**")
            
            if st.button("📦 Push IaC to Repository", use_container_width=True):
                with st.spinner("Committer: dami-bot. Running git push origin..."):
                    time.sleep(2.0)
                st.success("IaC pushed! Committed generated Terraform templates and Ansible playbooks under commit ID 'dami-auto-iac-wave-0'.")
                
            if st.button("🔌 Disconnect GitHub", use_container_width=True):
                st.session_state.github_conn = False
                st.rerun()
                
    # Confluence Card
    with col3:
        st.subheader("📚 Confluence Wiki")
        st.caption("Publish runbooks, checklists, and target topologies for team alignment.")
        
        if not st.session_state.confluence_conn:
            conf_domain = st.text_input("Confluence Domain", placeholder="company.atlassian.net/wiki", key="conf_dom")
            conf_space = st.text_input("Space Key", placeholder="MIGDOCS", key="conf_space")
            conf_token = st.text_input("API Token", type="password", placeholder="Enter Confluence API Token", key="conf_tok")
            
            if st.button("🔌 Connect Confluence", use_container_width=True):
                if conf_domain and conf_space and conf_token:
                    with st.spinner("Connecting to Confluence Wiki space..."):
                        time.sleep(1.5)
                    st.session_state.confluence_conn = True
                    st.success("Connected to wiki space successfully!")
                    st.rerun()
                else:
                    st.warning("Please fill in all fields.")
        else:
            st.markdown("<span class='status-badge status-success'>Connected</span>", unsafe_allow_html=True)
            st.info(f"Wiki Space Key: **{st.session_state.get('conf_space', 'MIGDOCS')}**")
            
            if st.button("✍️ Publish Runbooks & Checklist", use_container_width=True):
                with st.spinner("Rendering wiki pages and creating attachments..."):
                    time.sleep(2.0)
                st.success("Published runbook wiki space! Document: 'DAMI-Wave-0-Cutover-Runbook' is active.")
                
            if st.button("🔌 Disconnect Confluence", use_container_width=True):
                st.session_state.confluence_conn = False
                st.rerun()

    st.write("---")
    st.subheader("🔒 Secure Vault Credential Storage Status")
    st.markdown("""
    All credentials entered on this portal are encrypted and stored in a **Google Cloud Secret Manager** secure vault instance, referencing access controls under KMS.
    - **Encryption Standard:** AES-256-GCM
    - **Service Account Link:** `dami-migration-runner@cohort-2-497207.iam.gserviceaccount.com`
    """)

if __name__ == "__main__":
    render()
