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
  - Gọi kỵ sĩ bằng khẩu lệnh: "Hey Igris" (hoặc "hey igris").
  - Chủ nhân nói "Retreat" để dừng chương trình.
===================================================================
"""

async def execute_command(agent, command: str):
    """
    Gửi câu lệnh tới Agent để xử lý gọi tool và hiển thị phản hồi từ Igris.
    """
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
            print("\nIgris: Kính chào Chủ nhân! Thần luôn sẵn sàng trực chờ bảo vệ hệ thống.")
            
            waiting_for_wake = True
            
            while True:
                if waiting_for_wake:
                    print("\n--- 🛡️ IGRIS ĐANG TRỰC CHỜ KHẨU LỆNH (\"Hey Igris\")... ---")
                    speech = await stt_manager.listen()
                    if not speech:
                        continue
                    
                    speech_lower = speech.lower().strip()
                    
                    # Kết thúc nếu nghe thấy lệnh "Retreat"
                    if "retreat" in speech_lower:
                        print("\n[Igris]: Thần xin phép lui xuống (Retreat). Chúc Chủ nhân vạn sự như ý!")
                        break
                        
                    # Kích hoạt khi nghe thấy "Hey Igris"
                    if "hey igris" in speech_lower:
                        # Kiểm tra xem có lệnh đi kèm luôn trong câu không (Ví dụ: "Hey Igris, mở calculator")
                        idx = speech_lower.find("hey igris")
                        command_part = speech[idx + len("hey igris"):].strip(",. ")
                        
                        if command_part:
                            if "retreat" in command_part.lower():
                                print("\n[Igris]: Thần xin phép lui xuống (Retreat). Chúc Chủ nhân vạn sự như ý!")
                                break
                            print(f"\n[Igris]: Dạ, thưa Chủ nhân! Thần ghi nhận lệnh trực tiếp: \"{command_part}\"")
                            await execute_command(agent, command_part)
                        else:
                            print("\n[Igris]: Dạ, thưa Chủ nhân! Thần đang lắng nghe mệnh lệnh của người.")
                            waiting_for_wake = False
                    else:
                        continue
                else:
                    print("\n--- 🎤 ĐANG GHI NHẬN LỆNH CỦA CHỦ NHÂN... ---")
                    command = await stt_manager.listen()
                    if not command:
                        continue
                        
                    cmd_lower = command.lower().strip()
                    if "retreat" in cmd_lower:
                        print("\n[Igris]: Thần xin phép lui xuống (Retreat). Chúc Chủ nhân vạn sự như ý!")
                        break
                        
                    await execute_command(agent, command)
                    # Quay lại trạng thái chờ khẩu lệnh sau khi xử lý xong câu lệnh
                    waiting_for_wake = True
                    
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
