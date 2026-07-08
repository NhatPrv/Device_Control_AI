import asyncio
import sys
import os
import subprocess
import google.antigravity as ag
from core.stt import STTManager
from core.agent import get_agent_config

# Cấu hình encoding UTF-8 cho Windows console để hiển thị tiếng Việt chính xác
sys.stdout.reconfigure(encoding='utf-8')

BANNER = """
===================================================================
             ⚔️   KỴ SĨ HỘ VỆ LAPTOP - IGRIS LOCAL  ⚔️
===================================================================
  - Nhận diện giọng nói đa ngôn ngữ CUDA thực tế qua Faster-Whisper.
  - Sử dụng mô hình cục bộ Qwen 2.5 7B thông qua Ollama.
  - Hỗ trợ các công cụ: Điều khiển âm lượng, độ sáng, pin, phần mềm.
  - Chủ nhân nói "Thoát" hoặc "Tạm biệt" để dừng chương trình.
===================================================================
"""

async def main():
    print(BANNER)
    
    # 1. Khởi chạy proxy cổng 8000 ở background
    print("Igris: Đang thiết lập cổng liên kết API nội bộ...")
    proxy_path = os.path.join(os.path.dirname(__file__), "core", "proxy.py")
    
    try:
        proxy_process = subprocess.Popen(
            [sys.executable, proxy_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        print(f"Lỗi: Không thể khởi chạy cổng proxy nội bộ: {e}")
        return
        
    # Đợi 2 giây cho proxy khởi động hoàn chỉnh
    await asyncio.sleep(2.0)
    
    try:
        # 2. Khởi tạo STT và cấu hình Agent
        stt_manager = STTManager()
        config = get_agent_config()
        
        # 3. Bắt đầu phiên giao tiếp bất đồng bộ với Agent
        print("Igris: Đang triệu hồi kỵ sĩ bảo vệ...")
        async with ag.Agent(config) as agent:
            print("\nIgris: Kính chào Chủ nhân! Thần luôn sẵn sàng chấp hành mệnh lệnh.")
            
            while True:
                # Đọc âm thanh và nhận diện STT
                command = await stt_manager.listen()
                if not command:
                    continue
                
                # Kiểm tra yêu cầu thoát
                cmd_lower = command.lower().strip()
                if any(kw in cmd_lower for kw in ["thoát", "tạm biệt", "exit", "quit"]):
                    print("\n[Igris]: Thần xin phép lui xuống. Chúc Chủ nhân vạn sự như ý!")
                    break
                
                # Gửi lệnh đến Agent để xử lý và gọi tool tương ứng
                try:
                    print("Igris: Thần đang thực hiện...")
                    response = await agent.chat(command)
                    reply_text = await response.text()
                    
                    # Làm sạch phản hồi, loại bỏ các dòng log của SDK nội bộ
                    clean_lines = []
                    for line in reply_text.splitlines():
                        if not any(log_key in line for log_key in ["thora_plugin", "Logged response", "System step"]):
                            clean_lines.append(line)
                    final_reply = "\n".join(clean_lines).strip()
                    
                    print(f"\n[Igris]: {final_reply}")
                except Exception as e:
                    print(f"\n[Igris]: Báo cáo Chủ nhân, thần gặp lỗi khi thực hiện lệnh: {e}")
                    
    finally:
        # Tắt cổng proxy khi thoát chương trình
        print("\nIgris: Đang thu hồi các cổng kết nối...")
        proxy_process.terminate()
        proxy_process.wait()
        print("Igris: Đã hoàn tất ngắt kết nối an toàn.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nIgris: Đã dừng chương trình khẩn cấp theo yêu cầu hệ thống.")
