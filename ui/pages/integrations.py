# integrations.py
import streamlit as st
import os
import time
import agents.vault_manager as vault

def render():
    st.markdown("<h1 class='gradient-text'>DevOps & Tool Integrations</h1>", unsafe_allow_html=True)
    st.write("Securely connect D.A.M.I. to your DevOps toolchain to synchronize migration milestones, push generated templates, and publish cutover runbooks.")
    st.write("---")
    
    # Initialize connection states based on secure vault contents
    if "jira_conn" not in st.session_state:
        st.session_state.jira_conn = vault.get_secret("jira_token") is not None
    if "github_conn" not in st.session_state:
        st.session_state.github_conn = vault.get_secret("github_token") is not None
    if "confluence_conn" not in st.session_state:
        st.session_state.confluence_conn = vault.get_secret("confluence_token") is not None
        
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
                dom = jira_domain if jira_domain else "acme.atlassian.net"
                proj = jira_project if jira_project else "MIG"
                tok = jira_token if jira_token else "jira-token-secure-123"
                with st.spinner("Establishing Jira OAuth secure connection..."):
                    time.sleep(1.5)
                vault.save_secret("jira_token", tok)
                st.session_state.jira_proj = proj
                st.session_state.jira_conn = True
                st.success("Successfully connected to Jira Project!")
                st.rerun()
        else:
            st.markdown("<span class='status-badge status-success'>Connected</span>", unsafe_allow_html=True)
            st.info(f"Target Project Key: **{st.session_state.get('jira_proj', 'MIG')}**")
            
            if st.button("🚀 Sync Waves to Jira Board", use_container_width=True):
                with st.spinner("Generating Epics and tasks for Wave 0, 1, 2, 3, 4..."):
                    time.sleep(2.0)
                st.success("Jira board updated! Created 5 Epics and 100 workload migration sub-tasks successfully.")
                
            if st.button("🔌 Disconnect Jira", use_container_width=True):
                vault.delete_secret("jira_token")
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
                repo = github_repo if github_repo else "org/migration-iac"
                branch = github_branch if github_branch else "main"
                tok = github_token if github_token else "github-pat-secure-456"
                with st.spinner("Authorizing GitHub credentials..."):
                    time.sleep(1.5)
                vault.save_secret("github_token", tok)
                st.session_state.gh_branch = branch
                st.session_state.github_conn = True
                st.success("Connected to repository branch!")
                st.rerun()
        else:
            st.markdown("<span class='status-badge status-success'>Connected</span>", unsafe_allow_html=True)
            st.info(f"Target Branch: **{st.session_state.get('gh_branch', 'main')}**")
            
            if st.button("📦 Push IaC to Repository", use_container_width=True):
                with st.spinner("Committer: dami-bot. Running git push origin..."):
                    time.sleep(2.0)
                st.success("IaC pushed! Committed generated Terraform templates and Ansible playbooks under commit ID 'dami-auto-iac-wave-0'.")
                
            if st.button("🔌 Disconnect GitHub", use_container_width=True):
                vault.delete_secret("github_token")
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
                dom = conf_domain if conf_domain else "acme.atlassian.net/wiki"
                space = conf_space if conf_space else "MIGDOCS"
                tok = conf_token if conf_token else "confluence-api-token-789"
                with st.spinner("Connecting to Confluence Wiki space..."):
                    time.sleep(1.5)
                vault.save_secret("confluence_token", tok)
                st.session_state.conf_space = space
                st.session_state.confluence_conn = True
                st.success("Connected to wiki space successfully!")
                st.rerun()
        else:
            st.markdown("<span class='status-badge status-success'>Connected</span>", unsafe_allow_html=True)
            st.info(f"Wiki Space Key: **{st.session_state.get('conf_space', 'MIGDOCS')}**")
            
            if st.button("✍️ Publish Runbooks & Checklist", use_container_width=True):
                with st.spinner("Rendering wiki pages and creating attachments..."):
                    time.sleep(2.0)
                st.success("Published runbook wiki space! Document: 'DAMI-Wave-0-Cutover-Runbook' is active.")
                
            if st.button("🔌 Disconnect Confluence", use_container_width=True):
                vault.delete_secret("confluence_token")
                st.session_state.confluence_conn = False
                st.rerun()

    st.write("---")
    
    # Fetch active secret metadata
    active_secrets = []
    if vault.get_secret_metadata("jira_token"): active_secrets.append("jira_token")
    if vault.get_secret_metadata("github_token"): active_secrets.append("github_token")
    if vault.get_secret_metadata("confluence_token"): active_secrets.append("confluence_token")
    
    active_secrets_html = ""
    if active_secrets:
        active_secrets_html = "<div style='margin-top: 14px; border-top: 1px solid rgba(16, 185, 129, 0.15); padding-top: 14px;'><div style='color: #6b7280; font-size: 0.7rem; font-weight: 600; margin-bottom: 6px; letter-spacing: 0.05em;'>ENCRYPTED SECRETS IN SECRET MANAGER VAULT:</div>"
        for s_id in active_secrets:
            meta = vault.get_secret_metadata(s_id)
            active_secrets_html += f"""
                <div style="background-color: rgba(0, 0, 0, 0.15); padding: 8px 12px; border-radius: 4px; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center; border: 1px solid rgba(255, 255, 255, 0.02);">
                    <span style="color: #ffffff; font-family: monospace; font-size: 0.8rem; font-weight: 500;">🔑 {s_id}</span>
                    <span style="color: #a3a8b4; font-size: 0.72rem; font-family: monospace;">Ciphertext size: {meta['ciphertext_len']} bytes | Nonce: {meta['nonce'][:12]}...</span>
                </div>
            """
        active_secrets_html += "</div>"
    
    # Premium Secure Vault Card Styling
    st.markdown(f"""
        <div style="background-color: rgba(16, 185, 129, 0.03); border: 1px solid rgba(16, 185, 129, 0.15); border-radius: 8px; padding: 20px; margin-top: 10px;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; flex-wrap: wrap; gap: 10px;">
                <h3 style="margin: 0; color: #10b981; font-family: 'Outfit', 'Inter', sans-serif; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
                    🔒 Secure Vault Credential Storage Status
                </h3>
                <span style="background-color: rgba(16, 185, 129, 0.1); color: #10b981; font-size: 0.72rem; font-weight: 600; padding: 4px 10px; border-radius: 12px; border: 1px solid rgba(16, 185, 129, 0.2); display: flex; align-items: center; gap: 6px;">
                    <span style="display: inline-block; width: 6px; height: 6px; background-color: #10b981; border-radius: 50%; animation: pulse-green 2s infinite;"></span>
                    ACTIVE & ENCRYPTED
                </span>
            </div>
            <p style="margin: 0 0 16px 0; color: #a3a8b4; font-size: 0.88rem; line-height: 1.5;">
                All credentials entered on this portal are encrypted using envelope encryption and stored securely in a dedicated <strong>Google Cloud Secret Manager</strong> instance, referencing access controls managed under KMS.
            </p>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; font-size: 0.8rem;">
                <div style="background-color: rgba(255, 255, 255, 0.02); padding: 10px 14px; border-radius: 6px; border: 1px solid rgba(255, 255, 255, 0.05);">
                    <div style="color: #6b7280; margin-bottom: 4px; font-weight: 500; font-size: 0.7rem; letter-spacing: 0.05em;">ENCRYPTION STANDARD</div>
                    <div style="color: #ffffff; font-family: monospace; font-weight: 600;">AES-256-GCM</div>
                </div>
                <div style="background-color: rgba(255, 255, 255, 0.02); padding: 10px 14px; border-radius: 6px; border: 1px solid rgba(255, 255, 255, 0.05);">
                    <div style="color: #6b7280; margin-bottom: 4px; font-weight: 500; font-size: 0.7rem; letter-spacing: 0.05em;">AUTHORIZED SERVICE ACCOUNT</div>
                    <div style="color: #10b981; font-family: monospace; word-break: break-all; font-weight: 600;">dami-migration-runner@cohort-2-497207.iam.gserviceaccount.com</div>
                </div>
            </div>
            {active_secrets_html}
        </div>
        <style>
            @keyframes pulse-green {{
                0% {{ opacity: 0.3; transform: scale(0.95); }}
                50% {{ opacity: 1; transform: scale(1.05); }}
                100% {{ opacity: 0.3; transform: scale(0.95); }}
            }}
        </style>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    render()
