import asyncio
import queue
import sys
import os
import numpy as np
import sounddevice as sd

# Dynamic CUDA DLL registration for Windows systems running local pip dependencies
if sys.platform == "win32":
    try:
        import nvidia
        nvidia_dir = list(nvidia.__path__)[0]
        dll_paths = [
            os.path.join(nvidia_dir, "cublas", "bin"),
            os.path.join(nvidia_dir, "cudnn", "bin"),
            os.path.join(nvidia_dir, "cuda_nvrtc", "bin"),
            os.path.join(nvidia_dir, "cuda_runtime", "bin"),
        ]
        for path in dll_paths:
            if os.path.exists(path):
                os.add_dll_directory(path)
        # Prepend directories to system PATH for compiled C/C++ extensions
        os.environ["PATH"] = ";".join(dll_paths) + ";" + os.environ["PATH"]
    except Exception:
        pass

from faster_whisper import WhisperModel

class STTManager:
    def __init__(self, model_size="base", device="cuda", compute_type="float16"):
        """
        Initialize Faster-Whisper model running on CUDA GPU.
        """
        print("Igris: Initializing speech recognition model (Faster-Whisper CUDA)...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.sample_rate = 16000
        self.threshold = 0.025  # Energy threshold to start speaking (RMS)
        self.silence_limit = 1.2  # Max silence duration (seconds) before segmenting sentence
        
    def transcribe(self, audio_data: np.ndarray) -> str:
        """
        Transcribe numpy audio data to text.
        Auto-detects language (English, Vietnamese, Japanese, Chinese, etc.).
        """
        try:
            segments, info = self.model.transcribe(
                audio_data, 
                beam_size=5,
                vad_filter=True,  # Use built-in Silero VAD to filter out silence/noise
                vad_parameters=dict(min_silence_duration_ms=500),
                initial_prompt="Hey Igris, open Chrome, check the battery, volume, brightness, mở máy tính, tăng độ sáng, retreat"
            )
            text = "".join(segment.text for segment in segments)
            return text.strip()
        except Exception as e:
            print(f"Igris: Error during STT transcription: {e}", file=sys.stderr)
            return ""

    async def listen(self) -> str:
        """
        Listen to the microphone and automatically segment sentences by energy threshold.
        """
        q = queue.Queue()
        loop = asyncio.get_event_loop()
        
        def callback(indata, frames, time, status):
            if status:
                print(status, file=sys.stderr)
            q.put(indata.copy())
            
        chunk_duration = 0.1  # 100ms per chunk
        chunk_size = int(self.sample_rate * chunk_duration)
        
        stream = sd.InputStream(
            samplerate=self.sample_rate, 
            channels=1, 
            blocksize=chunk_size, 
            callback=callback
        )
        
        recording = []
        is_speaking = False
        silence_time = 0.0
        
        print("\n--- 🎧 IGRIS IS LISTENING... ---")
        
        with stream:
            while True:
                # Read data from microphone queue
                try:
                    data = q.get_nowait()
                except queue.Empty:
                    await asyncio.sleep(0.02)
                    continue
                
                # Calculate RMS of the chunk
                rms = np.sqrt(np.mean(data**2))
                
                if rms > self.threshold:
                    if not is_speaking:
                        print("Igris: Yes, I am listening...")
                        is_speaking = True
                    recording.append(data)
                    silence_time = 0.0
                else:
                    if is_speaking:
                        recording.append(data)
                        silence_time += chunk_duration
                        if silence_time >= self.silence_limit:
                            break
                    else:
                        # Buffer short pre-speech audio to prevent losing starting words
                        if len(recording) > 10:
                            recording.pop(0)
                        recording.append(data)
                        
        if not recording:
            return ""
            
        # Concatenate chunks into a flat numpy array
        audio_data = np.concatenate(recording, axis=0).flatten()
        
        # Run transcription asynchronously in ThreadPool to avoid blocking main event loop
        print("Igris: Transcribing speech...")
        text = await loop.run_in_executor(None, self.transcribe, audio_data)
        
        if text:
            print(f"-> Master said: \"{text}\"")
        return text
