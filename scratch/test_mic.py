import asyncio
import sys
import os

# Add root directory to python path to import core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.stt import STTManager

# Set console encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    print("==================================================")
    print("          🎙️  MICROPHONE STT TEST SCRIPT          ")
    print("==================================================")
    print("Initializing Faster-Whisper model on CUDA GPU...")
    
    try:
        stt = STTManager()
        print("STT model loaded successfully!")
    except Exception as e:
        print(f"Fatal Error: Failed to load STT model: {e}")
        return
        
    print("\n--- STANDBY: Speak into your microphone now ---")
    print("    Press CTRL+C to exit the test.")
    print("==================================================")
    
    while True:
        try:
            text = await stt.listen()
            if text:
                print(f"\n[HEARD TEXT]: \"{text}\"")
                print("--------------------------------------------------")
        except KeyboardInterrupt:
            print("\nTest terminated by user.")
            break
        except Exception as e:
            print(f"\nError in loop: {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest terminated by user.")
