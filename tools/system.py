import asyncio
import re

# PowerShell script to communicate with Windows Core Audio API via C# (no Admin rights required)
AUDIO_POWERSHELL_SCRIPT = """
Add-Type -TypeDefinition @'
using System.Runtime.InteropServices;
[Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioEndpointVolume {
    int f(); int g(); int h(); int i();
    int SetMasterVolumeLevelScalar(float fLevel, System.Guid pguidEventContext);
    int j(); int GetMasterVolumeLevelScalar(out float pfLevel);
    int k(); int l(); int m(); int n();
    int SetMute(bool bMute, System.Guid pguidEventContext);
}
[Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice { int Activate(ref System.Guid id, int clsCtx, int activationParams, out IAudioEndpointVolume aev); }
[Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator { int f(); int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice endpoint); }
[ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")] class MMDeviceEnumeratorComObject { }

public class Audio {
    private static IAudioEndpointVolume GetVolumeObject() {
        var enumerator = new MMDeviceEnumeratorComObject() as IMMDeviceEnumerator;
        IMMDevice dev = null;
        enumerator.GetDefaultAudioEndpoint(0, 1, out dev);
        IAudioEndpointVolume epv = null;
        var epvid = typeof(IAudioEndpointVolume).GUID;
        dev.Activate(ref epvid, 23, 0, out epv);
        return epv;
    }
    public static float GetVolume() {
        var epv = GetVolumeObject();
        float level = 0f;
        epv.GetMasterVolumeLevelScalar(out level);
        return level;
    }
    public static void SetVolume(float level) {
        var epv = GetVolumeObject();
        epv.SetMasterVolumeLevelScalar(level, System.Guid.Empty);
    }
}
'@
"""

async def get_battery_status() -> str:
    """
    Get battery percentage and current charging state via PowerShell.
    """
    try:
        # Get battery percentage
        pct_cmd = "powershell -Command \"(Get-CimInstance Win32_Battery).EstimatedChargeRemaining\""
        process_pct = await asyncio.create_subprocess_shell(
            pct_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout_pct, _ = await process_pct.communicate()
        pct_str = stdout_pct.decode().strip()
        
        # Get power line status (Online: charging/AC, Offline: discharging/battery)
        status_cmd = "powershell -Command \"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SystemInformation]::PowerStatus.PowerLineStatus\""
        process_status = await asyncio.create_subprocess_shell(
            status_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout_status, _ = await process_status.communicate()
        status_str = stdout_status.decode().strip()
        
        if not pct_str:
            return "Report: Unable to locate battery details on this device."
            
        charging_text = "charging" if status_str == "Online" else "on battery power (not charging)"
        return f"Report: Current battery is at {pct_str}%, system is {charging_text}."
    except Exception as e:
        return f"Error checking battery: {str(e)}"

async def control_volume(action: str) -> str:
    """
    Increase/decrease system volume by calling Core Audio API via PowerShell C#.
    Actions supported: 'increase' / 'tăng', 'decrease' / 'giảm'.
    """
    action_lower = action.lower().strip()
    try:
        # Get current volume (returns float value from 0.0 to 1.0)
        get_script = AUDIO_POWERSHELL_SCRIPT + "\n[Audio]::GetVolume()"
        process_get = await asyncio.create_subprocess_exec(
            "powershell", "-Command", get_script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout_get, stderr_get = await process_get.communicate()
        vol_str = stdout_get.decode().strip()
        
        if not vol_str:
            err_msg = stderr_get.decode().strip()
            return f"Failed to retrieve current volume. Error: {err_msg}"
            
        current_vol = float(vol_str)
        
        if action_lower in ["increase", "tăng"]:
            # Increase by 10% (0.1)
            new_vol = min(current_vol + 0.1, 1.0)
            action_desc = "Increased"
        elif action_lower in ["decrease", "giảm"]:
            # Decrease by 10% (0.1)
            new_vol = max(current_vol - 0.1, 0.0)
            action_desc = "Decreased"
        else:
            return f"Volume control action '{action}' is not supported."
            
        if new_vol == current_vol:
            return f"Report: System volume is already at boundary limit ({int(current_vol * 100)}%)."
            
        # Set new volume
        set_script = AUDIO_POWERSHELL_SCRIPT + f"\n[Audio]::SetVolume({new_vol:.2f})"
        process_set = await asyncio.create_subprocess_exec(
            "powershell", "-Command", set_script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process_set.communicate()
        
        return f"Report: {action_desc} system volume from {int(current_vol * 100)}% to {int(new_vol * 100)}%."
    except Exception as e:
        return f"Error while controlling volume: {str(e)}"

async def control_brightness(action: str) -> str:
    """
    Increase/decrease laptop screen brightness via WMI/CimInstance.
    Actions supported: 'increase' / 'tăng', 'decrease' / 'giảm'.
    """
    action_lower = action.lower().strip()
    try:
        # Get current brightness (0 - 100)
        get_cmd = "powershell -Command \"(Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness).CurrentBrightness\""
        process_get = await asyncio.create_subprocess_shell(
            get_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout_get, _ = await process_get.communicate()
        bright_str = stdout_get.decode().strip()
        
        if not bright_str:
            return "WMI monitor brightness class not supported on this device."
            
        current_bright = int(bright_str)
        
        if action_lower in ["increase", "tăng"]:
            # Increase by 10%
            new_bright = min(current_bright + 10, 100)
            action_desc = "Increased"
        elif action_lower in ["decrease", "giảm"]:
            # Decrease by 10%
            new_bright = max(current_bright - 10, 0)
            action_desc = "Decreased"
        else:
            return f"Brightness control action '{action}' is not supported."
            
        if new_bright == current_bright:
            return f"Report: Screen brightness is already at boundary limit ({current_bright}%)."
            
        # Set new brightness
        set_cmd = f"powershell -Command \"$monitor = Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods; Invoke-CimMethod -InputObject $monitor -MethodName WmiSetBrightness -Arguments @{{Brightness = {new_bright}; Timeout = 1}}\""
        process_set = await asyncio.create_subprocess_shell(
            set_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process_set.communicate()
        
        return f"Report: {action_desc} screen brightness from {current_bright}% to {new_bright}%."
    except Exception as e:
        return f"Error while controlling screen brightness: {str(e)}"
