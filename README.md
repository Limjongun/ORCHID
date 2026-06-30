# ORCHID Local AI Desktop Assistant

**Status: Under Development (v0.3.0-dev)**

ORCHID is a robust, local-first artificial intelligence desktop assistant designed for system-level automation and natural language execution of complex administrative and operational tasks. The architecture utilizes a local Large Language Model (LLM) backend via Ollama, combined with an extensible tool-calling framework (Agentic Loop) capable of interacting with the host operating system, filesystem, network, hardware, and productivity applications.

## Architecture Overview

The system operates on an Agentic Loop mechanism supporting up to 15 recursive tool-calling iterations per user request. This enables ORCHID to execute multi-step workflows autonomously without manual intervention.

### Core Components
- **LLM Engine (`core/llm_engine.py`)**: Manages model context, system prompts, tool routing, and backend switching (Local Ollama vs. Azure OpenAI).
- **Security Sandbox (`core/sandbox.py`)**: Intercepts high-risk function calls (e.g., file deletion, terminal execution, git modifications) and enforces user-authorization protocols via blocking UI prompts.
- **UI Application (`ui/app.py`)**: Built on `CustomTkinter`, providing a multithreaded GUI interface that displays real-time execution states and dynamic tool invocation logs.

## Plugin Ecosystem & Tool Integrations

ORCHID's capabilities are modularly defined across several plugin namespaces. The system currently maintains over 55 active function tools:

1. **File System Management (`plugins/file_explorer.py`)**
   - Directory traversal, file reading/writing, regex-based file searching, recursive item deletion, item movement/renaming, and ZIP compression algorithms.

2. **System Control & Automation (`plugins/system_control.py`)**
   - Process execution management, force termination of processes, OS power states (sleep/hibernate/shutdown), audio level manipulation, and Chromium profile management.

3. **Hardware Diagnostics (`plugins/hardware_info.py`)**
   - Comprehensive extraction of physical and logical CPU metrics, memory utilization, disk partition mapping, GPU string identification, and Windows driver querying.

4. **Network & Web Parsing (`plugins/web_network.py`)**
   - Headless DuckDuckGo search querying, web navigation, IP address resolution, and network latency diagnostics.

5. **Terminal Execution (`plugins/terminal_control.py`)**
   - Direct parsing and execution of PowerShell and Bash commands within a subprocess shell environment.

6. **Version Control (`plugins/git_control.py`)**
   - Automated git command-line interface handling for repository initialization, staging, committing, and remote synchronization. Modifying commands are sandboxed.

7. **Productivity Operations (`plugins/office_tools.py`)**
   - Automated parsing and generation of common document formats: PDF (via PyMuPDF), Word `.docx` (via python-docx), Excel `.xlsx` (via openpyxl), and CSV processing.

8. **Robotic Process Automation (`plugins/input_control.py`)**
   - Direct hardware-level inputs for mouse telemetry (move/click/drag) and keyboard event simulation via `pyautogui`. Invoked strictly under explicit user request for UI-based automations.

## Installation and Setup

### Prerequisites
- Python 3.11+
- Ollama runtime environment (with `qwen2.5:latest` model initialized locally on port `11434`)
- Windows OS (Required for specific hardware/driver/RPA queries)

### Deployment

1. Clone the repository:
   ```bash
   git clone https://github.com/Limjongun/ORCHID.git
   cd ORCHID
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Execute the application:
   ```bash
   python main.py
   ```

## Development Roadmap

The following modules are planned for future integration:
- **Clipboard Management**: Bidirectional clipboard data parsing and assignment.
- **Advanced Process Telemetry**: Thread-level analysis and startup sequence management.
- **Screen Vision (OCR)**: Visual parsing of on-screen elements via Tesseract.
- **Notification Daemon**: Native OS integration for task completion toasts.
- **Image Processing Algorithms**: Resolution mutation, format conversion, and compression parameters.

## License
Proprietary / Under Development.
