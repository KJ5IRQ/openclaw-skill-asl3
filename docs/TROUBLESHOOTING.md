# Troubleshooting Guide

## Quick Diagnostic Steps

When something isn't working, follow these steps in order:

1. **Check if the API service is running**
2. **Verify API can reach Asterisk**
3. **Test with curl before PowerShell**
4. **Check logs for errors**
5. **Verify configuration is correct**

## Common Issues

### API Service Won't Start

#### Symptom
```bash
sudo systemctl status asl-agent
# Shows: Failed to start or inactive (dead)
```

#### Diagnosis

**Check the logs:**
```bash
sudo journalctl -u asl-agent -n 50
```

**Common Causes:**

**1. Port 8073 Already in Use**

```bash
sudo netstat -tlnp | grep 8073
```

If something is using port 8073:
- Change the port in `config.yaml`
- Or stop the conflicting service

**2. Config File Not Found**

```
FileNotFoundError: Config file not found: /opt/asl-agent/config.yaml
```

Fix:
```bash
cd /opt/asl-agent
ls -la config.yaml  # Does it exist?
# If not, copy from example
cp config.yaml.example config.yaml
nano config.yaml  # Fill in your settings
```

**3. Python Package Missing**

```
ModuleNotFoundError: No module named 'fastapi'
```

Fix:
```bash
cd /opt/asl-agent
source venv/bin/activate
pip install -r requirements.txt
```

**4. Invalid YAML Syntax**

```
yaml.scanner.ScannerError: mapping values are not allowed here
```

Fix:
```bash
# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"
# If it shows an error, fix the line mentioned
nano config.yaml
```

**5. Permission Denied**

```
PermissionError: [Errno 13] Permission denied: '/opt/asl-agent/audit.log'
```

Fix:
```bash
sudo chown -R asl:asl /opt/asl-agent
sudo chmod 755 /opt/asl-agent
sudo chmod 644 /opt/asl-agent/*.py
sudo chmod 600 /opt/asl-agent/config.yaml
```

### Cannot Connect to AMI

#### Symptom
```
Failed to connect to AMI: [Errno 111] Connection refused
```

#### Diagnosis

**1. Check Asterisk is Running**

```bash
sudo asterisk -rx "core show version"
```

If you get an error, Asterisk isn't running:
```bash
sudo systemctl status asterisk
sudo systemctl start asterisk
```

**2. Check AMI is Enabled**

```bash
sudo grep "enabled = yes" /etc/asterisk/manager.conf
```

Should return: `enabled = yes`

If not:
```bash
sudo nano /etc/asterisk/manager.conf
# Find [general] section, ensure: enabled = yes
sudo asterisk -rx "manager reload"
```

**3. Verify AMI User Exists**

```bash
grep -A5 "^\[asl-agent\]" /etc/asterisk/manager.conf
```

Should show:
```ini
[asl-agent]
secret = YOUR_PASSWORD
read = system,call,reporting,command
write = command,reporting
deny = 0.0.0.0/0.0.0.0
permit = 127.0.0.1/255.255.255.255
```

If missing, add it and reload:
```bash
sudo asterisk -rx "manager reload"
```

**4. Check AMI Port**

```bash
sudo netstat -tlnp | grep 5038
```

Should show Asterisk listening on port 5038.

**5. Verify AMI Password Matches**

```bash
# Check what's in manager.conf
sudo grep "secret = " /etc/asterisk/manager.conf | grep asl-agent

# Check what's in config.yaml
grep "password:" /opt/asl-agent/config.yaml
```

They must match exactly.

### API Returns "Invalid API Key"

#### Symptom
```
401 Unauthorized: Invalid API key
```

#### Diagnosis

**1. Verify API Key Matches**

On Pi:
```bash
grep "api_key:" /opt/asl-agent/config.yaml
```

On Windows:
```powershell
Select-String -Path "$env:APPDATA\Roaming\npm\node_modules\clawdbot\skills\asl-control\scripts\asl-api.ps1" -Pattern "ASL_API_KEY"
```

They must match exactly (case-sensitive, no extra spaces).

**2. Check Header Format**

When using curl, the header must be:
```bash
-H "X-API-Key: YOUR_KEY"
```

Not:
- `-H "Authorization: Bearer YOUR_KEY"` ❌
- `-H "API-Key: YOUR_KEY"` ❌
- `-H "X-Api-Key: YOUR_KEY"` ❌ (wrong case)

### Connection Commands Don't Work

#### Symptom
```
✅ Connected to node 55553
```
But node doesn't actually connect. Or:
```
❌ Failed to connect to node 55553
```

#### Diagnosis

**1. Check the Other Node is Online**

```bash
# Look up the node
wget -qO- http://stats.allstarlink.org/nodeinfo.cgi?node=55553
```

If it returns nothing or shows offline, the node is down.

**2. Verify on AllScan First**

Before debugging the API, try connecting manually via AllScan web interface.

If AllScan can't connect either, the problem is:
- The remote node is offline
- Your node can't reach it (firewall/network issue)
- The remote node is rejecting connections

