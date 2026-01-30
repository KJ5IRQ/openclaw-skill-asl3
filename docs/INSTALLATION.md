# Installation Guide

This guide walks you through setting up the ASL Control system from scratch.

## Prerequisites

### Hardware
- Raspberry Pi (tested on Pi 4B, aarch64)
- AllStar Link node running ASL3
- Windows PC (for Telegram control via Moltbot)

### Software
- ASL 3.6.3 or later (Asterisk 22.5.2+)
- Python 3.13+ on Raspberry Pi
- Moltbot/Clawdbot installed on Windows
- PowerShell 5.1+ on Windows

## Part 1: Backend Setup (Raspberry Pi)

### 1. Install Python Dependencies

```bash
ssh asl@your-pi-ip

# Install system packages
sudo apt update
sudo apt install python3-pip python3-venv

# Create installation directory
sudo mkdir -p /opt/asl-agent
sudo chown $USER:$USER /opt/asl-agent
cd /opt/asl-agent
```

### 2. Set Up Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install fastapi==0.109.0 uvicorn[standard]==0.27.0 \
    pyyaml==6.0.1 python-multipart==0.0.6 \
    panoramisk==1.4 aiohttp==3.9.1
```

### 3. Copy Backend Files

Copy these files to `/opt/asl-agent/`:
- `asl_agent.py`
- `ami_client.py`
- `config.py`
- `event_handler.py`
- `requirements.txt`

```bash
# Example using git
cd /opt/asl-agent
git clone https://github.com/KJ5IRQ/openclaw-skill-asl3.git temp
cp temp/backend/*.py .
cp temp/backend/requirements.txt .
rm -rf temp
```

### 4. Configure AMI Access

Create AMI user in `/etc/asterisk/manager.conf`:

```bash
sudo nano /etc/asterisk/manager.conf
```

Add this section:

```ini
[asl-agent]
secret = GENERATE_STRONG_PASSWORD_HERE
read = system,call,reporting,command
write = command,reporting
deny = 0.0.0.0/0.0.0.0
permit = 127.0.0.1/255.255.255.255
```

Reload Asterisk manager:
```bash
sudo asterisk -rx "manager reload"
```

### 5. Create Configuration File

```bash
cd /opt/asl-agent
cp config.yaml.example config.yaml
nano config.yaml
```

Edit `config.yaml`:

```yaml
ami:
  host: "127.0.0.1"
  port: 5038
  username: "asl-agent"
  password: "YOUR_AMI_PASSWORD"  # From manager.conf

node:
  number: "YOUR_NODE_NUMBER"  # e.g., "2560"
  callsign: "YOUR_CALLSIGN"   # e.g., "W5XYZ"

api:
  host: "0.0.0.0"
  port: 8073
  api_key: "GENERATE_WITH_openssl_rand_-base64_32"

webhooks:
  enabled: false  # Keep disabled for v1.0

logging:
  level: "INFO"
  audit_file: "/opt/asl-agent/audit.log"

security:
  rate_limit_per_minute: 10
  require_confirmation: ["disconnectall"]
```

Generate API key:
```bash
openssl rand -base64 32
```

### 6. Test the Service

```bash
cd /opt/asl-agent
source venv/bin/activate
python3 asl_agent.py
```

Test in another terminal:
```bash
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:8073/
```

Should return:
```json
{
  "service": "ASL Agent",
  "node": "YOUR_NODE",
  "callsign": "YOUR_CALLSIGN",
  "status": "running",
  "ami_connected": true
}
```

Press Ctrl+C to stop the test.

### 7. Install Systemd Service

```bash
sudo cp asl-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable asl-agent
sudo systemctl start asl-agent
```

Check status:
```bash
sudo systemctl status asl-agent
sudo journalctl -u asl-agent -f
```

### 8. Configure Firewall (if enabled)

```bash
sudo ufw allow from 192.168.1.0/24 to any port 8073
```

Or allow from specific IP:
```bash
sudo ufw allow from YOUR_PC_IP to any port 8073
```

## Part 2: Frontend Setup (Windows)

### 1. Install Moltbot/Clawdbot

Follow the [Moltbot installation guide](https://github.com/cktang88/openclaw).

### 2. Install the Skill

```powershell
# Navigate to Moltbot skills directory
cd "$env:APPDATA\Roaming\npm\node_modules\clawdbot\skills"

# Clone or copy the skill
git clone https://github.com/KJ5IRQ/openclaw-skill-asl3.git asl-control

# Or manually copy the skill folder
```

### 3. Configure PowerShell Script

Edit `asl-control\skill\scripts\asl-api.ps1`:

```powershell
$ASL_API_BASE = "http://YOUR_PI_IP:8073"
$ASL_API_KEY = "YOUR_API_KEY_FROM_CONFIG_YAML"
```

### 4. Test PowerShell Functions

```powershell
. "$env:APPDATA\Roaming\npm\node_modules\clawdbot\skills\asl-control\skill\scripts\asl-api.ps1"

Get-NodeStatus
Get-ConnectedNodes
```

### 5. Configure Telegram Bot

Follow Moltbot's Telegram configuration to enable the skill.

## Part 3: Verification

### Test Backend API

```bash
# From Pi or Windows
curl -H "X-API-Key: YOUR_KEY" http://PI_IP:8073/status
```

### Test PowerShell

```powershell
Get-NodeStatus
Connect-Node -NodeNumber 55553
Get-ConnectedNodes
Disconnect-Node -NodeNumber 55553
```

### Test Telegram

Send to your bot:
```
Check my node status
Connect to node 55553
Who's connected?
Disconnect from node 55553
```

## Troubleshooting

### Backend won't start
- Check AMI credentials: `sudo asterisk -rx "manager show connected"`
- Check Python errors: `sudo journalctl -u asl-agent -n 50`
- Verify port 8073 not in use: `sudo netstat -tlnp | grep 8073`

### Cannot connect from Windows
- Check firewall on Pi
- Verify API key matches
- Test with curl from Pi first
- Check Pi IP address hasn't changed

### Connection commands don't work
- Verify AMI permissions in manager.conf
- Check Asterisk is running: `sudo asterisk -rx "core show version"`
- Review audit log: `tail -f /opt/asl-agent/audit.log`

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more common issues.

## Security Recommendations

1. **Change default passwords** - Generate strong AMI and API passwords
2. **Restrict network access** - Use firewall rules to limit API access
3. **Use HTTPS** - Consider reverse proxy with SSL for production
4. **Rotate API keys** - Periodically regenerate API keys
5. **Monitor audit log** - Review `/opt/asl-agent/audit.log` regularly
6. **Keep updated** - Watch for security updates

## Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system design
- Review [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Join discussions on GitHub for help and tips

## Upgrading

To upgrade to a new version:

```bash
cd /opt/asl-agent
sudo systemctl stop asl-agent
git pull  # or copy new files
sudo systemctl start asl-agent
```

Check [CHANGELOG.md](../CHANGELOG.md) for breaking changes.
