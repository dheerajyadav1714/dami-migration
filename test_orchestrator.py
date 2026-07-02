# test_orchestrator.py
import sys
import os
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from agents.orchestrator import orchestrator_agent

def main():
    print("Initializing ADK Runner...")
    runner = Runner(
        agent=orchestrator_agent, 
        session_service=InMemorySessionService(), 
        app_name="DAMI_Migration",
        auto_create_session=True
    )
    
    prompt = "Please run the dependency mapper and summarize what you find."
    print(f"Running agent with prompt: '{prompt}'")
    
    new_message = types.Content(role="user", parts=[types.Part(text=prompt)])
    
    try:
        events = runner.run(
            user_id="test_user",
            session_id="test_session",
            new_message=new_message
        )
        print("\n--- Agent Streamed Events ---")
        for event in events:
            # Print the event representation or properties
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(part.text, end="", flush=True)
            # If it has function calls, let's print them
            calls = event.get_function_calls()
            if calls:
                print(f"\n[Agent Triggered Tools: {[c.name for c in calls]}]")
        print("\n------------------------------")
    except Exception as e:
        print(f"Error running agent: {e}")

if __name__ == "__main__":
    main()
