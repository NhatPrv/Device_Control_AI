import asyncio
import sys
import os
import subprocess
import tkinter as tk
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

def select_language_dialog() -> str:
    """
    Shows a GUI popup dialog using Tkinter to select the preferred language.
    Returns 'en' or 'vi'.
    """
    selected = "en"
    
    root = tk.Tk()
    root.title("Igris - Select Language")
    root.geometry("320x150")
    root.resizable(False, False)
    # Center window
    root.eval('tk::PlaceWindow . center')
    
    # Label
    label = tk.Label(
        root, 
        text="Select Preferred Language:\nChọn Ngôn Ngữ Bạn Muốn Dùng:", 
        font=("Arial", 11),
        justify=tk.CENTER
    )
    label.pack(pady=15)
    
    def set_en():
        nonlocal selected
        selected = "en"
        root.destroy()
        
    def set_vi():
        nonlocal selected
        selected = "vi"
        root.destroy()
        
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=5)
    
    btn_en = tk.Button(btn_frame, text="English (en)", command=set_en, width=13, font=("Arial", 10))
    btn_en.pack(side=tk.LEFT, padx=12)
    
    btn_vi = tk.Button(btn_frame, text="Tiếng Việt (vi)", command=set_vi, width=13, font=("Arial", 10))
    btn_vi.pack(side=tk.LEFT, padx=12)
    
    # Set window on top
    root.attributes('-topmost', True)
    root.mainloop()
    
    return selected

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
    finally:
        try:
            agent.conversation.clear_history()
        except Exception:
            pass

async def main():
    # 1. Show GUI language selector popup first
    selected_lang = select_language_dialog()
    
    # 2. Start proxy on port 8000 in background and log to proxy.log
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
        # 3. Initialize STT with chosen language and Agent config
        stt_manager = STTManager(language=selected_lang)
        config = get_agent_config()
        
        # 4. Start communication session with Agent
        async with ag.Agent(config) as agent:
            # "sau khi config xong, trên terminal chỉ hiện thông báo đang nghe"
            if selected_lang == "vi":
                print("\nIgris: Đang lắng nghe...")
            else:
                print("\nIgris: Standby...")
                
            waiting_for_wake = True
            
            while True:
                speech = await stt_manager.listen()
                if not speech:
                    continue
                
                speech_lower = speech.lower().strip()
                
                # Exit on "Retreat"
                if "retreat" in speech_lower:
                    print("\n[Igris]: Retreating as commanded.")
                    break
                    
                # Wake up check
                is_woken, command_part = parse_wake_word(speech)
                if is_woken:
                    # Clear screen immediately upon wake word detection
                    clear_screen()
                    
                    # Ask Master what they want
                    if selected_lang == "vi":
                        print("\n[Igris]: Dạ, thưa Chủ nhân! Người muốn gì?")
                    else:
                        print("\n[Igris]: Yes, Master! What do you want?")
                        
                    # Wait for command (no timeout)
                    command = await stt_manager.listen()
                    if not command:
                        if selected_lang == "vi":
                            print("\nIgris: Đang lắng nghe...")
                        else:
                            print("\nIgris: Standby...")
                        continue
                        
                    cmd_lower = command.lower().strip()
                    if "retreat" in cmd_lower:
                        print("\n[Igris]: Retreating as commanded.")
                        break
                        
                    # Check for immediate cancel
                    if cmd_lower in ["cancel", "hủy", "huy"]:
                        if selected_lang == "vi":
                            print("\n[Igris]: Đã hủy lệnh.")
                            print("\nIgris: Đang lắng nghe...")
                        else:
                            print("\n[Igris]: Command canceled.")
                            print("\nIgris: Standby...")
                        continue
                        
                    # Ask for confirmation
                    if selected_lang == "vi":
                        print(f"\n[Igris]: Chủ nhân muốn \"{command}\" phải không?")
                    else:
                        print(f"\n[Igris]: You want me to \"{command}\", correct?")
                        
                    # Listen for confirmation (no timeout)
                    confirm_speech = await stt_manager.listen()
                    if not confirm_speech:
                        if selected_lang == "vi":
                            print("\n[Igris]: Đã hủy lệnh.")
                            print("\nIgris: Đang lắng nghe...")
                        else:
                            print("\n[Igris]: Command canceled.")
                            print("\nIgris: Standby...")
                        continue
                        
                    confirm_lower = confirm_speech.lower().strip()
                    if selected_lang == "vi":
                        yes_keywords = ["có", "co", "xác nhận", "xac nhan", "đúng", "dung", "yes", "y", "đồng ý", "dong y", "chấp nhận", "chap nhan", "ok"]
                        no_keywords = ["không", "khong", "hủy", "huy", "no", "n", "từ chối", "tu choi", "bỏ qua", "bo qua"]
                    else:
                        yes_keywords = ["yes", "y", "confirm", "correct", "sure", "ok", "accept", "approve", "agree", "proceed"]
                        no_keywords = ["no", "n", "cancel", "incorrect", "stop", "reject", "deny", "refuse", "decline"]
                        
                    is_yes = any(kw in confirm_lower for kw in yes_keywords)
                    is_no = any(kw in confirm_lower for kw in no_keywords)
                    
                    if is_yes and not is_no:
                        if selected_lang == "vi":
                            print("\n[Igris]: Đã xác nhận. Bắt đầu thực thi...")
                        else:
                            print("\n[Igris]: Confirmed. Executing...")
                        await execute_command(agent, command)
                    else:
                        if selected_lang == "vi":
                            print("\n[Igris]: Đã hủy lệnh.")
                        else:
                            print("\n[Igris]: Command canceled.")
                            
                    # Back to standby
                    if selected_lang == "vi":
                        print("\nIgris: Đang lắng nghe...")
                    else:
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
