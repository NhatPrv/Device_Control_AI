import asyncio
import sys
import os
import subprocess
import google.antigravity as ag
from core.stt import STTManager
from core.agent import get_agent_config

# Set UTF-8 encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

BANNER = """
===================================================================
             ⚔️   LAPTOP GUARDIAN KNIGHT - IGRIS LOCAL  ⚔️
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
    Checks if the speech contains any phonetic variation of the wake word "Hey Igris".
    Returns (is_woken, command_part).
    """
    speech_lower = speech.lower().strip()
    
    # List of common mis-transcriptions/phonetic variations of "Hey Igris" by Whisper
    wake_variations = [
        "hey igris", "hey egris", "hey e-gris", "hey igres", "hey igrees",
        "hey, i'm chris", "hey im chris", "hey i'm chris",
        "hey, i creed", "hey i creed", "hey i greed", "hey i greed",
        "hey, i quit", "hey i quit",
        "hey, i creeped", "hey i creeped",
        "hey, i agree", "hey i agree",
        "hey, i'm free", "hey im free",
        "hey, i think", "hey i think",
        "i eat it", "i'll be up for it", "ill be up for it",
        "hay igris", "hai igris",
        "ハイイクリー", "はい いくり", "hai ikuri"
    ]
    
    for var in wake_variations:
        idx = speech_lower.find(var)
        if idx != -1:
            # Extract the command trailing the wake word
            command_part = speech[idx + len(var):].strip(",. ")
            return True, command_part
            
    return False, ""

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
    except Exception as e:
        print(f"\n[Igris]: Error while executing command: {e}")

async def main():
    print(BANNER)
    
    # 1. Start proxy on port 8000 in background
    print("Igris: Setting up local API connection port...")
    proxy_path = os.path.join(os.path.dirname(__file__), "core", "proxy.py")
    
    try:
        proxy_process = subprocess.Popen(
            [sys.executable, proxy_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        print(f"Error: Unable to start local proxy port: {e}")
        return
        
    # Wait 2 seconds for proxy to start up completely
    await asyncio.sleep(2.0)
    
    try:
        # 2. Initialize STT and Agent config
        stt_manager = STTManager()
        config = get_agent_config()
        
        # 3. Start communication session with Agent
        print("Igris: Summoning guardian knight...")
        async with ag.Agent(config) as agent:
            print("\nIgris: Greetings Master! I am standby and ready to guard the system.")
            
            waiting_for_wake = True
            
            while True:
                if waiting_for_wake:
                    print("\n--- 🛡️ IGRIS STANDBY - WAITING FOR WAKE WORD (\"Hey Igris\")... ---")
                    speech = await stt_manager.listen()
                    if not speech:
                        continue
                    
                    speech_lower = speech.lower().strip()
                    
                    # Exit on "Retreat"
                    if "retreat" in speech_lower:
                        print("\n[Igris]: Retreating as commanded. Have a great day, Master!")
                        break
                        
                    # Wake up check
                    is_woken, command_part = parse_wake_word(speech)
                    if is_woken:
                        if command_part:
                            if "retreat" in command_part.lower():
                                print("\n[Igris]: Retreating as commanded. Have a great day, Master!")
                                break
                            print(f"\n[Igris]: Yes, Master! Executing direct command: \"{command_part}\"")
                            await execute_command(agent, command_part)
                        else:
                            print("\n[Igris]: Yes, Master! I am listening to your command.")
                            waiting_for_wake = False
                    else:
                        continue
                else:
                    print("\n--- 🎤 LISTENING FOR MASTER'S COMMAND (15s timeout)... ---")
                    try:
                        # Set 15 seconds timeout for command input
                        command = await asyncio.wait_for(stt_manager.listen(), timeout=15.0)
                        if not command:
                            continue
                            
                        cmd_lower = command.lower().strip()
                        if "retreat" in cmd_lower:
                            print("\n[Igris]: Retreating as commanded. Have a great day, Master!")
                            break
                            
                        await execute_command(agent, command)
                    except asyncio.TimeoutError:
                        print("\n[Igris]: Standby timeout (15s). Returning to wake-word standby mode.")
                    finally:
                        # Go back to wake word standby mode
                        waiting_for_wake = True
                    
    finally:
        # Stop proxy when exit
        print("\nIgris: Disconnecting ports...")
        proxy_process.terminate()
        proxy_process.wait()
        print("Igris: Disconnected successfully.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nIgris: Force stopped by user request.")
