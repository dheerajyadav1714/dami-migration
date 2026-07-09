# stakeholders.py
import streamlit as st
import os
import pandas as pd
from google.cloud import bigquery
from google.genai import Client
from google.genai import types

def generate_stakeholder_content(wave_name: str, server_count: int, apps: str, use_vertex: bool, project_id: str, location: str):
    prompt = f"""
    You are an enterprise migration project manager. 
    Create a detailed stakeholder communication package for the upcoming cloud migration wave.
    
    Wave Details:
    - Wave Name: {wave_name}
    - Total Servers: {server_count}
    - Key Applications: {apps}
    
    Provide output exactly in this format using Markdown:
    
    ### 1. RACI Matrix
    Create a markdown table with columns: Task, Responsible, Accountable, Consulted, Informed. Include 5-6 key migration tasks.
    
    ### 2. Stakeholder Notification Email (T-minus 14 Days)
    Write a professional email template notifying business owners about the upcoming downtime window. Include placeholders for dates.
    
    ### 3. Cutover Completion Email
    Write a short success notification email template for post-migration.
    """
    
    model_name = "gemini-2.5-pro"
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        client = Client(api_key=api_key)
    else:
        client = Client(enterprise=True)
        model_name = f"projects/{os.getenv('VERTEX_PROJECT_ID', 'gcp-experiments-490315')}/locations/{location}/publishers/google/models/{model_name}"

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.3)
        )
        return response.text
    except Exception as e:
        return f"Failed to generate content: {e}"

def render():
    st.markdown("<h1 class='gradient-text'>Stakeholder Communications</h1>", unsafe_allow_html=True)
    st.write("Automatically generate RACI matrices and standardized email notifications for your business unit owners and stakeholders.")
    st.write("---")
    
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_v3")
    
    try:
        bq_client = bigquery.Client(project=project_id)
        df = bq_client.query(f"SELECT wave_id, wave_name, wave_number FROM `{project_id}.{dataset}.waves` ORDER BY wave_number").to_dataframe()
    except:
        df = pd.DataFrame()
        
    if df.empty:
        st.warning("No migration waves found. Please generate waves in the Wave Planner first.")
        return
        
    wave_options = [f"Wave {row['wave_number']}: {row['wave_name']}" for _, row in df.iterrows()]
    selected_wave = st.selectbox("Select Target Wave", wave_options)
    
    idx = wave_options.index(selected_wave)
    wave_id = df.iloc[idx]["wave_id"]
    wave_name = df.iloc[idx]["wave_name"]
    
    # Get server count and apps
    try:
        servers_df = bq_client.query(f"""
            SELECT s.name 
            FROM `{project_id}.{dataset}.wave_workloads` w 
            JOIN `{project_id}.{dataset}.servers` s ON w.server_id = s.server_id
            WHERE w.wave_id = '{wave_id}'
        """).to_dataframe()
        server_count = len(servers_df)
        apps = ", ".join(servers_df["name"].head(3).tolist()) + ("..." if server_count > 3 else "")
    except:
        server_count = 10
        apps = "Web, App, DB Tiers"
        
    if st.button("📝 Generate Comm Package", type="primary"):
        with st.spinner(f"Generating RACI & Templates for {wave_name}..."):
            vertex = not bool(os.getenv("GEMINI_API_KEY"))
            loc = os.getenv("VERTEX_AI_LOCATION", "us-central1")
            content = generate_stakeholder_content(wave_name, server_count, apps, vertex, project_id, loc)
            
            st.success("Communications Package Generated!")
            st.markdown(content)
            
            st.download_button(
                label="💾 Download Package (Markdown)",
                data=content,
                file_name=f"stakeholder_comm_{wave_id}.md",
                mime="text/markdown"
            )

if __name__ == "__main__":
    render()
