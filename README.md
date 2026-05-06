# MNF - Modpack Manager

A command-line tool for managing Minecraft modpacks with Fabric, supporting content from Modrinth.

---

## Platform Compatibility

| Platform | Status | Notes |
|----------|--------|-------|
| Linux | ✅ Supported | Fully tested and supported |
| macOS | ❓ Unknown | Not tested; likely works but untested |
| Windows | ❌ Unsupported | Not tested but definitely does not work |

**Launcher Requirement:** Use the official Minecraft launcher from [minecraft.net](https://www.minecraft.net/en-us/download) or [flathub.org](https://flathub.org/en/apps/com.mojang.Minecraft). Other launchers may function but will not display the modpack launch option.

---

## System Requirements

### Core Dependencies

- **[Python 3](https://www.python.org/downloads/)** - Required for running the application
- **[Java](https://www.java.com/en/download/)** - Required for installing Fabric
- **[curl](https://curl.se/download.html)** - Required for downloading files (pre-installed on Linux)

### Python Dependencies

Install the following Python packages:
- `requests` - HTTP library for making web requests
- `termcolor` - Terminal color output

**Installation:**

1. Open a terminal in the directory containing `main.py`
2. Run the following command:
   ```sh
   pip install .
   ```
   (Python must be installed and available in your PATH)

---

## Getting Started

### Running the Application

1. Open a terminal in the directory containing `main.py`
2. Execute the following command:
   ```sh
   python main.py
   ```

The application will launch and display an interactive menu with available options.

---

## Documentation

For detailed information on using MNF, refer to the [MANUAL.md](MANUAL.md) file.
