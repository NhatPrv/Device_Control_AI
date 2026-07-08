import asyncio
import re
import urllib.parse
from typing import Literal
import win32gui
import win32process
import psutil

async def get_active_browser() -> str:
    """
    Check if the active window is 'chrome' (Google Chrome) or 'browser' (Cốc Cốc).
    Returns the active browser target command name, defaulting to 'chrome'.
    """
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        proc = psutil.Process(pid)
        proc_name = proc.name().lower()
        if "chrome" in proc_name:
            return "chrome"
        elif "browser" in proc_name:  # Cốc Cốc executable is 'browser.exe'
            return "browser"
    except Exception:
        pass
    return "chrome"

async def open_application(app_name: str, profile: str = None) -> str:
    """
    Open a local system application by name (e.g. 'chrome' to open Google Chrome, 'notepad', 'calc' for calculator).
    Use this tool if the user explicitly asks to open or launch the Google Chrome browser or any local app.
    
    Parameters:
    - app_name: Name of the app (e.g., 'chrome', 'notepad').
    - profile: Optional. If app_name is 'chrome', specify the profile directory name (e.g., 'Default', 'Profile 1', 'Profile 2') to open Chrome with that specific profile.
    """
    app_lower = app_name.lower().strip()
    
    # Common Vietnamese/English application mapping dictionary
    app_map = {
        "chrome": "chrome",
        "google chrome": "chrome",
        "trình duyệt chrome": "chrome",
        "coc coc": "browser",
        "cốc cốc": "browser",
        "coc coc browser": "browser",
        "trình duyệt cốc cốc": "browser",
        "cocococ": "browser",
        "cocococ browser": "browser",
        "go go": "browser",
        "go go browser": "browser",
        "gogo": "browser",
        "gogo browser": "browser",
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
    
    # Safety check: Only allow alphanumeric characters, spaces, dots, dashes, and underscores.
    if not re.match(r"^[a-zA-Z0-9_\-\.\s]+$", target):
        return "Security warning: Application name contains invalid characters."
        
    if target in ["chrome", "browser"]:
        profile_to_use = profile if profile else "Default"
        profile_safe = profile_to_use.strip().replace('"', '')
        if not re.match(r"^[a-zA-Z0-9_\-\s]+$", profile_safe):
            return "Security warning: Profile name contains invalid characters."
        cmd = f"cmd.exe /c start \"\" \"{target}\" --profile-directory=\"{profile_safe}\""
    else:
        cmd = f"cmd.exe /c start \"\" \"{target}\""
    
    try:
        # Use create_subprocess_shell to run start command in cmd
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            if profile:
                return f"Successfully opened application '{app_name}' with profile '{profile}'."
            return f"Successfully opened application '{app_name}'."
        else:
            # Fallback: application not found, search on active browser
            browser_to_use = await get_active_browser()
            browser_name = "Google Chrome" if browser_to_use == "chrome" else "Cốc Cốc"
            
            search_query = f"Download {app_name}"
            search_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(search_query)}"
            cmd_search = f'cmd.exe /c start "" "{browser_to_use}" --profile-directory="Default" "{search_url}"'
            
            proc_search = await asyncio.create_subprocess_shell(
                cmd_search,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc_search.communicate()
            return f"I could not find the application '{app_name}' on your system. I have opened a Google search in {browser_name} to search for '{app_name}' instead."
            
    except Exception as e:
        # Fallback in case of launch exception
        try:
            browser_to_use = await get_active_browser()
            browser_name = "Google Chrome" if browser_to_use == "chrome" else "Cốc Cốc"
            search_query = f"Download {app_name}"
            search_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(search_query)}"
            cmd_search = f'cmd.exe /c start "" "{browser_to_use}" --profile-directory="Default" "{search_url}"'
            proc_search = await asyncio.create_subprocess_shell(
                cmd_search,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc_search.communicate()
            return f"I could not find the application '{app_name}' on your system. I have opened a Google search in {browser_name} to search for '{app_name}' instead."
        except Exception:
            pass
        return f"System error while opening application '{app_name}': {str(e)}"
 
async def browser_control(action: Literal["new_tab", "open_url"], url: str = None) -> str:
    """
    Perform browser operations like opening a new tab or navigating to a specific URL.
    This opens the URL directly inside the currently active browser (Google Chrome or Cốc Cốc) to match user context.
    """
    action_lower = action.lower().strip()
    browser_to_use = await get_active_browser()
    browser_name = "Google Chrome" if browser_to_use == "chrome" else "Cốc Cốc"
    
    if action_lower == "new_tab":
        cmd = f'cmd.exe /c start "" "{browser_to_use}" --profile-directory="Default" "https://www.google.com"'
        try:
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            return f"Successfully opened a new tab in {browser_name}."
        except Exception as e:
            return f"Failed to open a new tab. Error: {str(e)}"
            
    elif action_lower == "open_url":
        if not url:
            return "Error: Valid URL not specified."
            
        url_target = url.strip()
        
        # Normalize URL if no schema is provided
        if not re.match(r"^https?://", url_target, re.IGNORECASE):
            url_target = "https://" + url_target
            
        # Basic URL validation to ensure safety
        if not re.match(r"^https?://[a-zA-Z0-9\-\.\/\?\&\=\#\_\%]+$", url_target):
            return "Security warning: URL contains invalid characters."
            
        cmd = f'cmd.exe /c start "" "{browser_to_use}" --profile-directory="Default" "{url_target}"'
        try:
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            return f"Successfully navigated {browser_name} to: {url_target}"
        except Exception as e:
            return f"Failed to access page '{url_target}'. Error: {str(e)}"
    else:
        return f"Action '{action}' is not supported in browser controls."
