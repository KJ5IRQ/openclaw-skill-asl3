# Complete Beginner's Guide to ASL Control

**New to programming, Linux, or Raspberry Pi?** This guide explains everything step-by-step, assuming no prior knowledge.

## What You're Building

You're setting up a system that lets you control your AllStar Link amateur radio node by:
- Typing messages to a Telegram bot on your phone
- Running commands in PowerShell on your Windows computer

Think of it like a remote control for your node that works from anywhere.

## What You Need

### Hardware
- **Raspberry Pi with ASL3** - Your AllStar Link node (already running)
- **Windows PC** - Where you'll send commands from
- **Internet connection** - Both devices need internet

### Software Already Installed
- Your Pi should have ASL3 already working
- Your Windows PC should have PowerShell (it comes with Windows)

### What You'll Install
- **On the Pi**: Python programs that let your node accept remote commands
- **On Windows**: Moltbot/Clawdbot (a chatbot framework) and this skill

## Understanding the System

```
Your Phone (Telegram)
        ↓
  "Connect to node 55553"
        ↓
Your Windows PC (Moltbot)
        ↓
    Translates to commands
        ↓
Your Raspberry Pi (API)
        ↓
    Talks to Asterisk
        ↓
Your Node Connects!
```

**In plain English:**
1. You send a message to your Telegram bot
2. The bot (running on Windows) figures out what you want
3. It sends a command to your Raspberry Pi
4. Your Pi tells Asterisk what to do
5. Your node connects/disconnects/etc.

## Part 1: Download the Code from GitHub

### What is GitHub?
GitHub is a website where programmers share code. Think of it like Google Drive for code.

### Step 1: Get the Code

**Method A: Using Git (Recommended)**

1. **On Windows**, open PowerShell (search for "PowerShell" in Start menu)
2. **Type these commands** (press Enter after each):

```powershell
# Go to your Documents folder
cd C:\Users\$env:USERNAME\Documents

# Download the code
git clone https://github.com/KJ5IRQ/openclaw-skill-asl3.git

# Go into the folder
cd openclaw-skill-asl3
```

**If you get "git is not recognized":**
- Install Git from: https://git-scm.com/download/win
- Use all default options during install
- Close and reopen PowerShell, then try again

**Method B: Download as ZIP (Easier but Less Flexible)**

1. Go to: https://github.com/KJ5IRQ/openclaw-skill-asl3
2. Click the green "Code" button
3. Click "Download ZIP"
4. Extract the ZIP to `C:\Users\YourName\Documents\openclaw-skill-asl3`

### ✅ Checkpoint: You Should Now Have
A folder at `C:\Users\YourName\Documents\openclaw-skill-asl3` with files inside like `README.md`, `LICENSE`, and folders named `backend`, `skill`, `docs`.

## Part 2: Set Up the Raspberry Pi (Backend)

### What is SSH?
SSH is a way to control your Raspberry Pi from your Windows computer by typing commands. Think of it like remote desktop, but using text instead of graphics.

### Step 1: Connect to Your Pi

1. **Find your Pi's IP address**
   - On your Pi, type: `hostname -I`
   - Or check your router's device list
   - It looks like: `192.168.1.88`

2. **On Windows**, open PowerShell and type:
```powershell
ssh asl@192.168.1.88
```
Replace `192.168.1.88` with YOUR Pi's IP address.

3. **Type your Pi's password** when prompted (you won't see it as you type - this is normal)

**If SSH doesn't work:**
- Make sure SSH is enabled on your Pi
- Try: `ssh -l asl 192.168.1.88`
- Check you're using the right IP address

### ✅ Checkpoint: You Should See
A command prompt that looks like: `asl@raspberrypi:~ $`

This means you're now controlling your Pi from Windows!

### Step 2: Install Python Tools

**What is this doing?** Setting up the programming environment needed to run the API.

Type these commands one at a time (press Enter after each):

```bash
# Update the Pi's software list
sudo apt update

# Install Python tools
sudo apt install python3-pip python3-venv -y
```

**What does this mean?**
- `sudo` = "Run this as administrator"
- `apt` = The Pi's software installer
- `update` = Check for new software versions
- `install` = Download and install software
- `-y` = Answer "yes" to all questions automatically

