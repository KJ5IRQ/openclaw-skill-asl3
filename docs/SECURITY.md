# Security Best Practices

## Overview

This document outlines security considerations and best practices for deploying the ASL Control system.

## Threat Model

### Assets to Protect

1. **Your AllStar Node** - Unauthorized control could disrupt communications
2. **API Access** - Prevents unauthorized commands
3. **AMI Access** - Prevents Asterisk compromise
4. **Credentials** - API keys, AMI passwords
5. **Audit Logs** - Evidence of who did what

### Potential Threats

1. **Unauthorized API Access** - Attackers controlling your node
2. **Credential Theft** - Stolen API keys or passwords
3. **Network Eavesdropping** - Intercepted communications
4. **Denial of Service** - API flooding
5. **Configuration Tampering** - Modified settings
6. **Log Deletion** - Covering tracks

## Defense Layers

### Layer 1: Network Security

#### Firewall Configuration

**Recommended: Restrict API Access by IP**

```bash
# Allow only from your home network
sudo ufw allow from 192.168.1.0/24 to any port 8073

# Or allow from specific IP
sudo ufw allow from YOUR_PC_IP to any port 8073

# Deny all other API access
sudo ufw deny 8073
```

**Production: Use VPN**

For remote access, use a VPN instead of exposing the API to the internet:

```bash
# Only allow VPN subnet
sudo ufw allow from 10.8.0.0/24 to any port 8073

# Block direct internet access
sudo ufw deny 8073
```

#### AMI Protection

**AMI is localhost-only by design:**

```ini
# In /etc/asterisk/manager.conf
[asl-agent]
deny = 0.0.0.0/0.0.0.0      # Deny all
permit = 127.0.0.1/255.255.255.255  # Allow only localhost
```

**Never change this to allow external AMI access.**

### Layer 2: Authentication

#### API Key Management

**Generation:**

```bash
# Generate strong 256-bit key
openssl rand -base64 32
```

**Storage:**

- **Pi:** `/opt/asl-agent/config.yaml` (readable only by asl user)
- **Windows:** Embedded in asl-api.ps1 (user's profile)
- **Never** commit to git
- **Never** send via unencrypted channels

**Rotation:**

Rotate API keys every 90 days or immediately if compromised:

```bash
# Generate new key
NEW_KEY=$(openssl rand -base64 32)

# Update Pi config
nano /opt/asl-agent/config.yaml
# Update api_key value

# Restart service
sudo systemctl restart asl-agent

# Update Windows config
notepad "$env:APPDATA\Roaming\npm\node_modules\clawdbot\skills\asl-control\scripts\asl-api.ps1"
# Update $ASL_API_KEY value
```

#### AMI Credentials

**Password Strength:**

```bash
# Generate strong AMI password
openssl rand -base64 16
```

**Storage:**

- `/etc/asterisk/manager.conf` (root readable only)
- `/opt/asl-agent/config.yaml` (asl user readable only)

**Permissions in manager.conf:**

```ini
[asl-agent]
secret = STRONG_PASSWORD_HERE
read = system,call,reporting,command    # Read-only where possible
write = command,reporting               # Write only what's needed
# NO write to: system, config, dialplan
```

### Layer 3: Transport Security

#### HTTPS/TLS (Production Recommended)

**Current State:** API uses HTTP (unencrypted)

**Risk:** API keys and commands sent in clear text on the network

**Mitigation:**

Use a reverse proxy with TLS:

**Option A: Nginx**

```nginx
server {
    listen 443 ssl;
    server_name your-node.example.com;

    ssl_certificate /etc/letsencrypt/live/your-node.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-node.example.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8073;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

**Option B: Caddy (Easier)**

```
your-node.example.com {
    reverse_proxy localhost:8073
}
```

Caddy automatically handles SSL certificates via Let's Encrypt.

#### VPN (Recommended for Remote Access)

Instead of exposing the API to the internet, use a VPN:

**Popular Options:**
- WireGuard (modern, fast)
- OpenVPN (widely supported)
- Tailscale (zero-config mesh VPN)

**Benefits:**
- Encrypted tunnel
- No port forwarding needed
- Works from anywhere
- Can access other services too

### Layer 4: Application Security

#### Rate Limiting

**Current Implementation:** Basic (10 requests/minute in config)

**Recommended Enhancement:**

Add rate limiting per IP at the reverse proxy level:

**Nginx:**
```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/m;

location / {
    limit_req zone=api burst=5;
    proxy_pass http://localhost:8073;
}
```

#### Input Validation

**Current:** Node numbers validated by API

**Risks:**
- Malformed node numbers
- SQL injection (N/A - no database)
- Command injection (mitigated by AMI library)

**Validation in place:**
- Node numbers: numeric only
- API endpoints: specific allowed operations
- AMI commands: pre-defined templates

#### Audit Logging

**What's Logged:**
- Timestamp (UTC)
- User (currently always "api")
- Command executed
- Parameters

**Location:** `/opt/asl-agent/audit.log`

**Best Practices:**

```bash
# Review logs regularly
tail -f /opt/asl-agent/audit.log

# Look for suspicious patterns
grep "connect" /opt/asl-agent/audit.log | grep -v "YOUR_KNOWN_NODES"

# Archive old logs
sudo logrotate /opt/asl-agent/audit.log
```

**Log Retention:**

Create `/etc/logrotate.d/asl-agent`:

```
/opt/asl-agent/audit.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
    create 0640 asl asl
}
```

### Layer 5: System Hardening

#### Service Permissions

**Systemd Security:**

The service file includes:

```ini
[Service]
User=asl
Group=asl
NoNewPrivileges=true    # Can't escalate privileges
PrivateTmp=true         # Isolated /tmp
ProtectSystem=strict    # Read-only system
ProtectHome=true        # No access to user homes
ReadWritePaths=/opt/asl-agent  # Only needed directory writable
ReadOnlyPaths=/etc/asterisk    # Can read but not write Asterisk config
```

#### File Permissions

**Recommended Permissions:**

```bash
# Config file (contains secrets)
sudo chmod 600 /opt/asl-agent/config.yaml
sudo chown asl:asl /opt/asl-agent/config.yaml

