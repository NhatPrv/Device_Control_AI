import asyncio
import sys
import os
import numpy as np
import sounddevice as sd
import queue

# Add root directory to python path to import core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.stt import STTManager

# Set console encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    print("==================================================")
    print("          🎙️  MICROPHONE STT & RMS DEBUG          ")
    print("==================================================")
    print("Initializing Faster-Whisper model on CUDA GPU...")
    
    try:
        stt = STTManager()
        print("STT model loaded successfully!")
    except Exception as e:
        print(f"Fatal Error: Failed to load STT model: {e}")
        return
        
    print("\n--- STANDBY: Speak into your microphone now ---")
    print("    This script prints real-time RMS energy levels.")
    print("    If RMS stays at 0.0000, your microphone is muted or not selected correctly in Windows.")
    print("    Press CTRL+C to exit the test.")
    print("==================================================")
    
    q = queue.Queue()
    loop = asyncio.get_event_loop()
    
    def callback(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        q.put(indata.copy())
        
    chunk_duration = 0.1  # 100ms per chunk
    chunk_size = int(stt.sample_rate * chunk_duration)
    
    stream = sd.InputStream(
        samplerate=stt.sample_rate, 
        channels=1, 
        blocksize=chunk_size, 
        callback=callback
    )
    
    recording = []
    is_speaking = False
    silence_time = 0.0
    
    with stream:
        while True:
            try:
                try:
                    data = q.get_nowait()
                except queue.Empty:
                    await asyncio.sleep(0.02)
                    continue
                
                # Calculate RMS level
                rms = np.sqrt(np.mean(data**2))
                
                # Print real-time RMS level to console on a single line
                sys.stdout.write(f"\rRMS Level: {rms:.4f} | Trigger Threshold: {stt.threshold:.4f} | Speaking: {is_speaking} ")
                sys.stdout.flush()
                
                if rms > stt.threshold:
                    if not is_speaking:
                        print("\n\nIgris: Yes, I am listening...")
                        is_speaking = True
                    recording.append(data)
                    silence_time = 0.0
                else:
                    if is_speaking:
                        recording.append(data)
                        silence_time += chunk_duration
                        if silence_time >= stt.silence_limit:
                            print("\nIgris: Processing speech...")
                            break
                    else:
                        if len(recording) > 10:
                            recording.pop(0)
                        recording.append(data)
            except KeyboardInterrupt:
                return
                
    if recording:
        audio_data = np.concatenate(recording, axis=0).flatten()
        print("Igris: Transcribing speech...")
        text = await loop.run_in_executor(None, stt.transcribe, audio_data)
        if text:
            print(f"\n[HEARD TEXT]: \"{text}\"")
        else:
            print("\n[HEARD TEXT]: (Empty - Whisper could not recognize any words)")
        print("==================================================")

if __name__ == "__main__":
    try:
        while True:
            asyncio.run(main())
            import time
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nTest terminated by user.")
    except Exception as e:
        print(f"\nError: {e}")
