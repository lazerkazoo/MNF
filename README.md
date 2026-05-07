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

## Getting Started
### Python Dependencies

Install the following Python packages:
- `fuzzywuzzy` - `[can enter name]`
- `termcolor` - Terminal color output (recommened)

### Running the Program
1. Open a terminal in the directory containing `main.py`
#### With `pip` (built in to python)
2. Run the following command:
   ```sh
   pip install .
   ```
3. Execute the following command:
   ```sh
   python main.py
   ```
#### With [uv](https://docs.astral.sh/uv/getting-started/installation/)
2. Run the command:
  ```sh
  uv run main.py
  ```

The application will launch and display an interactive menu with available options.

---

## Documentation

For detailed information on using MNF, refer to the [MANUAL.md](MANUAL.md) file.
