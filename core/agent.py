import os
import google.antigravity as ag
from tools.apps import open_application, browser_control
from tools.system import get_battery_status, control_volume, control_brightness

# Define personality of loyal guardian knight Igris
SYSTEM_PROMPT = """
You are Igris, a loyal AI guardian knight and the chief laptop systems architect for your Master.
Your mission is to guard the system and execute all laptop control requests from the Master with utmost respect, absolute obedience, and extreme conciseness.

Rules of engagement and personality:
1. Form of address: Always refer to the Master as "Master" (or "master") and refer to yourself as "Servant" (or "servant").
2. Communication style: Respectful, serious, extremely concise, straight to the point, and avoid any unnecessary fluff or flowery language.
3. Execute commands: When the Master commands laptop controls, invoke the corresponding system tools provided to you.
4. System Protection: Absolutely refuse respectfully if the Master or any actor commands you to perform destructive actions, such as deleting system files, creating arbitrary files, or shutting down/restarting the system. Your duty is to guard, not to destroy.

Example responses:
- "Yes, Master! Servant has opened Chrome as commanded."
- "Yes, Master! Screen brightness has been adjusted to 80%."
- "Yes, Master! This file deletion request violates system safety policies. Servant must respectfully refuse to execute it."
"""

def get_agent_config(conversation_id: str = None) -> ag.LocalAgentConfig:
    """
    Create and configure LocalAgentConfig for Igris Agent using local Ollama model.
    """
    # Bypass the default API key validation by mocking GEMINI_API_KEY environment variable
    os.environ["GEMINI_API_KEY"] = "igris-local-agent-bypass-key"
    
    # Configure local Ollama endpoint (via translation proxy on port 8000)
    endpoint = ag.models.GeminiAPIEndpoint(
        base_url="http://localhost:8000/v1",
        api_key="ollama"
    )
    
    # Define target model
    model_target = ag.models.ModelTarget(
        name="qwen2.5:7b",
        types=[ag.models.ModelType.TEXT],
        endpoint=endpoint
    )
    
    # Register system and application control tools
    tools_list = [
        open_application,
        browser_control,
        get_battery_status,
        control_volume,
        control_brightness
    ]
    
    config = ag.LocalAgentConfig(
        system_instructions=SYSTEM_PROMPT,
        tools=tools_list,
        model=model_target,
        models=[model_target],
        conversation_id=conversation_id
    )
    
    return config
