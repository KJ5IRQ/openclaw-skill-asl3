"""ASL Agent - REST API for AllStar Link node control."""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from config import config
from ami_client import ami_client
from event_handler import EventHandler

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize event handler
event_handler = EventHandler(ami_client)
monitoring_task: Optional[asyncio.Task] = None


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    global monitoring_task
    
    # Startup
    logger.info("Starting ASL Agent...")
    try:
        await ami_client.connect()
        await event_handler.start()
        
        # Start monitoring loop (disabled if webhooks disabled)
        if config.webhooks_enabled:
            monitoring_task = asyncio.create_task(event_handler.monitoring_loop())
        
        logger.info(f"ASL Agent started for node {config.node_number} ({config.node_callsign})")
        yield
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down ASL Agent...")
        if monitoring_task:
            monitoring_task.cancel()
            try:
                await monitoring_task
            except asyncio.CancelledError:
                pass
        
        await event_handler.stop()
        await ami_client.disconnect()
        logger.info("ASL Agent stopped")


# Create FastAPI app
app = FastAPI(
    title="ASL Agent",
    description="REST API for AllStar Link node control",
    version="1.0.0",
    lifespan=lifespan
)


# Security: API Key validation
async def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key from request header."""
    if x_api_key != config.api_key:
        logger.warning("Invalid API key attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return x_api_key


# Audit logging
def audit_log(command: str, user: str = "api", details: str = ""):
    """Log command execution to audit file."""
    timestamp = datetime.utcnow().isoformat()
    log_entry = f"{timestamp} | {user} | {command} | {details}\n"
    
    try:
        with open(config.audit_file, 'a') as f:
            f.write(log_entry)
    except Exception as e:
        logger.error(f"Audit log failed: {e}")


# Pydantic models
class ConnectRequest(BaseModel):
    node: str = Field(..., description="Node number to connect to")
    monitor_only: bool = Field(False, description="Connect in monitor mode (receive only)")

class DisconnectRequest(BaseModel):
    node: str = Field(..., description="Node number to disconnect")


# API Routes

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "ASL Agent",
        "node": config.node_number,
        "callsign": config.node_callsign,
        "status": "running",
        "ami_connected": ami_client.connected
    }


@app.get("/status", dependencies=[Depends(verify_api_key)])
async def get_status():
    """Get node status and statistics."""
    try:
        stats = await ami_client.get_node_stats()
        audit_log("status", details="Status retrieved")
        return stats
    except Exception as e:
        logger.error(f"Status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/nodes", dependencies=[Depends(verify_api_key)])
async def get_nodes():
    """Get list of connected nodes."""
    try:
        nodes = await ami_client.get_connected_nodes()
        audit_log("nodes", details=f"{len(nodes)} nodes connected")
        return {"connected_nodes": nodes, "count": len(nodes)}
    except Exception as e:
        logger.error(f"Nodes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/connect", dependencies=[Depends(verify_api_key)])
async def connect_node(request: ConnectRequest):
    """Connect to another AllStar node."""
    try:
        mode = "monitor" if request.monitor_only else "transceive"
        result = await ami_client.connect_node(request.node, request.monitor_only)
        audit_log("connect", details=f"Node {request.node} ({mode})")
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return {
            "success": True,
            "message": f"Connected to node {request.node} in {mode} mode",
            "node": request.node,
            "mode": mode
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Connect error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/disconnect", dependencies=[Depends(verify_api_key)])
async def disconnect_node(request: DisconnectRequest):
    """Disconnect from a specific node."""
    try:
        result = await ami_client.disconnect_node(request.node)
        audit_log("disconnect", details=f"Node {request.node}")
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return {
            "success": True,
            "message": f"Disconnected from node {request.node}",
            "node": request.node
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Disconnect error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/disconnect-all", dependencies=[Depends(verify_api_key)])
async def disconnect_all():
    """Disconnect from all nodes."""
    try:
        result = await ami_client.disconnect_all()
        audit_log("disconnect-all", details="All nodes disconnected")
        
        return {
            "success": True,
            "message": "Disconnected from all nodes"
        }
    except Exception as e:
        logger.error(f"Disconnect all error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/audit", dependencies=[Depends(verify_api_key)])
async def get_audit_log(lines: int = 50):
    """Get recent audit log entries."""
    try:
        with open(config.audit_file, 'r') as f:
            all_lines = f.readlines()
            recent = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return {
            "entries": [line.strip() for line in recent],
            "count": len(recent)
        }
    except FileNotFoundError:
        return {"entries": [], "count": 0}
    except Exception as e:
        logger.error(f"Audit log error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config.api_host,
        port=config.api_port,
        log_level=config.log_level.lower()
    )
