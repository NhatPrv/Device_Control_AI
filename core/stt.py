import asyncio
import queue
import sys
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

class STTManager:
    def __init__(self, model_size="base", device="cuda", compute_type="float16"):
        """
        Khởi tạo mô hình Faster-Whisper chạy trên GPU CUDA.
        """
        print("Igris: Đang khởi tạo mô hình nhận diện giọng nói (Faster-Whisper CUDA)...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.sample_rate = 16000
        self.threshold = 0.025  # Ngưỡng năng lượng âm thanh bắt đầu nói (RMS)
        self.silence_limit = 1.2  # Thời gian im lặng (giây) tối đa trước khi ngắt câu
        
    def transcribe(self, audio_data: np.ndarray) -> str:
        """
        Chuyển đổi mảng numpy chứa dữ liệu âm thanh thành văn bản.
        Tự động nhận diện ngôn ngữ (Việt, Anh, Nhật, Trung...).
        """
        try:
            segments, info = self.model.transcribe(
                audio_data, 
                beam_size=5,
                vad_filter=True,  # Sử dụng bộ lọc Silero VAD tích hợp để lọc nhiễu im lặng
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            text = "".join(segment.text for segment in segments)
            return text.strip()
        except Exception as e:
            print(f"Igris: Lỗi trong quá trình nhận diện STT: {e}", file=sys.stderr)
            return ""

    async def listen(self) -> str:
        """
        Lắng nghe microphone thực tế và tự động tách câu theo ngưỡng âm lượng.
        """
        q = queue.Queue()
        loop = asyncio.get_event_loop()
        
        def callback(indata, frames, time, status):
            if status:
                print(status, file=sys.stderr)
            q.put(indata.copy())
            
        chunk_duration = 0.1  # Mỗi chunk 100ms
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
        
        print("\n--- 🎧 IGRIS ĐANG LẮNG NGHE CHỦ NHÂN... ---")
        
        with stream:
            while True:
                # Đọc dữ liệu từ hàng đợi micrô
                try:
                    data = q.get_nowait()
                except queue.Empty:
                    await asyncio.sleep(0.02)
                    continue
                
                # Tính RMS của chunk
                rms = np.sqrt(np.mean(data**2))
                
                if rms > self.threshold:
                    if not is_speaking:
                        print("Igris: Dạ, thần đang nghe...")
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
                        # Lưu trữ đệm âm thanh ngắn trước khi nói để tránh mất chữ đầu
                        if len(recording) > 10:
                            recording.pop(0)
                        recording.append(data)
                        
        if not recording:
            return ""
            
        # Ghép các khối âm thanh thành mảng numpy phẳng
        audio_data = np.concatenate(recording, axis=0).flatten()
        
        # Chạy nhận dạng bất đồng bộ trong ThreadPool để không bị treo event loop chính
        print("Igris: Đang dịch giọng nói...")
        text = await loop.run_in_executor(None, self.transcribe, audio_data)
        
        if text:
            print(f"-> Chủ nhân nói: \"{text}\"")
        return text