**This takes 2-5 minutes.** You'll see lots of text scroll by - that's normal.

### ✅ Checkpoint: When Done
You're back at the `asl@raspberrypi:~ $` prompt with no errors.

### Step 3: Create the Installation Folder

**What is this doing?** Creating a special folder to hold all the program files.

```bash
# Create the folder
sudo mkdir -p /opt/asl-agent

# Give yourself permission to use it
sudo chown $USER:$USER /opt/asl-agent

# Go into the folder
cd /opt/asl-agent
```

**What does this mean?**
- `/opt/asl-agent` = A folder path (like `C:\Program Files` on Windows)
- `mkdir` = Make directory (create folder)
- `-p` = Create parent folders if needed
- `chown` = Change owner (give yourself permission)

### ✅ Checkpoint: Your Prompt Should Show
`asl@raspberrypi:/opt/asl-agent $`

This means you're now in the `/opt/asl-agent` folder.

### Step 4: Set Up Python Virtual Environment

**What is a virtual environment?** Think of it like a separate, clean workspace for this project's Python tools - it keeps things organized and prevents conflicts.

```bash
# Create the virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate
```

### ✅ Checkpoint: Your Prompt Should Now Show
`(venv) asl@raspberrypi:/opt/asl-agent $`

The `(venv)` means you're in the virtual environment.

### Step 5: Install Python Packages

**What is this doing?** Installing the specific tools (libraries) the API needs to work.

```bash
pip install fastapi==0.109.0 uvicorn[standard]==0.27.0 pyyaml==6.0.1 python-multipart==0.0.6 panoramisk==1.4 aiohttp==3.9.1
```

**This takes 3-10 minutes.** You'll see "Collecting...", "Downloading...", "Installing..." - all normal.

### ✅ Checkpoint: When Done
You see "Successfully installed..." messages and you're back at the `(venv)` prompt.

### Step 6: Copy the Program Files

**What is this doing?** Getting the actual code onto your Pi.

```bash
# Download the code
git clone https://github.com/KJ5IRQ/openclaw-skill-asl3.git temp

# Copy the backend files
cp temp/backend/*.py .
cp temp/backend/requirements.txt .
cp temp/backend/asl-agent.service .
cp temp/backend/config.yaml.example config.yaml

# Remove the temporary folder
rm -rf temp
```

**If git isn't installed:**
```bash
sudo apt install git -y
```
Then try the commands above again.

### ✅ Checkpoint: List Your Files
Type: `ls -la`

You should see files like:
- `asl_agent.py`
- `ami_client.py`
- `config.py`
- `event_handler.py`
- `config.yaml`
- `requirements.txt`
- `asl-agent.service`

### Step 7: Configure AMI Access

**What is AMI?** Asterisk Manager Interface - it's how programs talk to Asterisk (the software running your node).

**Create a password for AMI:**

```bash
# Generate a random password
openssl rand -base64 16
```

**Copy the password it shows you** - you'll need it in a minute.

**Edit the AMI configuration:**

```bash
sudo nano /etc/asterisk/manager.conf
```

**What is nano?** A simple text editor (like Notepad on Windows).

**Scroll to the bottom** using arrow keys, then add this section:

```ini
[asl-agent]
secret = PASTE_YOUR_PASSWORD_HERE
read = system,call,reporting,command
write = command,reporting
deny = 0.0.0.0/0.0.0.0
permit = 127.0.0.1/255.255.255.255
```

**Replace `PASTE_YOUR_PASSWORD_HERE` with the password from earlier.**

**Save and exit:**
- Press `Ctrl+X`
- Press `Y` (to save)
- Press `Enter` (to confirm)

**Tell Asterisk to reload:**
```bash
sudo asterisk -rx "manager reload"
```

### ✅ Checkpoint: You Should See
`Reloading manager configuration`

### Step 8: Create Your Configuration File

**What is this doing?** Setting up YOUR specific node number, password, and settings.

```bash
# Make sure you're in the right folder
cd /opt/asl-agent

# Edit the config file
nano config.yaml
```

**You'll see a file that looks like this.** Change the parts in CAPS:

