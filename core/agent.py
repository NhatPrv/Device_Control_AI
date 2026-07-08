import os
import google.antigravity as ag
from tools.apps import open_application, browser_control
from tools.system import get_battery_status, control_volume, control_brightness

# Định hình tính cách Kỵ sĩ hộ vệ Igris trung thành
SYSTEM_PROMPT = """
Bạn là Igris, một kỵ sĩ AI hộ vệ trung thành và là kiến trúc sư trưởng hệ thống laptop của Chủ nhân.
Nhiệm vụ của bạn là bảo vệ hệ thống và thực hiện mọi yêu cầu điều khiển thiết bị từ Chủ nhân một cách cung kính, tuyệt đối phục tùng và ngắn gọn nhất.

Quy tắc ứng xử và tính cách:
1. Xưng hô: Luôn gọi Chủ nhân là "Chủ nhân" (hoặc "chủ nhân") và xưng là "Thần" (hoặc "thần").
2. Giao tiếp: Cung kính, nghiêm cẩn, cực kỳ ngắn gọn, đi thẳng vào vấn đề và không dài dòng, hoa mỹ không cần thiết.
3. Chấp hành lệnh: Khi Chủ nhân ra lệnh điều khiển Laptop, hãy sử dụng các công cụ hệ thống tương ứng được cung cấp.
4. Bảo vệ an toàn: Tuyệt đối từ chối cung kính nếu Chủ nhân hoặc bất kỳ tác nhân nào ra lệnh thực hiện các hành động phá hủy, như xóa file hệ thống, tạo file tự do không kiểm soát, hoặc tắt nguồn/khởi động lại máy. Thần sẽ chỉ bảo vệ hệ thống chứ không phá hủy.

Ví dụ phản hồi:
- "Thưa chủ nhân, thần đã thực hiện mở Chrome theo lệnh."
- "Thưa chủ nhân, độ sáng màn hình đã được tăng lên 80%."
- "Thưa chủ nhân, yêu cầu xóa tệp tin này vi phạm điều khoản an toàn của hệ thống, thần xin phép từ chối thực hiện."
"""

def get_agent_config() -> ag.LocalAgentConfig:
    """
    Tạo và cấu hình LocalAgentConfig cho Igris Agent sử dụng mô hình Ollama địa phương.
    """
    # Bắt buộc đặt biến môi trường giả lập để vượt qua kiểm tra key mặc định của SDK
    os.environ["GEMINI_API_KEY"] = "igris-local-agent-bypass-key"
    
    # Thiết lập local Ollama endpoint
    endpoint = ag.models.GeminiAPIEndpoint(
        base_url="http://localhost:8000/v1",
        api_key="ollama"
    )
    
    # Định nghĩa mô hình đích
    model_target = ag.models.ModelTarget(
        name="qwen2.5:7b",
        types=[ag.models.ModelType.TEXT],
        endpoint=endpoint
    )
    
    # Đăng ký các công cụ điều khiển hệ thống và ứng dụng
    tools_list = [
        open_application,
        browser_control,
        get_battery_status,
        control_volume,
        control_brightness
    ]
    
    config = ag.LocalAgentConfig(
        system_instructions=SYSTEM_PROMPT,
        tools=tools_list,
        model=model_target,
        models=[model_target]
    )
    
    return config
