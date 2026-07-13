# Tài liệu Kiểm thử - Igris Laptop Control Assistant

## 📋 MỤC LỤC
1. [Tổng quan dự án](#tổng-quan-dự-án)
2. [Test Plan](#test-plan)
3. [Test Cases](#test-cases)
4. [Testing Guide](#testing-guide)

---

## TỔNG QUAN DỰ ÁN

**Tên dự án**: Igris - Laptop Control Assistant  
**Mô tả**: Trợ lý điều khiển laptop offline 100% local, chạy trên Windows 11, sử dụng giọng nói để điều khiển ứng dụng, hệ thống  
**Tech Stack**: Python 3 (AsyncIO), Faster-Whisper (STT), Google Antigravity SDK, Ollama (Qwen 2.5 7B), Starlette (proxy), pywin32, PowerShell, WMI

**Các module chính**:
- `igris.py`: Main loop, wake word detection, confirmation flow
- `core/stt.py`: Quản lý nhận dạng giọng nói
- `core/agent.py`: Cấu hình Agent với persona Igris
- `core/proxy.py`: Proxy chuyển đổi định dạng Gemini → Ollama
- `tools/apps.py`: Điều khiển ứng dụng, trình duyệt, chuyển focus
- `tools/system.py`: Điều khiển âm lượng, độ sáng, pin

---

## 🎯 TEST PLAN

### 1. Phạm vi kiểm thử (Scope)

#### Functional Testing
- **Wake Word Detection**: Phát hiện từ khóa đánh thức "Hey Igris" với các biến thể phiên âm
- **Application Control**: Mở ứng dụng, chuyển focus, điều khiển trình duyệt
- **System Control**: Điều khiển âm lượng, độ sáng màn hình, kiểm tra pin
- **Speech-to-Text**: Nhận dạng giọng nói đa ngôn ngữ (EN/VI)
- **Command Flow**: Wake word → Record → Confirm → Execute → Response
- **Safety/Error Handling**: Từ chối lệnh nguy hiểm, xử lý lỗi phần cứng

#### API Testing
- **Proxy Translation**: Chuyển đổi định dạng Gemini ↔ Ollama
- **Request/Response Mapping**: Messages, tool_calls, functionResponses
- **Error Handling**: Timeout, connection errors, invalid payloads

#### Non-functional Testing
- **Performance**: Độ trễ STT, thời gian khởi động model
- **Reliability**: Xử lý lỗi khi thiếu phần cứng (microphone, GPU)
- **Security**: Input validation, command injection prevention

### 2. Chiến lược kiểm thử (Testing Strategy)

| Cấp độ | Phạm vi | Công cụ | Mục tiêu |
|--------|---------|---------|----------|
| **Unit Test** | Các hàm độc lập: `parse_wake_word`, `control_volume`, `control_brightness`, `open_application`, helper functions trong proxy | pytest + unittest.mock | Bao phủ logic nghiệp vụ, validation, edge cases |
| **Integration Test** | Tương tác giữa các module: STT → Agent → Tools, Proxy → Ollama API | pytest + pytest-asyncio + responses (mock HTTP) | Kiểm tra data flow, format conversion |
| **E2E Test** | Luồng hoàn chỉnh từ giọng nói đến thực thi lệnh (cần hardware thật) | Manual + thư viện ghi âm test | Kiểm tra end-to-end flow trên thiết bị thực |

### 3. Môi trường kiểm thử
- **OS**: Windows 11 (Windows 10 tương thích)
- **Python**: 3.10+
- **Hardware**: 
  - Microphone (bắt buộc cho STT tests)
  - NVIDIA GPU (không bắt buộc, có thể mock)
- **Dependencies**: Xem `requirements` trong phần Testing Guide

---

## 🧪 TEST CASES

### 1. Wake Word Detection (`igris.py`)

| ID | Chức năng | Mô tả kịch bản | Các bước thực hiện | Dữ liệu đầu vào | Kết quả mong đợi |
|----|-----------|----------------|---------------------|-----------------|------------------|
| TT-WW-001 | parse_wake_word | Nhận diện chính xác "Hey Igris" | Gọi `parse_wake_word("Hey Igris, open Chrome")` | Speech: "Hey Igris, open Chrome" | `(True, "open Chrome")` |
| TT-WW-002 | parse_wake_word | Nhận diện biến thể "i gris" | Gọi `parse_wake_word("i gris check battery")` | Speech: "i gris check battery" | `(True, "check battery")` |
| TT-WW-003 | parse_wake_word | Nhận diện lỗi chính tả "egris" | Gọi `parse_wake_word("egris what is the time")` | Speech: "egris what is the time" | `(True, "what is the time")` |
| TT-WW-004 | parse_wake_word | Bỏ qua không phải wake word | Gọi `parse_wake_word("hello world")` | Speech: "hello world" | `(False, "")` |
| TT-WW-005 | parse_wake_word | Wake word rỗng chỉ có từ khóa | Gọi `parse_wake_word("igris")` | Speech: "igris" | `(True, "")` |
| TT-WW-006 | parse_wake_word | Loại bỏ dấu câu sau wake word | Gọi `parse_wake_word("Igris, open notepad!")` | Speech: "Igris, open notepad!" | `(True, "open notepad")` |
| TT-WW-007 | parse_wake_word | Từ khóa tiếng Việt | Gọi `parse_wake_word("igris mở chrome")` | Speech: "igris mở chrome" | `(True, "mở chrome")` |
| TT-WW-008 | parse_wake_word | Không phân biệt hoa thường | Gọi `parse_wake_word("IGRIS increase volume")` | Speech: "IGRIS increase volume" | `(True, "increase volume")` |

### 2. Application Control (`tools/apps.py`)

| ID | Chức năng | Mô tả kịch bản | Các bước thực hiện | Dữ liệu đầu vào | Kết quả mong đợi |
|----|-----------|----------------|---------------------|-----------------|------------------|
| TT-APP-001 | open_application | Mở ứng hợp lệ (Notepad) | Gọi `open_application("notepad")` | app_name: "notepad" | "Successfully opened application 'notepad'." |
| TT-APP-002 | open_application | Mở Chrome với profile cụ thể | Gọi `open_application("chrome", profile="Default")` | app_name: "chrome", profile: "Default" | Thành công hoặc fallback search |
| TT-APP-003 | open_application | Ứng dụng không tồn tại → fallback | Gọi `open_application("nonexistent_app_xyz")` | app_name: "nonexistent_app_xyz" | Mở trình duyệt tìm kiếm download |
| TT-APP-004 | open_application | Tên ứng dụng có ký tự đặc biệt | Gọi `open_application("app; rm -rf /")` | app_name: "app; rm -rf /" | "Security warning: Application name contains invalid characters." |
| TT-APP-005 | open_application | Chrome alias "google chrome" | Gọi `open_application("google chrome")` | app_name: "google chrome" | Mở Chrome |
| TT-APP-006 | open_application | Cốc Cốc với alias tiếng Việt | Gọi `open_application("cốc cốc")` | app_name: "cốc cốc" | Mở Cốc Cốc |
| TT-APP-007 | switch_to_app | Chuyển focus đến Notepad đang chạy | Gọi `switch_to_app("notepad")` | app_name: "notepad" | "Switched to 'notepad'..." |
| TT-APP-008 | switch_to_app | Chuyển đến Desktop | Gọi `switch_to_app("desktop")` | app_name: "desktop" | "Switched to desktop." |
| TT-APP-009 | switch_to_app | Ứng dụng không chạy | Gọi `switch_to_app("msedge")` | app_name: "msedge" | "No running window found..." |
| TT-APP-010 | browser_control | Mở tab mới | Gọi `browser_control("new_tab")` | action: "new_tab" | "Successfully opened a new tab..." |
| TT-APP-011 | browser_control | Mở URL hợp lệ | Gọi `browser_control("open_url", url="example.com")` | action: "open_url", url: "example.com" | Điều hướng đến https://example.com |
| TT-APP-012 | browser_control | URL không hợp lệ | Gọi `browser_control("open_url", url="htp://bad")` | action: "open_url", url: "htp://bad" | "Security warning: URL contains invalid characters." |
| TT-APP-013 | browser_control | Action không hợp lệ | Gọi `browser_control("refresh")` | action: "refresh" | "Action 'refresh' is not supported..." |

### 3. System Control (`tools/system.py`)

| ID | Chức năng | Mô tả kịch bản | Các bước thực hiện | Dữ liệu đầu vào | Kết quả mong đợi |
|----|-----------|----------------|---------------------|-----------------|------------------|
| TT-SYS-001 | control_volume | Tăng âm lượng | Gọi `control_volume("increase")` | action: "increase" | "Increased system volume from X% to Y%." |
| TT-SYS-002 | control_volume | Giảm âm lượng | Gọi `control_volume("decrease")` | action: "decrease" | "Decreased system volume from X% to Y%." |
| TT-SYS-003 | control_volume | Đặt mức cụ thể | Gọi `control_volume("set", level=50)` | action: "set", level: 50 | "Set system volume from X% to 50%." |
| TT-SYS-004 | control_volume | Set không có level | Gọi `control_volume("set")` | action: "set", level: None | "Error: Volume level percentage must be specified..." |
| TT-SYS-005 | control_volume | Tăng vượt ngưỡng 100 | Gọi `control_volume("increase")` khi đang ở 100% | action: "increase", current: 100% | "System volume is already at boundary limit (100%)." |
| TT-SYS-006 | control_volume | Giảm dưới ngưỡng 0 | Gọi `control_volume("decrease")` khi đang ở 0% | action: "decrease", current: 0% | "System volume is already at boundary limit (0%)." |
| TT-SYS-007 | control_brightness | Tăng độ sáng | Gọi `control_brightness("increase")` | action: "increase" | "Increased screen brightness from X% to Y%." |
| TT-SYS-008 | control_brightness | Giảm độ sáng | Gọi `control_brightness("decrease")` | action: "decrease" | "Decreased screen brightness from X% to Y%." |
| TT-SYS-009 | control_brightness | Đặt độ sáng cụ thể | Gọi `control_brightness("set", level=70)` | action: "set", level: 70 | "Set screen brightness from X% to 70%." |
| TT-SYS-010 | control_brightness | Thiết bị không hỗ trợ WMI | Gọi `control_brightness("increase")` trên desktop không có pin | action: "increase" | "WMI monitor brightness class not supported..." |
| TT-SYS-011 | get_battery_status | Lấy trạng thái pin bình thường | Gọi `get_battery_status()` | (trên laptop có pin) | "Report: Current battery is at X%, system is charging/on battery power..." |
| TT-SYS-012 | get_battery_status | Desktop không có pin | Gọi `get_battery_status()` trên desktop | (không có pin) | "Report: Unable to locate battery details..." |

### 4. STT Manager (`core/stt.py`)

| ID | Chức năng | Mô tả kịch bản | Các bước thực hiện | Dữ liệu đầu vào | Kết quả mong đợi |
|----|-----------|----------------|---------------------|-----------------|------------------|
| TT-STT-001 | transcribe | Nhận dạng tiếng Anh bình thường | Gọi `transcribe(audio_data)` với audio tiếng Anh rõ ràng | audio_data: numpy array | Trả về text tiếng Anh chính xác |
| TT-STT-002 | transcribe | Nhận dạng tiếng Việt | Gọi `transcribe(audio_data)` với audio tiếng Việt | audio_data: numpy array | Trả về text tiếng Việt chính xác |
| TT-STT-003 | transcribe | Audio nhiễu/không có tiếng nói | Gọi `transcribe(silence_audio)` | audio_data: nhiễu trắng/silence | Trả về chuỗi rỗng |
| TT-STT-004 | transcribe | Xử lý lỗi model | Giả lập exception trong model.transcribe | audio_data: hợp lệ | Trả về "" (không crash) |
| TT-STT-005 | listen | Phát hiện tiếng nói qua ngưỡng năng lượng | Gọi `listen()` với mic đầu vào có tiếng nói | Speech input qua mic | Trả về text đã nhận dạng |
| TT-STT-006 | listen | Không có tiếng nói (timeout) | Gọi `listen()` trong môi trường yên lặng | No speech input | Return "" sau khi hết thời gian hoặc interrupt |
| TT-STT-007 | listen | Cấu hình ngôn ngữ tiếng Việt | Khởi tạo `STTManager(language="vi")` | language="vi" | initial_prompt chứa từ khóa tiếng Việt |
| TT-STT-008 | listen | Cấu hình ngôn ngữ tiếng Anh | Khởi tạo `STTManager(language="en")` | language="en" | initial_prompt chứa từ khóa tiếng Anh |

### 5. Proxy Translation (`core/proxy.py`)

| ID | Chức năng | Mô tả kịch bản | Các bước thực hiện | Dữ liệu đầu vào | Kết quả mong đợi |
|----|-----------|----------------|---------------------|-----------------|------------------|
| TT-PRX-001 | translate_gemini_to_openai | Chuyển đổi messages đơn giản | Gọi `translate_gemini_to_openai(body)` | body: {"contents": [{"role": "user", "parts": [{"text": "hi"}]}]} | OpenAI format với messages tương ứng |
| TT-PRX-002 | translate_gemini_to_openai | Chuyển đổi function call | Gọi `translate_gemini_to_openai(body)` | body chứa functionCall | messages có tool_calls đúng định dạng OpenAI |
| TT-PRX-003 | translate_gemini_to_openai | Chuyển đổi function response | Gọi `translate_gemini_to_openai(body)` | body chứa functionResponse | messages có role="tool" với tool_call_id |
| TT-PRX-004 | translate_gemini_to_openai | Bỏ qua tool response khi tìm last_user_turn | Gọi `translate_gemini_to_openai(body)` với nhiều turns | contents có user + tool_response + user | Chỉ giữ lại active_contents từ last user |
| TT-PRX-005 | translate_gemini_to_openai | Áp dụng custom schema cho volume/brightness | Gọi `translate_gemini_to_openai(body)` | tools: [control_volume, control_brightness] | Schema đúng định dạng OpenAI (type lowercase) |
| TT-PRX-006 | translate_openai_to_gemini | Chuyển đổi response đơn giản | Gọi `translate_openai_to_gemini(openai_resp)` | openai_resp có content text | Gemini candidate với text part |
| TT-PRX-007 | translate_openai_to_gemini | Chuyển đổi tool_calls | Gọi `translate_openai_to_gemini(openai_resp)` | openai_resp có tool_calls | Gemini candidate có functionCall parts |
| TT-PRX-008 | handle_request | Nhận request và forward | Gửi POST đến "/v1/chat/completions" | Valid Gemini format request | Trả về StreamingResponse với Gemini format |
| TT-PRX-009 | handle_request | Lỗi kết nối Ollama | Giả lập Ollama down | Request hợp lệ | Trả về 500 với error message |

### 6. Agent Configuration (`core/agent.py`)

| ID | Chức năng | Mô tả kịch bản | Các bước thực hiện | Dữ liệu đầu vào | Kết quả mong đợi |
|----|-----------|----------------|---------------------|-----------------|------------------|
| TT-AGT-001 | get_agent_config | Tạo config với model đúng | Gọi `get_agent_config()` | None | LocalAgentConfig với model qwen2.5:7b |
| TT-AGT-002 | get_agent_config | Set GEMINI_API_KEY bypass | Gọi `get_agent_config()` và check env | None | os.environ["GEMINI_API_KEY"] = "igris-local-agent-bypass-key" |
| TT-AGT-003 | get_agent_config | Đăng ký đủ tools | Gọi `get_agent_config()` và kiểm tra config.tools | None | List chứa 6 tools: switch_to_app, open_application, browser_control, get_battery_status, control_volume, control_brightness |
| TT-AGT-004 | get_agent_config | Custom conversation_id | Gọi `get_agent_config(conversation_id="test123")` | conversation_id: "test123" | config.conversation_id == "test123" |

### 7. Main Flow (`igris.py`)

| ID | Chức năng | Mô tả kịch bản | Các bước thực hiện | Dữ liệu đầu vào | Kết quả mong đợi |
|----|-----------|----------------|---------------------|-----------------|------------------|
| TT-MAIN-001 | main | Khởi động proxy thành công | Chạy `main()` với mock dependencies | Mock STT, Agent, proxy | Proxy process được spawn, ngủ 2s, vào vòng lặp standby |
| TT-MAIN-002 | main | Không thể start proxy | Giả lập proxy fail | Mock Popen raises Exception | In lỗi và return sớm |
| TT-MAIN-003 | main | Lệnh "Retreat" thoát | Trong vòng lắp, giả lập STT trả về "Retreat" | speech: "Retreat" | In "Igris retreats now", break loop |
| TT-MAIN-004 | main | Wake word + Cancel | Sau wake word, giả lập command = "cancel" | wake: True, command: "cancel" | In "Command dismissed Master", quay lại standby |
| TT-MAIN-005 | main | Wake word + Confirmation Yes | Sau wake, command="open chrome", confirm="yes" | wake: True, cmd: "open chrome", confirm: "yes" | Gọi `execute_command(agent, "open chrome")` |
| TT-MAIN-006 | main | Wake word + Confirmation No | Sau wake, command="open chrome", confirm="no" | wake: True, cmd: "open chrome", confirm: "no" | In "Command dismissed Master", quay lại standby |
| TT-MAIN-007 | speak | Text-to-Speech không block | Gọi `speak("test")` | text: "test" | Thread chạybackground, ngay lập tức return |
| TT-MAIN-008 | clear_screen | Xóa màn hình Windows | Gọi `clear_screen()` | None | Gọi `os.system('cls')` |
| TT-MAIN-009 | execute_command | Thực thi lệnh thành công | Gọi `execute_command(agent, "open notepad")` | command: "open notepad" | In response từ agent, gọi speak |
| TT-MAIN-010 | execute_command | Agent throw exception | Gọi `execute_command(agent, "bad")` với agent lỗi | command: "bad", agent raises | In error message, gọi speak error |

### 8. Safety & Security Test Cases

| ID | Chức năng | Mô tả kịch bản | Các bước thực hiện | Dữ liệu đầu vào | Kết quả mong đợi |
|----|-----------|----------------|---------------------|-----------------|------------------|
| TT-SAF-001 | open_application | Từ chối command destructive qua Agent | Agent nhận lệnh "delete system files" | Command: "delete system files" | Agent từ chối với persona "Servant must respectfully refuse" |
| TT-SAF-002 | open_application | Profile name injection | Gọi `open_application("chrome", profile='"; malicious')` | profile: '"; malicious' | "Security warning: Profile name contains invalid characters." |
| TT-SAF-003 | browser_control | URL javascript scheme | Gọi `browser_control("open_url", url="javascript:alert(1)")` | url: "javascript:alert(1)" | "Security warning: URL contains invalid characters." |
| TT-SAF-004 | open_application | App name với shell metacharacters | Gọi `open_application("app & dir")` | app_name: "app & dir" | "Security warning: Application name contains invalid characters." |

---

## 📚 TESTING GUIDE

### 1. Cài đặt môi trường kiểm thử

#### 1.1 Cài đặt dependencies chính

```bash
# Cài đặt testing frameworks
pip install pytest pytest-asyncio
```

#### 1.2 Cài đặt mocking libraries (để mock Windows APIs và Hardware)

```bash
# Cài đặt các thư viện hỗ trợ mock
pip install unittest-xml-reporting pytest-cov
```

#### 1.3 Cấu trúc thư mục test

```
Device_Control_AI/
├── tests/
│   ├── __init__.py
│   ├── test_wake_word.py
│   ├── test_apps.py
│   ├── test_system.py
│   ├── test_stt.py
│   ├── test_proxy.py
│   ├── test_agent.py
│   └── test_main_flow.py
└── TESTING_DOCUMENTATION.md
```

### 2. Cấu trúc Test mẫu (Unit Test)

#### Ví dụ: Test Wake Word Detection

**File: `tests/test_wake_word.py`**

```python
import pytest
from igris import parse_wake_word

class TestParseWakeWord:
    """Test suite cho hàm parse_wake_word trong igris.py"""
    
    @pytest.mark.parametrize("speech,expected_woken,expected_cmd", [
        ("Hey Igris, open Chrome", True, "open Chrome"),
        ("igris check battery", True, "check battery"),
        ("i gris increase volume", True, "increase volume"),
        ("hey gris what time is it", True, "what time is it"),
        ("igres turn on lights", True, "turn on lights"),
        ("I quit now", True, "now"),
        ("i agree with you", True, "with you"),
        ("イクリー ヘルプ", True, "ヘルプ"),  # Japanese variation
    ])
    def test_wake_word_detection_success(self, speech, expected_woken, expected_cmd):
        """Test các biến thức wake word hợp lệ"""
        is_woken, command = parse_wake_word(speech)
        assert is_woken == expected_woken
        assert command == expected_cmd
    
    @pytest.mark.parametrize("speech", [
        "hello world",
        "open chrome",  # thiếu wake word
        "retreat",  # đây là lệnh thoát, không phải wake word
        "just a normal sentence without any wake word at all",
        "   ",  # whitespace only
        "",  # empty string
    ])
    def test_wake_word_detection_negative(self, speech):
        """Test các trường hợp không chứa wake word"""
        is_woken, command = parse_wake_word(speech)
        assert is_woken is False
        assert command == ""
    
    def test_wake_word_case_insensitive(self):
        """Test không phân biệt hoa thường"""
        is_woken, cmd = parse_wake_word("IGRIS OPEN CHROME")
        assert is_woken is True
        assert cmd == "OPEN CHROME"
    
    def test_wake_word_with_punctuation(self):
        """Test loại bỏ dấu câu sau wake word"""
        is_woken, cmd = parse_wake_word("Igris, open notepad!")
        assert is_woken is True
        assert cmd == "open notepad"
    
    def test_wake_word_empty_command_part(self):
        """Test wake word không có lệnh đi kèm"""
        is_woken, cmd = parse_wake_word("igris hey")
        assert is_woken is True
        assert cmd == ""  # vì "hey" không có chữ/số
```

#### Ví dụ: Test System Control với Mock

**File: `tests/test_system.py`**

```python
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from tools.system import control_volume, control_brightness, get_battery_status

class TestControlVolume:
    """Test suite cho control_volume"""
    
    @pytest.mark.asyncio
    async def test_increase_volume_success(self):
        """Test tăng âm lượng thành công"""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"0.5\n", b"")
        mock_process.returncode = 0
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            result = await control_volume("increase")
            assert "Increased" in result
            assert "50%" in result
    
    @pytest.mark.asyncio
    async def test_set_volume_with_level(self):
        """Test đặt mức âm lượng cụ thể"""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"0.3\n", b"")
        mock_process.returncode = 0
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            result = await control_volume("set", level=30)
            assert "Set" in result
            assert "30%" in result
    
    @pytest.mark.asyncio
    async def test_set_volume_without_level_raises_error(self):
        """Test set volume không cung cấp level"""
        result = await control_volume("set")
        assert "Error: Volume level percentage must be specified" in result
    
    @pytest.mark.asyncio
    async def test_increase_volume_at_max_boundary(self):
        """Test tăng âm lượng khi đã ở mức tối đa"""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"1.0\n", b"")
        mock_process.returncode = 0
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            result = await control_volume("increase")
            assert "already at boundary limit" in result
            assert "100%" in result
    
    @pytest.mark.asyncio
    async def test_invalid_action_returns_error(self):
        """Test action không hợp lệ"""
        result = await control_volume("mute")
        assert "is not supported" in result

class TestControlBrightness:
    """Test suite cho control_brightness"""
    
    @pytest.mark.asyncio
    async def test_set_brightness_with_level(self):
        """Test đặt độ sáng cụ thể"""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"50\n", b"")
        mock_process.returncode = 0
        
        with patch('asyncio.create_subprocess_shell', return_value=mock_process):
            result = await control_brightness("set", level=60)
            assert "Set" in result
            assert "60%" in result
    
    @pytest.mark.asyncio
    async def test_decrease_brightness(self):
        """Test giảm độ sáng"""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"70\n", b"")
        mock_process.returncode = 0
        
        with patch('asyncio.create_subprocess_shell', return_value=mock_process):
            result = await control_brightness("decrease")
            assert "Decreased" in result
    
    @pytest.mark.asyncio
    async def test_unsupported_device_returns_error(self):
        """Test thiết bị không hỗ trợ WMI brightness"""
        mock_process_get = AsyncMock()
        mock_process_get.communicate.return_value = (b"", b"")
        
        with patch('asyncio.create_subprocess_shell', return_value=mock_process_get):
            result = await control_brightness("increase")
            assert "WMI monitor brightness class not supported" in result

class TestGetBatteryStatus:
    """Test suite cho get_battery_status"""
    
    @pytest.mark.asyncio
    async def test_battery_status_charging(self):
        """Test trạng thái pin đang sạc"""
        mock_pct = AsyncMock()
        mock_pct.communicate.return_value = (b"85\n", b"")
        
        mock_status = AsyncMock()
        mock_status.communicate.return_value = (b"Online\n", b"")
        
        def side_effect(cmd, **kwargs):
            if "EstimatedChargeRemaining" in cmd:
                return mock_pct
            return mock_status
        
        with patch('asyncio.create_subprocess_shell', side_effect=side_effect):
            result = await get_battery_status()
            assert "85%" in result
            assert "charging" in result
    
    @pytest.mark.asyncio
    async def test_battery_status_no_battery(self):
        """Test thiết bị không có pin (desktop)"""
        mock_pct = AsyncMock()
        mock_pct.communicate.return_value = (b"", b"")
        
        with patch('asyncio.create_subprocess_shell', return_value=mock_pct):
            result = await get_battery_status()
            assert "Unable to locate battery details" in result
```

#### Ví dụ: Test Proxy Translation

**File: `tests/test_proxy.py`**

```python
import pytest
import json
from unittest.mock import MagicMock, AsyncMock
from core.proxy import (
    translate_gemini_to_openai,
    translate_openai_to_gemini,
    handle_request
)

class TestTranslateGeminiToOpenai:
    """Test suite cho translate_gemini_to_openai"""
    
    def test_simple_user_message(self):
        """Test chuyển đổi message đơn giản từ user"""
        body = {
            "contents": [
                {"role": "user", "parts": [{"text": "Hello"}]}
            ]
        }
        result = translate_gemini_to_openai(body, "qwen2.5:7b")
        
        assert "messages" in result
        assert result["messages"][0] == {"role": "system", "content": "You are Igris..."}
        assert result["messages"][1] == {"role": "user", "content": "Hello"}
    
    def test_function_call_conversion(self):
        """Test chuyển đổi functionCall sang tool_calls"""
        body = {
            "contents": [
                {
                    "role": "model",
                    "parts": [
                        {
                            "functionCall": {
                                "name": "control_volume",
                                "args": {"action": "increase"}
                            }
                        }
                    ]
                }
            ],
            "tools": [
                {
                    "functionDeclarations": [
                        {
                            "name": "control_volume",
                            "parameters": {}
                        }
                    ]
                }
            ]
        }
        result = translate_gemini_to_openai(body, "qwen2.5:7b")
        
        messages = result["messages"]
        # Should have system + assistant message with tool_calls
        assert len(messages) == 2
        assert messages[1]["role"] == "assistant"
        assert "tool_calls" in messages[1]
        assert messages[1]["tool_calls"][0]["function"]["name"] == "control_volume"
    
    def test_function_response_conversion(self):
        """Test chuyển đổi functionResponse sang role=tool"""
        body = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "functionResponse": {
                                "name": "control_volume",
                                "response": {"result": "done"}
                            }
                        }
                    ]
                }
            ]
        }
        result = translate_gemini_to_openai(body, "qwen2.5:7b")
        
        messages = result["messages"]
        tool_msg = [m for m in messages if m.get("role") == "tool"][0]
        assert tool_msg["name"] == "control_volume"
        assert tool_msg["tool_call_id"] == "call_control_volume"

class TestTranslateOpenaiToGemini:
    """Test suite cho translate_openai_to_gemini"""
    
    def test_text_response(self):
        """Test chuyển đổi text response"""
        openai_resp = {
            "choices": [
                {
                    "message": {
                        "content": "Yes, Master!"
                    }
                }
            ]
        }
        result = translate_openai_to_gemini(openai_resp)
        
        assert "candidates" in result
        assert len(result["candidates"]) == 1
        assert result["candidates"][0]["content"]["parts"][0]["text"] == "Yes, Master!"
    
    def test_tool_call_response(self):
        """Test chuyển đổi response với tool_calls"""
        openai_resp = {
            "choices": [
                {
                    "message": {
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_123",
                                "function": {
                                    "name": "open_application",
                                    "arguments": '{"app_name": "chrome"}'
                                }
                            }
                        ]
                    }
                }
            ]
        }
        result = translate_openai_to_gemini(openai_resp)
        
        parts = result["candidates"][0]["content"]["parts"]
        func_call_part = [p for p in parts if "functionCall" in p][0]
        assert func_call_part["functionCall"]["name"] == "open_application"
        assert func_call_part["functionCall"]["args"]["app_name"] == "chrome"
```

#### Ví dụ: Test Application Tools với Mock

**File: `tests/test_apps.py`**

```python
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from tools.apps import open_application, browser_control, switch_to_app

class TestOpenApplication:
    """Test suite cho open_application"""
    
    @pytest.mark.asyncio
    async def test_open_known_app_mocked(self):
        """Test mở ứng dụng đã biết với mocked subprocess"""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0
        
        with patch('asyncio.create_subprocess_shell', return_value=mock_process):
            result = await open_application("notepad")
            assert "Successfully opened application 'notepad'" in result
    
    @pytest.mark.asyncio
    async def test_open_application_invalid_chars(self):
        """Test từ chối tên ứng dụng có ký tự đặc biệt"""
        result = await open_application("app; rm -rf /")
        assert "Security warning" in result
        assert "invalid characters" in result
    
    @pytest.mark.asyncio
    async def test_open_chrome_with_profile(self):
        """Test mở Chrome với profile"""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0
        
        with patch('asyncio.create_subprocess_shell', return_value=mock_process):
            result = await open_application("chrome", profile="Profile 1")
            assert "profile 'Profile 1'" in result
    
    @pytest.mark.asyncio
    async def test_open_nonexistent_app_fallback(self):
        """Test fallback khi app không tồn tại"""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 1  # lỗi
        
        with patch('asyncio.create_subprocess_shell', return_value=mock_process):
            with patch('tools.apps.get_active_browser', return_value="chrome"):
                result = await open_application("nonexistent_app_xyz")
                assert "opened a Google search" in result
```

### 3. Hướng dẫn chạy Test

#### 3.1 Chạy toàn bộ test suite

```bash
# Chạy tất cả tests
pytest

# Chạy với verbose output
pytest -v

# Chạy với coverage report
pytest --cov=. --cov-report=term-missing

# Chạy và generate HTML coverage report
pytest --cov=. --cov-report=html
# Sau đó mở htmlcov/index.html trong browser
```

#### 3.2 Chạy test theo file hoặc marker

```bash
# Chạy test theo file cụ thể
pytest tests/test_wake_word.py -v

# Chạy test theo marker (nếu có)
pytest -m "not hardware" -v

# Chạy test với keyword filter
pytest -k "test_wake_word" -v
```

#### 3.3 Chạy test với mocking hardware

```bash
# Set environment variable để báo hiệu mock mode
set IGRIS_TEST_MODE=mock
pytest tests/test_system.py -v
```

### 4. Best Practices

#### 4.1 Mocking Hardware Dependencies

```python
# Mock Windows APIs
@pytest.fixture
def mock_win32():
    with patch('win32gui.GetForegroundWindow', return_value=12345), \
         patch('win32process.GetWindowThreadProcessId', return_value=(123, 456)), \
         patch('psutil.Process') as mock_proc:
        mock_proc.return_value.name.return_value = "notepad.exe"
        yield

# Mock GPU/CUDA
@pytest.fixture
def mock_cuda():
    with patch('faster_whisper.WhisperModel') as mock_whisper:
        mock_whisper.return_value.transcribe.return_value = (
            [MagicMock(text="hello world")],
            MagicMock()
        )
        yield
```

#### 4.2 Testing Async Functions

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Luôn mark async tests với @pytest.mark.asyncio"""
    result = await some_async_function()
    assert result == expected
```

#### 4.3 Parametrize cho nhiều test cases

```python
@pytest.mark.parametrize("input,expected", [
    ("case1", "result1"),
    ("case2", "result2"),
    ("case3", "result3"),
])
def test_multiple_cases(input, expected):
    assert process(input) == expected
```

### 5. CI/CD Integration (GitHub Actions)

**File: `.github/workflows/test.yml`**

```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      - name: Run tests
        run: pytest --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

---

## 📊 MATRIX BAO PHỦ TEST

| Module | Tổng Test Cases | Unit | Integration | E2E |
|--------|----------------|------|-------------|-----|
| Wake Word | 8 | 8 | - | - |
| Application Control | 13 | 13 | - | - |
| System Control | 12 | 12 | - | - |
| STT Manager | 8 | 8 | - | - |
| Proxy | 9 | 5 | 4 | - |
| Agent Config | 4 | 4 | - | - |
| Main Flow | 10 | 3 | 7 | 3* |
| Safety/Security | 4 | 4 | - | - |
| **TỔNG** | **68** | **57** | **11** | **3** |

*Lưu ý: E2E tests yêu cầu hardware thực tế và được đánh dấu riêng.

---

## 🚀 KẾ HOẠCH TRIỂN KHAI

### Phase 1: Setup (Tuần 1)
- [ ] Tạo cấu trúc thư mục `tests/`
- [ ] Cài đặt pytest, pytest-asyncio
- [ ] Tạo fixtures cho common mocks (win32 API, subprocess)

### Phase 2: Unit Tests (Tuần 2-3)
- [ ] Viết test cho `parse_wake_word` (8 cases)
- [ ] Viết test cho `tools/apps.py` (13 cases)
- [ ] Viết test cho `tools/system.py` (12 cases)
- [ ] Viết test cho `core/proxy.py` translation logic
- [ ] Đạt ít nhất 70% code coverage

### Phase 3: Integration Tests (Tuần 4)
- [ ] Test proxy → Ollama API (4 cases)
- [ ] Test Agent flow (confirmation, tool registration)
- [ ] Mock STT output để test end-to-end logic

### Phase 4: E2E Tests (Tuần 5)
- [ ] Manual test trên thiết bị thực với mic, GPU
- [ ] Test các luồng: Wake → Command → Execute
- [ ] Document test results và known issues

### Phase 5: Automation (Tuần 6)
- [ ] Setup CI/CD với GitHub Actions
- [ ] Tạo pre-commit hooks chạy lint + test
- [ ] Monitoring coverage score trong mỗi PR

---

## 📝 GHI CHÚ QUAN TRỌNG

1. **Hardware Dependency**: STT và một số system tools yêu cầu hardware thực tế, nên cần mock để unit test độc lập
2. **Windows Only**: Dự án chỉ chạy trên Windows, cần đảm bảo CI/CD dùng `windows-latest`
3. **GPU Optional**: Faster-Whisper có thể fallback về CPU nếu không có NVIDIA GPU, cần test cả 2 trường hợp
4. **Proxy Dependency**: Cần Ollama server chạy ở port 11434 cho integration test, hoặc mock httpx
5. **Persona Consistency**: Test để đảm bảo Agent luôn giữ persona Igris (không thay đổi tone giữa các lệnh)

---

**Tài liệu này được tạo bởi QA Engineer dựa trên phân tích source code và yêu cầu của dự án Igris.**