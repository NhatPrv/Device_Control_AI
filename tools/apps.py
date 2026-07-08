import asyncio
import re
import webbrowser

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
        
    if target == "chrome" and profile:
        profile_safe = profile.strip().replace('"', '')
        if not re.match(r"^[a-zA-Z0-9_\-\s]+$", profile_safe):
            return "Security warning: Profile name contains invalid characters."
        cmd = f"cmd.exe /c start \"\" \"chrome\" --profile-directory=\"{profile_safe}\""
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
            err_msg = stderr.decode(errors='ignore').strip()
            return f"Failed to open application '{app_name}'. Error: {err_msg}"
    except Exception as e:
        return f"System error while opening application '{app_name}': {str(e)}"
 
async def browser_control(action: str, url: str = None) -> str:
    """
    Control default browser actions (new_tab: Open new tab, open_url: Open specified URL).
    This tool opens the default system browser (which might be Microsoft Edge).
    Warning: If the user specifically requests to open the 'Google Chrome' browser, do NOT use this tool; use open_application(app_name='chrome') instead.
    """
    action_lower = action.lower().strip()
    
    if action_lower == "new_tab":
        try:
            # Open new tab defaulting to Google search
            await asyncio.to_thread(webbrowser.open_new_tab, "https://www.google.com")
            return "Successfully opened a new tab."
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
            
        try:
            await asyncio.to_thread(webbrowser.open, url_target)
            return f"Successfully navigated browser to: {url_target}"
        except Exception as e:
            return f"Failed to access page '{url_target}'. Error: {str(e)}"
    else:
        return f"Action '{action}' is not supported in browser controls."
