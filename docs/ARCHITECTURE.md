# System Architecture

## Overview

The ASL Control system consists of three main components that work together to provide remote control of your AllStar Link node.

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTROL LAYER                            │
│  ┌──────────────────┐              ┌──────────────────┐    │
│  │    Telegram      │              │   PowerShell     │    │
│  │   (Optional)     │              │   (Windows)      │    │
│  └────────┬─────────┘              └────────┬─────────┘    │
│           │                                  │              │
│           │         Natural Language         │              │
│           │         or Direct Commands       │              │
│           └──────────────┬───────────────────┘              │
└──────────────────────────┼──────────────────────────────────┘
                           │
                  ┌────────▼─────────┐
                  │   Moltbot Skill  │
                  │  (asl-api.ps1)   │
                  └────────┬─────────┘
                           │
                           │ HTTP/JSON (API Key Auth)
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  APPLICATION LAYER                          │
│              (Raspberry Pi - Port 8073)                     │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              FastAPI REST API                        │  │
│  │              (asl_agent.py)                          │  │
│  │                                                       │  │
│  │  Endpoints:                                          │  │
│  │  - GET  /status        (node stats)                 │  │
│  │  - GET  /nodes         (connected nodes)            │  │
│  │  - POST /connect       (connect to node)            │  │
│  │  - POST /disconnect    (disconnect from node)       │  │
│  │  - POST /disconnect-all (drop all connections)      │  │
│  │  - GET  /audit         (command history)            │  │
│  └───────────────────┬──────────────────────────────────┘  │
│                      │                                      │
│  ┌───────────────────▼──────────────────────────────────┐  │
│  │           AMI Client Wrapper                        │  │
│  │           (ami_client.py)                           │  │
│  │                                                      │  │
│  │  - Manages connection to Asterisk AMI               │  │
│  │  - Translates REST requests to AMI commands         │  │
│  │  - Parses AMI responses                             │  │
│  │  - Verifies connection state                        │  │
│  └───────────────────┬──────────────────────────────────┘  │
└──────────────────────┼─────────────────────────────────────┘
                       │
                       │ AMI Protocol (Port 5038, localhost)
                       │
┌──────────────────────▼─────────────────────────────────────┐
│                   ASTERISK LAYER                           │
│                (AllStar Link / ASL3)                       │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │         Asterisk Manager Interface (AMI)            │ │
│  │         - Localhost-only access (127.0.0.1)         │ │
│  │         - Username/password authentication          │ │
│  │         - Command execution permissions             │ │
│  └───────────────────┬──────────────────────────────────┘ │
│                      │                                     │
│  ┌───────────────────▼──────────────────────────────────┐ │
│  │              app_rpt (AllStar)                      │ │
│  │              - Node connection management           │ │
│  │              - Link control via ilink commands      │ │
│  │              - Connection state tracking            │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

## Data Flow

### Connection Request Flow

1. **User initiates request**
   - Via Telegram: "Connect to node 55553"
   - Via PowerShell: `Connect-Node -NodeNumber 55553`

2. **Moltbot processes request**
   - Parses natural language (Telegram) or direct command (PowerShell)
   - Calls PowerShell function `Connect-Node`
   - Constructs HTTP POST request with JSON body

3. **API receives request**
   - FastAPI validates API key
   - Extracts node number and connection mode
   - Calls `ami_client.connect_node()`

4. **AMI Client executes command**
   - Sends AMI command: `rpt cmd {local_node} ilink 3 {remote_node}`
   - Waits 8 seconds for connection to establish
   - Queries connected nodes to verify connection

5. **Response flows back**
   - AMI Client returns success/failure to API
   - API logs to audit trail
   - Returns JSON response to PowerShell
   - PowerShell formats response for user

6. **User sees result**
   - Telegram: "✅ Connected to node 55553 in transceive mode"
   - PowerShell: Same formatted message

## Component Details

### FastAPI Application (asl_agent.py)

**Responsibilities:**
- HTTP request handling
- API key authentication
- Request validation
- Audit logging
- Error handling
- Response formatting

**Lifecycle:**
- Startup: Connect to AMI, start event handler
- Runtime: Process API requests, maintain AMI connection
- Shutdown: Cleanup AMI connection, stop event handler

**Technology:**
- FastAPI (async web framework)
- Uvicorn (ASGI server)
- Pydantic (data validation)

### AMI Client (ami_client.py)

**Responsibilities:**
- AMI connection management
- Command translation (REST → AMI)
- Response parsing (AMI → structured data)
- Connection verification
- State validation

**Key Methods:**
- `connect_node()` - Uses `rpt cmd ... ilink 3 ...`
- `disconnect_node()` - Uses `rpt cmd ... ilink 1 ...`
- `disconnect_all()` - Uses `rpt cmd ... ilink 6`
- `get_connected_nodes()` - Parses `rpt nodes` output
- `get_node_stats()` - Parses `rpt stats` output

