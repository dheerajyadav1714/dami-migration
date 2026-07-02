# main.py
import os
import sys
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.discovery import DiscoveryAgent
from agents.risk_scorer import RiskScorerAgent
from agents.wave_planner import WavePlannerAgent

load_dotenv()

app = FastAPI(
    title="D.A.M.I. API Server",
    description="Discovery & Autonomous Migration Intelligence Backend Service",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AgentRunRequest(BaseModel):
    project_id: str
    phase: str  # discovery, risk, wave, artifacts
    wave_number: int = None

class OrchestratorRunRequest(BaseModel):
    prompt: str

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "D.A.M.I. Backend API",
        "project": os.getenv("GCP_PROJECT_ID"),
        "version": "1.0.0"
    }

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    source_type: str = Form("vmware")
):
    print(f"Received file upload '{file.filename}' for source '{source_type}'...")
    
    # Save file to temp location
    temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "seed")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"uploaded_{file.filename}")
    
    try:
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            
        # Ingest using Discovery Agent
        agent = DiscoveryAgent()
        res = agent.normalize_and_load(temp_path, source_type=source_type)
        return {
            "status": "success",
            "message": f"Successfully loaded {res['loaded_count']} servers from {file.filename}.",
            "loaded_count": res["loaded_count"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process inventory: {str(e)}")

@app.post("/api/run-agent")
def run_agent(req: AgentRunRequest):
    print(f"Triggering phase '{req.phase}' for project '{req.project_id}'...")
    
    try:
        if req.phase == "discovery":
            # Running Discovery seeding/normalization
            seed_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "seed", "sample_rvtools.csv")
            if not os.path.exists(seed_file):
                # Auto generate if not exists
                from scripts.seed_database import main as run_seeding
                run_seeding()
                return {"status": "success", "message": "Database successfully seeded with 100 VMs, apps, and dependencies."}
            else:
                agent = DiscoveryAgent()
                res = agent.normalize_and_load(seed_file, source_type="vmware")
                return {"status": "success", "message": f"Discovered {res['loaded_count']} servers."}
                
        elif req.phase == "risk":
            agent = RiskScorerAgent()
            res = agent.assess_workloads()
            return {"status": "success", "message": f"Assessed and categorized {res['assessed_count']} servers."}
            
        elif req.phase == "wave":
            agent = WavePlannerAgent()
            res = agent.create_migration_waves()
            return {"status": "success", "message": f"Scheduled workloads into {res['waves_count']} migration waves."}
            
        elif req.phase == "artifacts":
            from agents.artifacts_generator import ArtifactsGeneratorAgent
            agent = ArtifactsGeneratorAgent()
            wave_num = req.wave_number if req.wave_number is not None else 0
            res = agent.generate_wave_artifacts(wave_num)
            return {
                "status": "success", 
                "message": f"Successfully generated IaC and Runbooks for Wave {wave_num}.",
                "artifacts_summary": res
            }
            
        else:
            raise HTTPException(status_code=400, detail="Invalid phase type. Select: discovery, risk, wave, artifacts")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")

@app.post("/api/run-orchestrator")
def run_orchestrator(req: OrchestratorRunRequest):
    print(f"Triggering Orchestrator with prompt: '{req.prompt}'...")
    try:
        from google.adk import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types
        from agents.orchestrator import orchestrator_agent
        
        runner = Runner(
            agent=orchestrator_agent,
            session_service=InMemorySessionService(),
            app_name="DAMI_Migration",
            auto_create_session=True
        )
        
        new_message = types.Content(role="user", parts=[types.Part(text=req.prompt)])
        events = runner.run(
            user_id="api_user",
            session_id="api_session",
            new_message=new_message
        )
        
        triggered_tools = []
        final_response = ""
        
        for event in events:
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        final_response = part.text
            calls = event.get_function_calls()
            if calls:
                triggered_tools.extend([c.name for c in calls])
                
        return {
            "status": "success",
            "triggered_tools": triggered_tools,
            "final_response": final_response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Orchestrator failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
