# OpenClaw Skill: AllStar Link Control

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![ASL3](https://img.shields.io/badge/ASL-3.6.3-green.svg)](https://www.allstarlink.org/)

Control your AllStar Link node naturally through Telegram or PowerShell, powered by [Moltbot/Clawdbot](https://github.com/openclaw/openclaw).

> **📚 New to Linux, GitHub, or Python?** Check out the [Complete Beginner's Guide](docs/BEGINNER_GUIDE.md) for step-by-step instructions with explanations of every command.



## Features

- 🤖 **Natural Language Control** - "Connect to node 55553" via Telegram
- 💻 **PowerShell API** - Direct commands from Windows terminal
- 🔐 **Secure** - API key authentication, localhost-only AMI access
- 📊 **Monitoring** - Real-time node status and connection tracking
- 📝 **Audit Trail** - Complete command history logging
- 🔌 **ASL3 Compatible** - Works with AllStar Link 3

## Quick Start

### Prerequisites

- AllStar Link 3 node (tested on ASL 3.6.3)
- Raspberry Pi (tested on Pi 4B, aarch64)
- Python 3.13+
- Moltbot/Clawdbot (for Telegram control)

### Installation

**Choose your path:**

- **[Complete Beginner's Guide](docs/BEGINNER_GUIDE.md)** - Start here if you're new to Linux, SSH, or GitHub. Everything is explained step-by-step.
- **[Installation Guide](docs/INSTALLATION.md)** - For experienced users. Assumes familiarity with Linux, Git, and Python.

**Quick overview:**

1. **Backend (Pi):** Install ASL Agent API service
2. **Frontend (Windows):** Install Moltbot skill for Telegram control
3. **Configure:** Set your node number, API keys, and credentials

## Usage Examples

### Via Telegram

```
You: Check my node status
Bot: 🔘 Node 2560 (W5XYZ) Status
     ⏱️ Uptime: 127 hours
     🔢 Keyups Today: 142
     🔗 Connected Nodes: 3

You: Connect to node 55553
Bot: ✅ Connected to node 55553 in transceive (TX/RX) mode

You: Who's connected?
Bot: 📡 Connected Nodes (2)
     • Node 54199
     • Node 55553
```

### Via PowerShell

```powershell
# Load functions
. "$env:APPDATA\Roaming\npm\node_modules\clawdbot\skills\asl-control\scripts\asl-api.ps1"

# Check status
Get-NodeStatus

# Connect to a node
Connect-Node -NodeNumber 55553

# List connections
Get-ConnectedNodes

# Disconnect
Disconnect-Node -NodeNumber 55553
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│            YOUR RASPBERRY PI                    │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │  ASTERISK / ASL3                         │  │
│  │  - Your AllStar Node                     │  │
│  │  - AMI on port 5038                      │  │
│  └─────────────────┬────────────────────────┘  │
│                    │                            │
│  ┌─────────────────▼────────────────────────┐  │
│  │  ASL AGENT API (FastAPI)                │  │
│  │  - REST API on port 8073                 │  │
│  │  - Translates REST → AMI commands        │  │
│  └─────────────────┬────────────────────────┘  │
└────────────────────┼─────────────────────────────┘
                     │
                     │ HTTP API Calls
                     │
        ┌────────────┴──────────────┐
        │                           │
┌───────▼────────┐        ┌─────────▼────────┐
│   TELEGRAM     │        │   POWERSHELL     │
│   (Mobile)     │        │   (Windows)      │
│                │        │                  │
│  Natural       │        │  Direct API      │
│  Language      │        │  Functions       │
└────────────────┘        └──────────────────┘
```

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed system design.

## Available Commands

### Node Control
- Connect to nodes (transceive or monitor mode)
- Disconnect from specific nodes
- Disconnect from all nodes

### Monitoring
- Check node status (uptime, keyups, connections)
- List connected nodes with mode information
- View command audit log

## Security

- API key authentication on all endpoints
- Localhost-only AMI binding
- Command audit trail
- No credentials stored in logs

See [SECURITY.md](docs/SECURITY.md) for security best practices.

## Compatibility

**Tested on:**
- ASL: 3.6.3 (Asterisk 22.5.2)
- OS: Debian 13 (Trixie)
- Hardware: Raspberry Pi 4B (aarch64)
- Python: 3.13.5

## Known Issues

- Node connection verification takes 8-10 seconds
- Webhook notifications disabled pending batching implementation

See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for common issues.

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## Roadmap

**Future versions may include:**
- Macro execution support
- Raw DTMF sequence sending
- Webhook notification batching
- Web dashboard interface
- Multi-node support

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Credits

Created by KJ5IRQ

Built for the [Moltbot/Clawdbot](https://github.com/openclaw/openclaw) ecosystem.

## Support

- **Issues:** Use GitHub Issues for bug reports
- **Discussions:** Use GitHub Discussions for questions
- **Documentation:** See `docs/` folder

## Acknowledgments

- AllStar Link community
- Moltbot/Clawdbot developers
- Asterisk project