**3. Check Firewall Rules**

```bash
sudo ufw status
```

Make sure outbound connections are allowed:
```bash
sudo ufw allow out 4569/udp  # IAX2 port
```

**4. Test with Asterisk CLI**

```bash
sudo asterisk -rx "rpt cmd YOUR_NODE ilink 3 55553"
# Wait 10 seconds
sudo asterisk -rx "rpt lstats YOUR_NODE"
```

If this doesn't work, the problem is ASL/Asterisk configuration, not the API.

**5. Check AMI Permissions**

```bash
grep -A5 "^\[asl-agent\]" /etc/asterisk/manager.conf
```

Must have:
```ini
write = command,reporting
```

**6. Verify Wait Time**

The API waits 8 seconds for connection to establish. Very slow connections might need longer.

Edit `ami_client.py` line 93:
```python
await asyncio.sleep(8)  # Increase to 15 if needed
```

### PowerShell Functions Don't Work

#### Symptom
```powershell
Get-NodeStatus
# Returns: ❌ Failed to get node status
```

#### Diagnosis

**1. Check API is Reachable**

```powershell
# Test basic connectivity
Test-NetConnection -ComputerName YOUR_PI_IP -Port 8073
```

If it fails:
- Check Pi IP address is correct
- Check Pi firewall allows your PC
- Check network connectivity

**2. Check Script is Configured**

```powershell
Select-String -Path "$env:APPDATA\Roaming\npm\node_modules\clawdbot\skills\asl-control\scripts\asl-api.ps1" -Pattern "ASL_API_BASE"
```

Should show: `http://YOUR_PI_IP:8073` (no trailing slash)

**3. Test with Curl First**

```powershell
$headers = @{"X-API-Key"="YOUR_KEY"}
Invoke-RestMethod -Uri "http://YOUR_PI_IP:8073/" -Headers $headers
```

If this works but the functions don't, the problem is in the PowerShell script.

**4. Check for Detailed Errors**

```powershell
$ErrorActionPreference = "Continue"
Get-NodeStatus
# This will show the actual error instead of the friendly message
```

### Nodes Show Empty/None

#### Symptom
```
🔗 Connected Nodes: None
```
But you know nodes are connected.

#### Diagnosis

**1. Check Asterisk Status Directly**

```bash
sudo asterisk -rx "rpt nodes YOUR_NODE"
```

Example output:
```
T427060, T516596, T54199
```

If Asterisk shows nodes, the parsing is broken.

**2. Check Parser Logic**

The parser in `ami_client.py` expects format:
```
T123456, M789012, R345678
```

Where:
- T = Transceive
- M = Monitor
- R = Receive

If your Asterisk returns a different format, the parser needs updating.

**3. Enable Debug Logging**

Edit `/opt/asl-agent/config.yaml`:
```yaml
logging:
  level: "DEBUG"
```

Restart service and check logs:
```bash
sudo systemctl restart asl-agent
sudo journalctl -u asl-agent -f
```

### Telegram Bot Doesn't Respond

#### Symptom
Bot receives message but doesn't execute command.

#### Diagnosis

**Note:** Telegram integration is not yet verified in this project. PowerShell functions are confirmed working.

**1. Check Moltbot is Running**

On Windows:
```powershell
Get-Process | Where-Object {$_.Name -like "*clawdbot*"}
```

**2. Check Skill is Installed**

```powershell
Test-Path "$env:APPDATA\Roaming\npm\node_modules\clawdbot\skills\asl-control"
```

**3. Check Skill Configuration**

Verify `SKILL.md` is present and `asl-api.ps1` is configured.

**4. Check Moltbot Logs**

See Moltbot documentation for log location.

### Service Keeps Crashing

#### Symptom
```bash
sudo systemctl status asl-agent
# Shows: activating (auto-restart)
```

#### Diagnosis

**1. Check Recent Crashes**

```bash
sudo journalctl -u asl-agent -n 100 | grep -i error
```

**2. Common Crash Causes**

