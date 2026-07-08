import asyncio
import re
import webbrowser

async def open_application(app_name: str) -> str:
    """
    Mở phần mềm hệ thống (Chrome, Notepad, Calculator...).
    """
    app_lower = app_name.lower().strip()
    
    # Bản đồ ánh xạ tên ứng dụng tiếng Việt / tiếng Anh phổ biến
    app_map = {
        "chrome": "chrome",
        "google chrome": "chrome",
        "trình duyệt chrome": "chrome",
        "notepad": "notepad",
        "sổ ghi chép": "notepad",
        "calculator": "calc",
        "máy tính": "calc",
        "word": "winword",
        "microsoft word": "winword",
        "excel": "excel",
        "microsoft excel": "excel",
        "explorer": "explorer",
        "file explorer": "explorer",
        "cmd": "cmd",
        "command prompt": "cmd",
        "powershell": "powershell",
        "paint": "mspaint"
    }
    
    target = app_map.get(app_lower, app_lower)
    
    # Kiểm tra an toàn: Chỉ cho phép ký tự chữ, số, dấu cách và dấu gạch dưới/gạch ngang/chấm
    if not re.match(r"^[a-zA-Z0-9_\-\.\s]+$", target):
        return "Cảnh báo an toàn: Tên ứng dụng chứa các ký tự không hợp lệ."
        
    cmd = f"cmd.exe /c start \"\" \"{target}\""
    
    try:
        # Sử dụng create_subprocess_shell để chạy lệnh start trong cmd
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            return f"Đã mở ứng dụng '{app_name}' thành công."
        else:
            err_msg = stderr.decode(errors='ignore').strip()
            return f"Không thể mở ứng dụng '{app_name}'. Lỗi: {err_msg}"
    except Exception as e:
        return f"Lỗi hệ thống khi mở ứng dụng '{app_name}': {str(e)}"

async def browser_control(action: str, url: str = None) -> str:
    """
    Thao tác trình duyệt (new_tab: Mở tab mới, open_url: mở trang web chỉ định).
    """
    action_lower = action.lower().strip()
    
    if action_lower == "new_tab":
        try:
            # Mở tab mới mặc định trang tìm kiếm Google
            await asyncio.to_thread(webbrowser.open_new_tab, "https://www.google.com")
            return "Đã mở tab mới thành công."
        except Exception as e:
            return f"Không thể mở tab mới. Lỗi: {str(e)}"
            
    elif action_lower == "open_url":
        if not url:
            return "Lỗi: Không tìm thấy địa chỉ URL hợp lệ."
            
        url_target = url.strip()
        
        # Chuẩn hóa URL nếu chưa có schema
        if not re.match(r"^https?://", url_target, re.IGNORECASE):
            url_target = "https://" + url_target
            
        # Kiểm tra tính hợp lệ cơ bản của URL để đảm bảo an toàn
        if not re.match(r"^https?://[a-zA-Z0-9\-\.\/\?\&\=\#\_\%]+$", url_target):
            return "Cảnh báo an toàn: Địa chỉ URL chứa ký tự không hợp lệ."
            
        try:
            await asyncio.to_thread(webbrowser.open, url_target)
            return f"Đã điều hướng trình duyệt đến trang: {url_target}"
        except Exception as e:
            return f"Không thể truy cập trang '{url_target}'. Lỗi: {str(e)}"
    else:
        return f"Hành động '{action}' không được hỗ trợ trong điều khiển trình duyệt."
