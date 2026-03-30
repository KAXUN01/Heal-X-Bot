# CLI Terminal Page

## Description
The CLI Terminal page provides a web-based command-line interface for direct system access. It allows administrators to execute commands, run diagnostics, and manage the system without SSH access.

## Purpose
- Provide direct command-line access via web
- Execute system commands securely
- View command history
- Enable quick diagnostics
- Support command autocomplete

## Features

### 1. Terminal Interface
- Full terminal emulation in browser
- Command history navigation (↑/↓ arrows)
- Tab autocomplete for commands
- Color-coded output

### 2. Command Input
- Text input with prompt display
- Execute button and Enter key support
- Clear output option
- Copy/export functionality

### 3. Output Display
- Scrollable output area
- Syntax highlighting for:
  - Success messages (green)
  - Error messages (red)
  - Warning messages (yellow)
  - Info messages (blue)

### 4. Command History Panel
- List of previously executed commands
- Click to re-execute
- Clear history option
- Persistent across sessions

## Available Commands

### Built-in Commands
```
help              - Show available commands
clear             - Clear terminal output
history           - Show command history
status            - Show system status
services          - List all services
logs [service]    - Show recent logs
restart [service] - Restart a service
health            - System health check
metrics           - Show system metrics
```

### System Commands
Full shell command execution:
```bash
ls, cd, cat, grep, tail, head, ps, top, df, du,
docker, systemctl, journalctl, curl, wget, etc.
```

### Healing Bot Commands
```
heal status       - Healing system status
heal start        - Start auto-healing
heal stop         - Stop auto-healing
heal history      - View healing history
heal analyze      - Run AI analysis
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/cli/execute` | POST | Execute command |
| `/api/cli/history` | GET | Get command history |
| `/api/cli/clear-history` | POST | Clear history |
| `/api/cli/autocomplete` | GET | Get autocomplete suggestions |

## Security

### Command Restrictions
Dangerous commands are blocked or require confirmation:
```python
restricted_commands = [
    'rm -rf /',
    'mkfs',
    'dd if=',
    ':(){:|:&};:',  # Fork bomb
    'chmod -R 777 /',
]
```

### Sandboxed Execution
- Commands run with limited permissions
- Working directory restricted
- Resource limits applied
- Timeout enforcement

### Authentication
- Session-based authentication required
- Role-based access control
- Command logging for audit

## Technical Implementation

### Command Execution
```python
@app.post("/api/cli/execute")
async def execute_command(request: CLIRequest):
    if is_dangerous(request.command):
        return {"error": "Command not allowed"}
    
    result = subprocess.run(
        request.command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=30,
        cwd=WORKING_DIR
    )
    
    return {
        "output": result.stdout,
        "error": result.stderr,
        "exit_code": result.returncode
    }
```

### Autocomplete
```python
def get_autocomplete(partial_command):
    suggestions = []
    
    # Built-in commands
    for cmd in BUILTIN_COMMANDS:
        if cmd.startswith(partial_command):
            suggestions.append(cmd)
    
    # File paths
    if '/' in partial_command:
        suggestions.extend(glob.glob(partial_command + '*'))
    
    return suggestions[:10]
```

### JavaScript Functions
```javascript
executeCLI()            // Execute entered command
handleKeyPress(e)       // Handle Enter/arrows/Tab
getAutocomplete()       // Fetch suggestions
copyCLIOutput()         // Copy output to clipboard
exportCLIOutput()       // Export as file
clearCLIOutput()        // Clear display
clearCLIHistory()       // Clear history
```

## Output Formatting

### Color Classes
```css
.cli-output-line.success { color: #10b981; }  /* Green */
.cli-output-line.error   { color: #ef4444; }  /* Red */
.cli-output-line.warning { color: #f59e0b; }  /* Yellow */
.cli-output-line.info    { color: #3b82f6; }  /* Blue */
```

### Output Categories
```javascript
function categorizeOutput(line) {
    if (line.includes('error') || line.includes('failed'))
        return 'error';
    if (line.includes('warning') || line.includes('warn'))
        return 'warning';
    if (line.includes('success') || line.includes('ok'))
        return 'success';
    return 'info';
}
```

## Configuration

### Terminal Settings
```json
{
  "max_output_lines": 1000,
  "command_timeout": 30,
  "history_size": 100,
  "prompt": "{user}@healing-bot:{path}$",
  "restricted_commands": ["rm -rf", "mkfs"],
  "working_directory": "/home/kasun"
}
```

## User Actions
- Type and execute commands
- Navigate command history
- Use Tab for autocomplete
- Copy/export output
- Clear output or history

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Execute command |
| `↑` | Previous command |
| `↓` | Next command |
| `Tab` | Autocomplete |
| `Ctrl+C` | Cancel (copy) |
| `Ctrl+L` | Clear screen |

## Related Pages
- [Services](04_SERVICES.md) - Service management
- [Logs & AI](07_LOGS_AI.md) - Log viewing
- [Processes](05_PROCESSES.md) - Process control