- AMI connection lost (Asterisk restarted)
- Config file changed while running
- Disk full (can't write audit log)
- Out of memory

**3. Check System Resources**

```bash
df -h  # Disk space
free -h  # Memory
top  # CPU usage
```

**4. Increase Restart Delay**

Edit `/etc/systemd/system/asl-agent.service`:
```ini
[Service]
RestartSec=30  # Wait 30 seconds before restart
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl restart asl-agent
```

## Performance Issues

### Slow Connection Times

#### Symptom
Connections take longer than 10 seconds.

#### Causes

1. **Network Latency** - Remote node is far away or on slow connection
2. **Node Overloaded** - Remote node is busy
3. **DNS Issues** - Node lookup is slow

#### Solutions

```bash
# Check network latency to node
ping $(dig +short NODE_NUMBER.allstarlink.org)

# Check DNS resolution time
time dig NODE_NUMBER.allstarlink.org
```

If DNS is slow, configure static node entries in `/etc/asterisk/rpt.conf`.

### High Memory Usage

#### Symptom
```bash
free -h
# Shows: high memory usage
```

#### Check API Memory

```bash
ps aux | grep asl_agent.py
```

If using more than 200MB, investigate:

```bash
sudo journalctl -u asl-agent | grep -i "memory\|oom"
```

### API Timeouts

#### Symptom
```
TimeoutError: Request timed out
```

#### Increase Timeouts

In PowerShell functions, increase timeout:
```powershell
Invoke-RestMethod -Uri $uri -Headers $headers -TimeoutSec 30
```

In API, increase AMI timeout:
```python
# ami_client.py
await asyncio.sleep(15)  # Increase from 8
```

## Diagnostic Commands

### Check Everything is Running

```bash
# Asterisk
sudo systemctl status asterisk

# ASL Agent API
sudo systemctl status asl-agent

# Firewall
sudo ufw status

# Network
hostname -I  # Shows Pi IP address
```

### Test API Endpoints

```bash
# Health check (no auth required)
curl http://localhost:8073/

# Status (requires auth)
curl -H "X-API-Key: YOUR_KEY" http://localhost:8073/status

# Connected nodes
curl -H "X-API-Key: YOUR_KEY" http://localhost:8073/nodes

# Audit log
curl -H "X-API-Key: YOUR_KEY" http://localhost:8073/audit?lines=10
```

### View Logs in Real-Time

```bash
# API service logs
sudo journalctl -u asl-agent -f

# Asterisk logs
sudo asterisk -rvvv

# Audit log
tail -f /opt/asl-agent/audit.log

# All system logs
sudo tail -f /var/log/syslog
```

### Verify Configuration

```bash
# Show config without secrets
grep -v "password\|secret\|api_key" /opt/asl-agent/config.yaml

# Validate YAML syntax
python3 -c "import yaml; print('Valid' if yaml.safe_load(open('/opt/asl-agent/config.yaml')) else 'Invalid')"

# Check file permissions
ls -la /opt/asl-agent/
```

## Getting Help

### Before Asking for Help

Gather this information:

```bash
# System info
uname -a
cat /etc/os-release

# ASL version
sudo asterisk -rx "core show version"

# API version
grep "version=" /opt/asl-agent/asl_agent.py

# Recent logs
sudo journalctl -u asl-agent -n 50 > /tmp/asl-agent-logs.txt

# Config (remove secrets!)
grep -v "password\|secret\|api_key" /opt/asl-agent/config.yaml > /tmp/config-sanitized.txt
```

### Where to Get Help

1. **GitHub Issues:** https://github.com/KJ5IRQ/openclaw-skill-asl3/issues
   - Search existing issues first
   - Include system info, logs, and what you tried

2. **GitHub Discussions:** https://github.com/KJ5IRQ/openclaw-skill-asl3/discussions
   - For questions and general help

3. **AllStar Link Community**
   - For ASL3-specific questions

### Include This in Bug Reports

```
**System:**
- Pi Model: (e.g., Raspberry Pi 4B)
- OS: (output of `cat /etc/os-release`)
- ASL Version: (output of `sudo asterisk -rx "core show version"`)
- Python Version: (output of `python3 --version`)

**Problem:**
(Describe what's not working)

**What I Tried:**
(List troubleshooting steps you've taken)

**Logs:**
(Paste relevant logs - remember to remove API keys!)

**Config:**
(Paste sanitized config.yaml)
```

## Advanced Troubleshooting

### Enable Debug Mode

```yaml
# config.yaml
logging:
  level: "DEBUG"
```

Restart and monitor:
```bash
sudo systemctl restart asl-agent
sudo journalctl -u asl-agent -f
```

### Trace AMI Commands

```bash
# In one terminal
sudo asterisk -rvvv

# In another terminal, trigger API command
curl -X POST -H "X-API-Key: YOUR_KEY" -H "Content-Type: application/json" \
  -d '{"node":"55553","monitor_only":false}' \
  http://localhost:8073/connect

# Watch Asterisk console for AMI activity
```

### Network Packet Capture

```bash
# Capture API traffic
sudo tcpdump -i any port 8073 -w /tmp/api-traffic.pcap

# Capture IAX2 traffic (node connections)
sudo tcpdump -i any port 4569 -w /tmp/iax2-traffic.pcap
```

Analyze with Wireshark on Windows.

### Manual AMI Testing

```bash
# Connect to AMI manually
telnet localhost 5038

# Login
Action: Login
Username: asl-agent
Secret: YOUR_AMI_PASSWORD

# Send command
Action: Command
Command: rpt cmd YOUR_NODE ilink 3 55553

# Logout
Action: Logoff
```

## Reset to Known Good State

If all else fails:

```bash
# Stop service
sudo systemctl stop asl-agent

# Backup current state
sudo cp -r /opt/asl-agent /opt/asl-agent.backup

# Remove virtual environment
rm -rf /opt/asl-agent/venv

# Recreate venv and reinstall
cd /opt/asl-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Verify config
nano config.yaml

# Restart service
sudo systemctl start asl-agent
sudo systemctl status asl-agent
```
