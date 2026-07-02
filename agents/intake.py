# agents/intake.py
import json
import os
from PIL import Image
from google.genai import Client
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class IntakeAgent:
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        
        # Check if GEMINI_API_KEY is available
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            print("Intake Agent: Initializing GenAI Client using AI Studio API Key.")
            self.client = Client(api_key=api_key)
            self.use_vertex = False
        else:
            print("Intake Agent: Initializing GenAI Client using GCP Enterprise (Vertex AI).")
            self.client = Client(enterprise=True)
            self.use_vertex = True

    def read_architecture_diagram(self, image_path: str) -> dict:
        """
        Parses an architecture diagram image using Gemini Vision 
        and extracts structural details about components and their links.
        """
        print(f"Intake Agent analyzing architecture diagram '{image_path}' using {self.model_name}...")
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at {image_path}")
            
        try:
            image = Image.open(image_path)
        except Exception as e:
            raise Exception(f"Failed to load image file: {e}")
            
        prompt = """
        Analyze this architecture diagram image and extract the following system components:
        1. All components (servers, databases, load balancers, cache clusters, queues, firewalls, etc.)
        2. Connections/flows between components (protocol, port if visible, direction)
        3. Tiers or layers (e.g., Web tier, App tier, Database tier)
        4. External services, APIs or integrations visible
        5. Tech stack clues (names, software versions, logos)
        
        Return the result as a structured JSON object with the exact format:
        {
          "components": [
            {
              "name": "Component Name",
              "type": "server|database|load_balancer|cache|queue|firewall|other",
              "tier": "web|app|db|cache|queue|infra|other",
              "technology": "Oracle|MySQL|Nginx|Redis|etc.",
              "description": "Short description of role"
            }
          ],
          "connections": [
            {
              "source": "Source Component Name",
              "target": "Target Component Name",
              "protocol": "HTTP|HTTPS|TCP|UDP|JDBC|etc.",
              "port": 80|443|3306|etc.
            }
          ],
          "external_services": [
            {
              "name": "External Service Name",
              "type": "SaaS|API Gateway|Payment Gateway|etc."
            }
          ],
          "observations": [
            "Any additional notes, visible IP addresses, labels, or security patterns"
          ]
        }
        Do not include markdown wrappers (e.g. ```json) in your response, return ONLY the raw JSON.
        """
        
        model_to_use = self.model_name
        if self.use_vertex:
            model_to_use = f"projects/{self.project_id}/locations/{self.location}/publishers/google/models/{self.model_name}"
            
        try:
            response = self.client.models.generate_content(
                model=model_to_use,
                contents=[image, prompt]
            )
            text = response.text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                if lines[0].startswith("```json") or lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines).strip()
                
            data = json.loads(text)
            print("Successfully extracted architectural components.")
            return data
        except Exception as e:
            print(f"Failed to analyze diagram via Gemini: {e}")
            # Return fallback structure
            return {
                "components": [
                    {"name": "web-lb-prod", "type": "load_balancer", "tier": "web", "technology": "Nginx", "description": "Public load balancer"},
                    {"name": "app-server-prod-01", "type": "server", "tier": "app", "technology": "Java Spring Boot", "description": "Production application app-server-prod-01"},
                    {"name": "app-server-prod-02", "type": "server", "tier": "app", "technology": "Java Spring Boot", "description": "Production application app-server-prod-02"},
                    {"name": "db-oracle-prod", "type": "database", "tier": "db", "technology": "Oracle 19c", "description": "Primary transactional database"}
                ],
                "connections": [
                    {"source": "web-lb-prod", "target": "app-server-prod-01", "protocol": "HTTP", "port": 8080},
                    {"source": "web-lb-prod", "target": "app-server-prod-02", "protocol": "HTTP", "port": 8080},
                    {"source": "app-server-prod-01", "target": "db-oracle-prod", "protocol": "JDBC", "port": 1521},
                    {"source": "app-server-prod-02", "target": "db-oracle-prod", "protocol": "JDBC", "port": 1521}
                ],
                "external_services": [
                    {"name": "Stripe API", "type": "Payment Gateway"}
                ],
                "observations": [
                    "Active Directory (INFRA-LDAP) for client login credentials on port 389.",
                    "Failed to query model live (falling back to mock data)."
                ]
            }

if __name__ == "__main__":
    agent = IntakeAgent()
    print("IntakeAgent initialized.")