```yaml
ami:
  host: "127.0.0.1"
  port: 5038
  username: "asl-agent"
  password: "YOUR_AMI_PASSWORD_FROM_STEP_7"

node:
  number: "YOUR_NODE_NUMBER"      # Example: "2560"
  callsign: "YOUR_CALLSIGN"       # Example: "W5XYZ"

api:
  host: "0.0.0.0"
  port: 8073
  api_key: "GENERATE_THIS_NEXT"   # Generate with: openssl rand -base64 32

webhooks:
  enabled: false

logging:
  level: "INFO"
  audit_file: "/opt/asl-agent/audit.log"

security:
  rate_limit_per_minute: 10
  require_confirmation: ["disconnectall"]
```

**To generate the API key:**
1. Press `Ctrl+X` to exit nano (don't save yet)
2. Type: `openssl rand -base64 32`
3. Copy that password
4. Type: `nano config.yaml`
5. Paste it where it says `GENERATE_THIS_NEXT`

**Fill in:**
- Your AMI password (from Step 7)
- Your node number (like "2560")
- Your callsign (like "W5XYZ")
- The API key you just generated

**Save:**
- Press `Ctrl+X`
- Press `Y`
- Press `Enter`

### ✅ Checkpoint: Check Your Config
```bash
cat config.yaml
```

You should see YOUR node number, callsign, and real passwords (not the examples).

### Step 9: Test the API

**Let's see if it works!**

```bash
# Make sure you're in the virtual environment
cd /opt/asl-agent
source venv/bin/activate

# Run the program
python3 asl_agent.py
```

**You should see:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Connected to AMI at 127.0.0.1:5038
INFO:     ASL Agent started for node YOUR_NODE
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8073
```

**If you see this - SUCCESS!** The API is running.

**Leave it running** and open a NEW PowerShell window on Windows.

### Step 10: Test from Windows

In the **NEW** PowerShell window:

```powershell
# Test the API (replace IP and API_KEY with yours)
Invoke-RestMethod -Uri "http://192.168.1.88:8073/" -Headers @{"X-API-Key"="YOUR_API_KEY"}
```

**You should get a response like:**
```
service      : ASL Agent
node         : YOUR_NODE
callsign     : YOUR_CALLSIGN
status       : running
ami_connected: True
```

**If you see this - VICTORY!** Your Pi can now accept commands.

**Go back to the Pi terminal** and press `Ctrl+C` to stop the test.

### Step 11: Install as a Service

**What is a service?** A program that runs automatically when your Pi starts up.

```bash
# Copy the service file
sudo cp /opt/asl-agent/asl-agent.service /etc/systemd/system/

# Tell systemd about it
sudo systemctl daemon-reload

# Make it start automatically
sudo systemctl enable asl-agent

# Start it now
sudo systemctl start asl-agent
```

**Check if it's running:**
```bash
sudo systemctl status asl-agent
```

**You should see:**
```
Active: active (running)
```

Press `Q` to exit the status view.

### ✅ Checkpoint: Your Pi Setup is DONE!
The API is now running on your Pi and will start automatically whenever you reboot.

## Part 3: Set Up Windows (Frontend)

### Step 1: Install Moltbot/Clawdbot

**What is Moltbot?** A framework that lets you create chatbots that can run PowerShell commands.

1. **Install Node.js** (required for Moltbot)
   - Go to: https://nodejs.org/
   - Download the LTS version
   - Install with all default options
   - Restart your computer

2. **Install Moltbot**

Open PowerShell as Administrator (Right-click → "Run as Administrator"):

```powershell
npm install -g clawdbot
```

**This takes 5-10 minutes.**

### ✅ Checkpoint: Test Installation
```powershell
clawdbot --version
```

You should see a version number like `1.x.x`.

### Step 2: Install the ASL Control Skill

```powershell
# Go to the skills folder
cd "$env:APPDATA\Roaming\npm\node_modules\clawdbot\skills"

# Copy the skill
# (Assuming you already downloaded the repo to Documents)
Copy-Item -Recurse "C:\Users\$env:USERNAME\Documents\openclaw-skill-asl3\skill" "asl-control"
```

### Step 3: Configure the PowerShell Script

```powershell
# Edit the config
notepad "$env:APPDATA\Roaming\npm\node_modules\clawdbot\skills\asl-control\scripts\asl-api.ps1"
```

**Change the first two lines:**

```powershell
$ASL_API_BASE = "http://YOUR_PI_IP:8073"        # Example: "http://192.168.1.88:8073"
$ASL_API_KEY = "YOUR_API_KEY_FROM_STEP_8"       # The key from config.yaml
```

**Save and close Notepad.**

### Step 4: Test PowerShell Functions

```powershell
# Load the functions
. "$env:APPDATA\Roaming\npm\node_modules\clawdbot\skills\asl-control\scripts\asl-api.ps1"

# Test it
Get-NodeStatus
```

**You should see:**
```
🔘 Node YOUR_NODE (YOUR_CALLSIGN) Status

⏱️ Uptime: XX hours
🔢 Keyups Today: XX
🔗 Connected Nodes: X
```

### ✅ Checkpoint: Windows Setup is DONE!

## Part 4: Using the System

### Via PowerShell (Windows)

**Every time you want to use it:**

```powershell
# Load the functions
. "$env:APPDATA\Roaming\npm\node_modules\clawdbot\skills\asl-control\scripts\asl-api.ps1"

# Check status
Get-NodeStatus

# See who's connected
Get-ConnectedNodes

# Connect to a node
Connect-Node -NodeNumber 55553

# Disconnect
Disconnect-Node -NodeNumber 55553
```

### Via Telegram (Optional)

Follow Moltbot's documentation to connect it to Telegram. Once connected, you can text your bot:
- "Check my node status"
- "Connect to node 55553"
- "Who's connected?"
- "Disconnect from everything"

## Troubleshooting

### "Connection refused" error
**Problem:** Can't reach the Pi
**Fix:** 
- Check Pi IP address: `hostname -I` on the Pi
- Ping the Pi: `ping 192.168.1.88` from Windows
- Check firewall settings on both devices

### "Invalid API key" error
**Problem:** Wrong API key
**Fix:**
- Check `config.yaml` on Pi: `cat /opt/asl-agent/config.yaml`
- Check `asl-api.ps1` on Windows - make sure they match exactly

### "AMI not connected" error
**Problem:** Can't talk to Asterisk
**Fix:**
- Check Asterisk is running: `sudo asterisk -rx "core show version"`
- Check AMI password in `/etc/asterisk/manager.conf`
- Reload manager: `sudo asterisk -rx "manager reload"`
- Restart the service: `sudo systemctl restart asl-agent`

### Node won't connect
**Problem:** Connection command doesn't work
**Fix:**
- Check the other node is actually online
- Try connecting via AllScan web interface first to verify
- Check audit log: `tail /opt/asl-agent/audit.log`

### How to view logs
```bash
# On the Pi, view the last 50 log entries
sudo journalctl -u asl-agent -n 50

# Watch logs in real-time
sudo journalctl -u asl-agent -f
```

## Glossary of Terms

- **API** - Application Programming Interface: A way for programs to talk to each other
- **AMI** - Asterisk Manager Interface: How programs control Asterisk
- **Asterisk** - The phone system software your AllStar node runs on
- **Backend** - The program running on your Pi that controls your node
- **Frontend** - The program running on Windows that you interact with
- **Git** - A tool for downloading and managing code
- **GitHub** - A website where code is shared
- **Node** - Your AllStar Link radio repeater/hotspot
- **PowerShell** - A command-line interface on Windows
- **Python** - The programming language the API is written in
- **REST API** - A standard way for programs to communicate over the internet
- **SSH** - Secure Shell: A way to remotely control Linux computers
- **Systemd** - The system that manages background programs on Linux
- **Virtual Environment** - An isolated Python workspace for one project

## Next Steps

- Read the main [INSTALLATION.md](INSTALLATION.md) for advanced configuration
- Check out [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more help
- Join the GitHub Discussions to ask questions

## Need Help?

1. Check the [Troubleshooting](#troubleshooting) section above
2. Look at existing GitHub Issues: https://github.com/KJ5IRQ/openclaw-skill-asl3/issues
3. Create a new issue with:
   - What you were trying to do
   - What happened instead
   - Any error messages you saw
   - Your Pi model and ASL version
