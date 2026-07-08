import asyncio
import sys
import os
import subprocess
import threading
import pythoncom
import win32com.client
import google.antigravity as ag
from core.stt import STTManager
from core.agent import get_agent_config

# Set UTF-8 encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

BANNER = """
===================================================================
             ⚔   LAPTOP GUARDIAN KNIGHT - IGRIS LOCAL  ⚔   
===================================================================
  - Multilingual real-time CUDA STT via Faster-Whisper.
  - Local Qwen 2.5 7B model execution via Ollama.
  - Supported tools: Volume, brightness, battery, applications.
  - Wake word command: "Hey Igris".
  - Exit command: "Retreat".
===================================================================
"""

def parse_wake_word(speech: str) -> tuple[bool, str]:
    """
    Checks if the speech contains any phonetic variation of the name "Igris" as a wake word.
    Returns (is_woken, command_part).
    """
    speech_lower = speech.lower().strip()
    
    # Core phonetic variations and common mis-transcriptions of the name "Igris"
    core_wake_words = [
        "igris", "egris", "e-gris", "igres", "igrees",
        "i gris", "i-gris", "hey gris", "hay gris", "hai gris", "hi gris",
        "i'm chris", "im chris", "i creed", "i greed",
        "i quit", "i creeped", "i agree", "i'm free",
        "im free", "i think", "i eat it", "ikuri", "イクリー"
    ]
    
    for word in core_wake_words:
        idx = speech_lower.find(word)
        if idx != -1:
            # Extract the command trailing the wake word and strip common punctuation
            command_part = speech[idx + len(word):].strip(",.?!;\"' ")
            if not any(c.isalnum() for c in command_part):
                command_part = ""
            return True, command_part
            
    return False, ""

def clear_screen():
    """
    Clears the console screen.
    """
    os.system('cls' if os.name == 'nt' else 'clear')

def speak(text: str):
    """
    Speak the given text using Windows SAPI TTS with a deep, dramatic male voice.
    Runs asynchronously in a background thread so it does not block the main event loop.
    """
    def _speak():
        pythoncom.CoInitialize()
        try:
            sapi = win32com.client.Dispatch('SAPI.SpVoice')
            # Select deep male voice (Microsoft David) for a cool knight feel
            voices = sapi.GetVoices()
            for i in range(voices.Count):
                if 'David' in voices.Item(i).GetDescription():
                    sapi.Voice = voices.Item(i)
                    break
            sapi.Rate = 1   # +25% faster: -1 was slightly slow, 1 is crisp and commanding
            sapi.Volume = 100
            sapi.Speak(text)
        except Exception:
            pass
        finally:
            pythoncom.CoUninitialize()
    threading.Thread(target=_speak, daemon=True).start()

async def execute_command(agent, command: str):
    """
    Send the command to the Agent to process tool calls and display the response.
    """
    try:
        print("Igris: Executing command...")
        response = await agent.chat(command)
        reply_text = await response.text()
        
        # Clean response, remove internal SDK logging lines
        clean_lines = []
        for line in reply_text.splitlines():
            if not any(log_key in line for log_key in ["thora_plugin", "Logged response", "System step"]):
                clean_lines.append(line)
        final_reply = "\n".join(clean_lines).strip()
        
        print(f"\n[Igris]: {final_reply}")
        speak(final_reply)
    except Exception as e:
        err_msg = f"Error while executing command: {e}"
        print(f"\n[Igris]: {err_msg}")
        speak("Master, an error occurred while executing the command.")

async def main():
    # 1. Start proxy on port 8000 in background and log to proxy.log
    proxy_path = os.path.join(os.path.dirname(__file__), "core", "proxy.py")
    log_file = open("proxy.log", "w", encoding="utf-8")
    try:
        proxy_process = subprocess.Popen(
            [sys.executable, proxy_path],
            stdout=log_file,
            stderr=log_file
        )
    except Exception as e:
        print(f"Error: Unable to start local proxy port: {e}")
        log_file.close()
        return
        
    # Wait 2 seconds for proxy to start up completely
    await asyncio.sleep(2.0)
    
    try:
        # 2. Initialize STT with English language and Agent config
        stt_manager = STTManager(language="en")
        config = get_agent_config()
        
        # 3. Start communication session with Agent
        async with ag.Agent(config) as agent:
            print("\nIgris: Standby...")
                
            while True:
                speech = await stt_manager.listen()
                if not speech:
                    continue
                
                speech_lower = speech.lower().strip()
                
                # Exit on "Retreat"
                if "retreat" in speech_lower:
                    msg = "As you wish, Master. Igris retreats into the shadows."
                    print(f"\n[Igris]: {msg}")
                    speak(msg)
                    break
                    
                # Wake up check
                is_woken, command_part = parse_wake_word(speech)
                if is_woken:
                    # Clear screen immediately upon wake word detection
                    clear_screen()
                    
                    # Ask Master what they want
                    wake_msg = "Yes, Master! What do you want?"
                    print(f"\n[Igris]: {wake_msg}")
                    speak(wake_msg)
                        
                    # Wait for command (no timeout)
                    command = await stt_manager.listen()
                    if not command:
                        print("\nIgris: Standby...")
                        continue
                        
                    cmd_lower = command.lower().strip()
                    if "retreat" in cmd_lower:
                        msg = "As you wish, Master. Igris retreats into the shadows."
                        print(f"\n[Igris]: {msg}")
                        speak(msg)
                        break
                        
                    # Check for immediate cancel
                    if cmd_lower in ["cancel", "stop", "reject"]:
                        cancel_msg = "Command dismissed, Master."
                        print(f"\n[Igris]: {cancel_msg}")
                        speak(cancel_msg)
                        print("\nIgris: Standby...")
                        continue
                        
                    # Ask for confirmation
                    confirm_prompt = f'You want me to "{command}", correct?'
                    print(f"\n[Igris]: {confirm_prompt}")
                    speak(confirm_prompt)
                        
                    # Listen for confirmation (no timeout)
                    confirm_speech = await stt_manager.listen()
                    if not confirm_speech:
                        cancel_msg = "No response received. Command dismissed, Master."
                        print(f"\n[Igris]: {cancel_msg}")
                        speak(cancel_msg)
                        print("\nIgris: Standby...")
                        continue
                        
                    confirm_lower = confirm_speech.lower().strip()
                    yes_keywords = ["yes", "y", "confirm", "correct", "sure", "ok", "accept", "approve", "agree", "proceed"]
                    no_keywords = ["no", "n", "cancel", "incorrect", "stop", "reject", "deny", "refuse", "decline"]
                        
                    is_yes = any(kw in confirm_lower for kw in yes_keywords)
                    is_no = any(kw in confirm_lower for kw in no_keywords)
                    
                    if is_yes and not is_no:
                        exec_msg = "As you command, Master. Executing now."
                        print(f"\n[Igris]: {exec_msg}")
                        speak(exec_msg)
                        await execute_command(agent, command)
                    else:
                        cancel_msg = "Command dismissed, Master."
                        print(f"\n[Igris]: {cancel_msg}")
                        speak(cancel_msg)
                            
                    # Back to standby
                    print("\nIgris: Standby...")
                else:
                    continue
                        
    finally:
        # Stop proxy when exit
        print("\nIgris: Disconnecting ports...")
        try:
            proxy_process.terminate()
            proxy_process.wait()
        except Exception:
            pass
        try:
            log_file.close()
        except Exception:
            pass
        print("Igris: Disconnected successfully.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nIgris: Force stopped by user request.")
