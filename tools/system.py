import asyncio
import re

# Mã PowerShell dùng để giao tiếp với Windows Core Audio API qua C# (không cần quyền Admin)
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
    Lấy thông tin phần trăm pin và trạng thái sạc hiện tại qua PowerShell.
    """
    try:
        # Lấy phần trăm pin
        pct_cmd = "powershell -Command \"(Get-CimInstance Win32_Battery).EstimatedChargeRemaining\""
        process_pct = await asyncio.create_subprocess_shell(
            pct_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout_pct, _ = await process_pct.communicate()
        pct_str = stdout_pct.decode().strip()
        
        # Lấy trạng thái cắm nguồn (Online: đang sạc/cắm AC, Offline: đang dùng pin)
        status_cmd = "powershell -Command \"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SystemInformation]::PowerStatus.PowerLineStatus\""
        process_status = await asyncio.create_subprocess_shell(
            status_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout_status, _ = await process_status.communicate()
        status_str = stdout_status.decode().strip()
        
        if not pct_str:
            return "Báo cáo chủ nhân: Không thể tìm thấy thông tin pin trên thiết bị này."
            
        charging_text = "đang cắm sạc" if status_str == "Online" else "đang sử dụng pin (không sạc)"
        return f"Báo cáo chủ nhân: Pin hiện tại đạt {pct_str}%, hệ thống {charging_text}."
    except Exception as e:
        return f"Gặp lỗi khi kiểm tra pin: {str(e)}"

async def control_volume(action: str) -> str:
    """
    Tăng/giảm âm lượng hệ thống bằng cách gọi Core Audio API qua PowerShell C#.
    Các hành động hỗ trợ: 'increase' / 'tăng', 'decrease' / 'giảm'.
    """
    action_lower = action.lower().strip()
    try:
        # Lấy âm lượng hiện tại (trả về giá trị float từ 0.0 đến 1.0)
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
            return f"Không thể lấy thông tin âm lượng. Lỗi: {err_msg}"
            
        current_vol = float(vol_str)
        
        if action_lower in ["increase", "tăng"]:
            # Tăng thêm 10% (0.1)
            new_vol = min(current_vol + 0.1, 1.0)
            action_desc = "Tăng"
        elif action_lower in ["decrease", "giảm"]:
            # Giảm bớt 10% (0.1)
            new_vol = max(current_vol - 0.1, 0.0)
            action_desc = "Giảm"
        else:
            return f"Hành động điều khiển âm lượng '{action}' không được hỗ trợ."
            
        if new_vol == current_vol:
            return f"Báo cáo: Âm lượng hệ thống đã ở mức tối đa/tối thiểu ({int(current_vol * 100)}%)."
            
        # Ghi nhận âm lượng mới
        set_script = AUDIO_POWERSHELL_SCRIPT + f"\n[Audio]::SetVolume({new_vol:.2f})"
        process_set = await asyncio.create_subprocess_exec(
            "powershell", "-Command", set_script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process_set.communicate()
        
        return f"Báo cáo: Đã {action_desc.lower()} âm lượng hệ thống từ {int(current_vol * 100)}% lên {int(new_vol * 100)}%."
    except Exception as e:
        return f"Gặp lỗi khi điều khiển âm lượng: {str(e)}"

async def control_brightness(action: str) -> str:
    """
    Tăng/giảm độ sáng màn hình laptop qua WMI/CimInstance.
    Các hành động hỗ trợ: 'increase' / 'tăng', 'decrease' / 'giảm'.
    """
    action_lower = action.lower().strip()
    try:
        # Lấy độ sáng hiện tại (0 - 100)
        get_cmd = "powershell -Command \"(Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness).CurrentBrightness\""
        process_get = await asyncio.create_subprocess_shell(
            get_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout_get, _ = await process_get.communicate()
        bright_str = stdout_get.decode().strip()
        
        if not bright_str:
            return "Không tìm thấy cấu hình màn hình laptop hỗ trợ WMI."
            
        current_bright = int(bright_str)
        
        if action_lower in ["increase", "tăng"]:
            # Tăng thêm 10%
            new_bright = min(current_bright + 10, 100)
            action_desc = "Tăng"
        elif action_lower in ["decrease", "giảm"]:
            # Giảm bớt 10%
            new_bright = max(current_bright - 10, 0)
            action_desc = "Giảm"
        else:
            return f"Hành động điều khiển độ sáng '{action}' không được hỗ trợ."
            
        if new_bright == current_bright:
            return f"Báo cáo: Độ sáng màn hình đã ở mức giới hạn ({current_bright}%)."
            
        # Thiết lập độ sáng mới
        set_cmd = f"powershell -Command \"$monitor = Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods; Invoke-CimMethod -InputObject $monitor -MethodName WmiSetBrightness -Arguments @{{Brightness = {new_bright}; Timeout = 1}}\""
        process_set = await asyncio.create_subprocess_shell(
            set_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process_set.communicate()
        
        return f"Báo cáo: Đã {action_desc.lower()} độ sáng màn hình từ {current_bright}% lên {new_bright}%."
    except Exception as e:
        return f"Gặp lỗi khi điều khiển độ sáng màn hình: {str(e)}"
