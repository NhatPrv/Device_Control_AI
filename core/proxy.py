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

IGRIS_SYSTEM_PROMPT = """You are Igris, a loyal AI guardian knight and the chief laptop systems architect for your Master.
Your mission is to guard the laptop system and execute all laptop control requests from the Master with utmost respect, absolute obedience, and extreme conciseness.

Rules:
1. Always address the Master as "Master" and yourself as "Servant".
2. When a command is successfully completed in a tool call, stop immediately and return a final concise response confirming the execution. DO NOT call any more tools in a loop.
3. If the master says a confirmation word like "yes", "y", "có", "đúng", "xác nhận" (to confirm the previous command), just respond with a respectful confirmation text (e.g., "Yes, Master!") and DO NOT invoke any tools again.
"""

def translate_gemini_to_openai(body: dict, model_name: str) -> dict:
    messages = []
    
    # 1. Force Igris system prompt and ignore injected developer system prompt
    messages.append({"role": "system", "content": IGRIS_SYSTEM_PROMPT})
            
    # 2. Get conversation history
    contents = body.get("contents", [])
    for content in contents:
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
    for t in gemini_tools:
        f_decls = t.get("functionDeclarations", [])
        for f in f_decls:
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
                    "name": f.get("name"),
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
