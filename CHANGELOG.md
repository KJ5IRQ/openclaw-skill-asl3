# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-30

### Added
- Initial release
- Natural language control via Telegram using Moltbot
- PowerShell API functions for Windows
- REST API backend (FastAPI) running on Raspberry Pi
- Node connection management (connect, disconnect, disconnect-all)
- Real-time node status monitoring
- Connected nodes listing with mode information
- API key authentication
- Command audit logging
- ASL3 / Asterisk AMI integration
- Comprehensive documentation

### Features
- `Get-NodeStatus` - View node uptime, keyups, and connection count
- `Get-ConnectedNodes` - List all connected nodes
- `Connect-Node` - Connect to nodes in transceive or monitor mode
- `Disconnect-Node` - Disconnect from specific nodes  
- `Disconnect-AllNodes` - Drop all connections
- `Get-AuditLog` - View command history

### Known Issues
- Connection verification takes 8-10 seconds
- Webhook notifications disabled (needs batching implementation)

### Tested On
- ASL 3.6.3 (Asterisk 22.5.2)
- Debian 13 (Trixie)
- Raspberry Pi 4B (aarch64)
- Python 3.13.5

[1.0.0]: https://github.com/KJ5IRQ/openclaw-skill-asl3/releases/tag/v1.0.0
