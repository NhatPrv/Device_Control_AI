# Project Summary: Igris Laptop Control Assistant

This project develops a 100% locally running Laptop Control Assistant on Windows 11, operating as a loyal digital guardian knight named **Igris**.

## 🖥️ Hardware Environment
- **Device**: Legion 5 Pro 2023
- **CPU**: Intel Core i9-13900HX
- **GPU**: NVIDIA GeForce RTX 4060
- **OS**: Windows 11

## ⚙️ Tech Stack
1. **Language & Runtime**: Asynchronous Python (`asyncio`).
2. **Agent Framework**: Google Antigravity SDK (`LocalAgentConfig`).
3. **Large Language Model (LLM)**: Local Ollama endpoint (routed via a translation proxy on port 8000 to port 11434) executing the `qwen2.5:7b` model.
4. **Speech-to-Text (STT)**: `faster-whisper` running directly on the Nvidia GPU via CUDA (`device="cuda"`, `compute_type="float16"`).

## ⚔️ Key Features
- **Application Control (`tools/apps.py`)**:
  - Open system applications (Chrome, Notepad, Calculator, etc.).
  - Control browser actions (Open a new tab, navigate to a specified URL).
- **System Control (`tools/system.py`)**:
  - Query battery level and power status via PowerShell.
  - Adjust (increase/decrease) system master volume.
  - Adjust (increase/decrease) laptop screen brightness.
- **Real-time Speech Interaction (`core/stt.py`)**:
  - Record audio from microphone and perform multilingual speech recognition.
- **Dialogue Processing & Guardian Persona (`core/agent.py`)**:
  - Embody Igris's respectful, serious, and extremely concise communication style.
  - Automatically match and execute corresponding system tools based on Master's instructions.

## 🛡️ System Safety Directives
- Absolutely no integration of destructive or dangerous functions, such as deleting system files/folders, creating arbitrary files outside the workspace, shutting down, or rebooting the device.
- If the Master issues a destructive or unsafe command, Igris will respectfully refuse to execute it to protect the safety of the system.