**Technology:**
- Panoramisk (async AMI library)
- asyncio (async operations)

### Event Handler (event_handler.py)

**Responsibilities:**
- Monitor node connection changes (when enabled)
- Send webhook notifications (when enabled)
- Track connection state

**Status:** Currently disabled (webhooks need batching implementation)

### Configuration (config.py)

**Responsibilities:**
- Load YAML configuration
- Provide typed configuration access
- Validate required settings

**Configuration Sources:**
- `/opt/asl-agent/config.yaml` on Pi

### PowerShell Functions (asl-api.ps1)

**Responsibilities:**
- Provide user-friendly interface
- HTTP request construction
- Response formatting
- Error handling

**Functions:**
- `Get-NodeStatus` → GET /status
- `Get-ConnectedNodes` → GET /nodes
- `Connect-Node` → POST /connect
- `Disconnect-Node` → POST /disconnect
- `Disconnect-AllNodes` → POST /disconnect-all
- `Get-AuditLog` → GET /audit

## Security Architecture

### Authentication Layer

**API Key:**
- 256-bit random key (generated via `openssl rand -base64 32`)
- Sent in `X-API-Key` header
- Validated on every request
- Failed attempts logged

### Network Security

**AMI Access:**
- Bound to localhost only (127.0.0.1)
- No external AMI access possible
- Separate AMI user with limited permissions

**API Access:**
- Binds to 0.0.0.0 (all interfaces) but should be firewalled
- Only allow specific IP ranges
- No TLS/HTTPS in base implementation (add reverse proxy for production)

### Permission Model

**AMI User Permissions:**
- Read: system, call, reporting, command
- Write: command, reporting
- No dialplan or configuration write access

**Command Audit:**
- All commands logged with timestamp
- User identification (currently always "api")
- Command details and parameters
- Stored in `/opt/asl-agent/audit.log`

## Performance Characteristics

### Connection Latency

**Connect Operation:**
- API request processing: <50ms
- AMI command execution: ~100ms
- Connection establishment: 8-10 seconds (network dependent)
- Verification: ~200ms
- Total: ~8-10 seconds

**Disconnect Operation:**
- API request processing: <50ms
- AMI command execution: ~100ms
- Disconnection processing: 3-5 seconds
- Verification: ~200ms
- Total: ~3-5 seconds

**Status Query:**
- API request processing: <50ms
- AMI command execution: ~100ms
- Parsing: <10ms
- Total: <200ms

### Scalability

**Current Limitations:**
- Single node per instance
- Synchronous connection operations
- No connection pooling

**Theoretical Limits:**
- API can handle 100+ requests/minute
- AMI can handle 10+ concurrent commands
- Bottleneck is ASL/Asterisk connection establishment

## Deployment Architecture

### Production Deployment

```
Internet
    │
    ├─── Reverse Proxy (Nginx/Caddy) ───┐
    │         - HTTPS/TLS                │
    │         - Rate limiting             │
    │         - IP restrictions           │
    │                                     │
    └─────────────────────────────────────┘
                    │
         ┌──────────▼──────────┐
         │   Raspberry Pi      │
         │                     │
         │  ┌──────────────┐  │
         │  │ ASL Agent    │  │
         │  │ (Port 8073)  │  │
         │  └──────┬───────┘  │
         │         │           │
         │  ┌──────▼───────┐  │
         │  │ Asterisk/AMI │  │
         │  │ (Port 5038)  │  │
         │  └──────────────┘  │
         └─────────────────────┘
```

### High Availability (Future)

For critical installations:
- Run multiple ASL nodes
- Single API instance per node
- External load balancer for API access
- Shared audit logging
- Monitoring and alerting

## Extension Points

### Adding New Commands

1. Add method to `AMIClient` class
2. Add endpoint to FastAPI app
3. Add PowerShell function
4. Update skill documentation

### Custom Webhooks

1. Enable webhooks in config.yaml
2. Implement batching in event_handler.py
3. Configure n8n or other webhook receiver
4. Add filtering logic

### Multi-Node Support

1. Modify config.py to support node array
2. Add node selection to API endpoints
3. Update PowerShell functions with node parameter
4. Handle multiple AMI connections

## Monitoring and Observability

### Logs

**System Logs:**
- Location: `journalctl -u asl-agent`
- Contains: startup, errors, warnings

**Audit Logs:**
- Location: `/opt/asl-agent/audit.log`
- Contains: all executed commands

**Asterisk Logs:**
- Location: `/var/log/asterisk/`
- Contains: AMI activity, connection events

### Health Checks

**API Health:**
- Endpoint: GET /
- Returns: service status, AMI connection state

**AMI Health:**
- Checked on each API request
- Automatic reconnection on failure

## Troubleshooting Guide

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed troubleshooting steps.

## Related Documentation

- [Installation Guide](INSTALLATION.md)
- [Beginner's Guide](BEGINNER_GUIDE.md)
- [Security Best Practices](SECURITY.md)