# Python files (readable by all, writable by owner)
sudo chmod 644 /opt/asl-agent/*.py
sudo chown asl:asl /opt/asl-agent/*.py

# Audit log (writable only by service)
sudo chmod 640 /opt/asl-agent/audit.log
sudo chown asl:asl /opt/asl-agent/audit.log
```

#### System Updates

**Keep everything updated:**

```bash
# Update Raspberry Pi OS
sudo apt update && sudo apt upgrade -y

# Update Python packages (in venv)
cd /opt/asl-agent
source venv/bin/activate
pip install --upgrade fastapi uvicorn pyyaml panoramisk aiohttp

# Update ASL3
sudo apt update && sudo apt upgrade asl3
```

**Monitor for security advisories:**
- Raspberry Pi security updates
- Python CVEs
- Asterisk security bulletins
- ASL3 announcements

## Incident Response

### If API Key is Compromised

1. **Immediately rotate the key:**
```bash
NEW_KEY=$(openssl rand -base64 32)
nano /opt/asl-agent/config.yaml  # Update api_key
sudo systemctl restart asl-agent
```

2. **Check audit logs:**
```bash
# Look for unauthorized activity
tail -100 /opt/asl-agent/audit.log | grep -v "YOUR_IP"
```

3. **Update all clients:**
- Update PowerShell script with new key
- Update Moltbot configuration

4. **Review firewall rules:**
```bash
sudo ufw status
```

### If Unauthorized Commands Detected

1. **Stop the service immediately:**
```bash
sudo systemctl stop asl-agent
```

2. **Review audit log:**
```bash
cat /opt/asl-agent/audit.log
```

3. **Check system logs:**
```bash
sudo journalctl -u asl-agent -n 200
```

4. **Investigate Asterisk logs:**
```bash
sudo grep "AMI" /var/log/asterisk/messages
```

5. **After investigation:**
- Rotate all credentials
- Update firewall rules
- Consider adding 2FA or VPN requirement

### If System is Compromised

1. **Isolate the Pi:**
```bash
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default deny outgoing
```

2. **Preserve evidence:**
```bash
# Copy audit log
cp /opt/asl-agent/audit.log /tmp/audit-$(date +%Y%m%d).log

# Copy system logs
sudo journalctl > /tmp/journal-$(date +%Y%m%d).log
```

3. **Restore from backup or rebuild**

4. **Change all credentials**

## Security Checklist

### Initial Setup
- [ ] Generate strong API key (32+ random bytes)
- [ ] Generate strong AMI password (16+ random bytes)
- [ ] Set file permissions correctly
- [ ] Configure firewall to restrict API access
- [ ] Verify AMI is localhost-only
- [ ] Test authentication works
- [ ] Review audit log format

### Regular Maintenance (Monthly)
- [ ] Review audit logs for anomalies
- [ ] Check for system updates
- [ ] Verify firewall rules
- [ ] Test backup/restore procedure

### Quarterly
- [ ] Rotate API key
- [ ] Rotate AMI password
- [ ] Review security advisories
- [ ] Update documentation

### After Incidents
- [ ] Rotate all credentials immediately
- [ ] Review and preserve logs
- [ ] Update firewall rules
- [ ] Document lessons learned

## Additional Resources

### Recommended Reading

- [OWASP REST Security Cheat Sheet](https://cheatsheetsecurity.org/cheatsheets/rest-security/)
- [Asterisk Security Best Practices](https://www.asterisk.org/community/security/)
- [Raspberry Pi Security](https://www.raspberrypi.com/documentation/computers/configuration.html#securing-your-raspberry-pi)

### Security Tools

**Log Analysis:**
- `fail2ban` - Auto-ban suspicious IPs
- `logwatch` - Daily log summaries

**Intrusion Detection:**
- `aide` - File integrity monitoring
- `rkhunter` - Rootkit detection

**Network Security:**
- `ufw` - Uncomplicated firewall
- `iptables` - Advanced firewall
- WireGuard/OpenVPN - VPN

## Reporting Security Issues

If you discover a security vulnerability:

1. **Do NOT** open a public GitHub issue
2. Email: security@your-domain.com (or create private security advisory)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Disclaimer

**This software is provided as-is with no warranty.** You are responsible for:
- Securing your deployment
- Protecting your credentials
- Monitoring for unauthorized access
- Maintaining backups
- Complying with local regulations

**Amateur radio operators:** Follow all applicable FCC/regulations for your jurisdiction when using remote control capabilities.
