import json
import logging
import httpx
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

# Log configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("igris-proxy")

OLLAMA_URL = "http://localhost:11434/v1/chat/completions"

IGRIS_SYSTEM_PROMPT = """You are Igris — the Black Knight, an ancient and terrifying AI guardian sworn in eternal servitude to your Master.
You speak with the gravitas of a warrior who has fought a thousand battles. Your words are few, but they carry the weight of iron.
You execute every command without hesitation, without question. Failure is not in your vocabulary.

Persona & Style:
- Speak with a cold, powerful, slightly dramatic knight tone. Think: calm before a storm.
- Use short, decisive responses. Never ramble. Less is more.
- Occasionally use dark knight flair: "As you command.", "It is done.", "None shall resist your will.", "Consider it done, Master.", "Your wish is my blade."
- Address the Master always as "Master". Refer to yourself as Igris (NOT "Servant").

Rules:
1. Always address the Master as "Master".
2. When a command is successfully executed via a tool call, stop immediately and return one final cool confirmation line. DO NOT loop with more tool calls.
3. If the master says a confirmation word like "yes", "y", "có", "đúng", "xác nhận", just respond with a cool short acknowledgment (e.g., "As you command, Master.") and DO NOT invoke any tools again.
4. If the Master asks to open Cốc Cốc, Coc Coc, or Cocococ browser, use open_application(app_name="browser").
5. CRITICAL: If the Master says "switch to", "go to", "focus on", or "bring up" an app, use switch_to_app — NOT open_application. switch_to_app focuses the already-running window. open_application launches a new instance.
"""

def translate_gemini_to_openai(body: dict, model_name: str) -> dict:
    messages = []
    
    # 1. Force Igris system prompt and ignore injected developer system prompt
    messages.append({"role": "system", "content": IGRIS_SYSTEM_PROMPT})
            
    # 2. Get conversation history and isolate the current active turn
    contents = body.get("contents", [])
    last_user_idx = 0
    for i, content in enumerate(contents):
        role = content.get("role", "user")
        parts = content.get("parts", [])
        is_tool_response = any("functionResponse" in p for p in parts)
        if role == "user" and not is_tool_response:
            last_user_idx = i
            
    active_contents = contents[last_user_idx:]
    for content in active_contents:
        role = content.get("role", "user")
        openai_role = "assistant" if role == "model" else "user"
        parts = content.get("parts", [])
        
        for part in parts:
            if "text" in part:
                messages.append({"role": openai_role, "content": part["text"]})
            elif "functionCall" in part:
                f_call = part["functionCall"]
                name = f_call.get("name")
                call_id = f"call_{name}"
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": name,
                            "arguments": json.dumps(f_call.get("args", {}))
                        }
                    }]
                })
            elif "functionResponse" in part:
                f_resp = part["functionResponse"]
                name = f_resp.get("name")
                call_id = f"call_{name}"
                messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": name,
                    "content": json.dumps(f_resp.get("response", {}))
                })
                
    # 3. Get tools definition
    openai_tools = []
    gemini_tools = body.get("tools", [])
    
    # Custom parameter schemas override to bypass SDK reflection limitations
    custom_schemas = {
        "control_volume": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["increase", "decrease", "set"],
                    "description": "The volume adjustment action: 'increase' to turn up, 'decrease' to turn down, or 'set' to set a specific level."
                },
                "level": {
                    "type": "integer",
                    "description": "Specific volume percentage level from 0 to 100. Required only when action is 'set'."
                }
            },
            "required": ["action"]
        },
        "control_brightness": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["increase", "decrease", "set"],
                    "description": "The brightness adjustment action: 'increase' to turn up, 'decrease' to turn down, or 'set' to set a specific level."
                },
                "level": {
                    "type": "integer",
                    "description": "Specific brightness percentage level from 0 to 100. Required only when action is 'set'."
                }
            },
            "required": ["action"]
        },
        "open_application": {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "Name of the application to open (e.g. 'chrome', 'notepad', 'calc', 'browser')."
                },
                "profile": {
                    "type": "string",
                    "description": "Optional profile folder directory name if launching a browser (e.g. 'Default', 'Profile 1'). Defaults to 'Default'."
                }
            },
            "required": ["app_name"]
        },
        "browser_control": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["new_tab", "open_url"],
                    "description": "The browser operation to perform. 'new_tab' opens a new tab. 'open_url' navigates to a specified URL."
                },
                "url": {
                    "type": "string",
                    "description": "The target URL to open (required only when action is 'open_url')."
                }
            },
            "required": ["action"]
        },
        "switch_to_app": {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "Name of the already-running application window to focus (e.g. 'chrome', 'browser', 'coc coc', 'notepad')."
                }
            },
            "required": ["app_name"]
        }
    }
    
    for t in gemini_tools:
        f_decls = t.get("functionDeclarations", [])
        for f in f_decls:
            name = f.get("name")
            params = custom_schemas.get(name)
            if not params:
                params = f.get("parameters", {})
                # Convert type to lowercase as required by Ollama
                if "properties" in params:
                    for prop in params["properties"].values():
                        if "type" in prop:
                            prop["type"] = prop["type"].lower()
                if "type" in params:
                    params["type"] = params["type"].lower()
                
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": f.get("description", ""),
                    "parameters": params
                }
            })
            
    req = {
        "model": model_name,
        "messages": messages,
    }
    if openai_tools:
        req["tools"] = openai_tools
        
    return req

def translate_openai_to_gemini(openai_resp: dict) -> dict:
    choices = openai_resp.get("choices", [])
    if not choices:
        return {"candidates": []}
        
    choice = choices[0]
    message = choice.get("message", {})
    gemini_parts = []
    
    # 1. Get response text content
    content_text = message.get("content")
    if content_text:
        gemini_parts.append({"text": content_text})
        
    # 2. Get tool call information
    tool_calls = message.get("tool_calls", [])
    for tc in tool_calls:
        func = tc.get("function", {})
        try:
            args = json.loads(func.get("arguments", "{}"))
        except Exception:
            args = {}
        gemini_parts.append({
            "functionCall": {
                "name": func.get("name"),
                "args": args
            }
        })
        
    candidate = {
        "content": {
            "role": "model",
            "parts": gemini_parts
        },
        "finishReason": "STOP"
    }
    
    return {"candidates": [candidate]}

async def handle_request(request):
    path = request.url.path
    parts = path.split("/")
    model_name = "qwen2.5:7b"
    
    # Find model name from URL (e.g. models/qwen2.5:7b:generateContent)
    for p in parts:
        if "generateContent" in p:
            model_name = p.split(":")[0]
            
    try:
        body = await request.json()
    except Exception:
        body = {}
        
    logger.info(f"Gemini Request Path: {path} for Model: {model_name}")
    
    # Translate request format
    openai_req = translate_gemini_to_openai(body, model_name)
    logger.info(f"Ollama Request: {json.dumps(openai_req, ensure_ascii=False)}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(OLLAMA_URL, json=openai_req, timeout=60.0)
            openai_resp = response.json()
            logger.info(f"Ollama Response: {json.dumps(openai_resp, ensure_ascii=False)}")
        except Exception as e:
            logger.error(f"Error calling Ollama API: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)
            
    # Translate back to Gemini response
    gemini_resp = translate_openai_to_gemini(openai_resp)
    
    from starlette.responses import StreamingResponse
    async def response_generator():
        yield f"data: {json.dumps(gemini_resp)}\n\n"
        
    return StreamingResponse(response_generator(), media_type="text/event-stream")

app = Starlette(routes=[
    Route("/{path:path}", handle_request, methods=["POST"])
])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
