"""AMI event handler for monitoring node connections."""
import asyncio
import logging
import aiohttp
from datetime import datetime
from typing import Dict, Optional
from config import config

logger = logging.getLogger(__name__)


class EventHandler:
    """Handle AMI events and send webhooks to n8n."""
    
    def __init__(self, ami_client):
        self.ami_client = ami_client
        self.session: Optional[aiohttp.ClientSession] = None
        self.connected_nodes = set()
    
    async def start(self):
        """Start event monitoring."""
        if config.webhooks_enabled:
            self.session = aiohttp.ClientSession()
            logger.info("Event handler started with webhooks enabled")
        else:
            logger.info("Event handler started (webhooks disabled)")
    
    async def stop(self):
        """Stop event monitoring and cleanup."""
        if self.session:
            await self.session.close()
        logger.info("Event handler stopped")
    
    async def send_webhook(self, event_type: str, data: Dict):
        """Send webhook notification to n8n."""
        if not config.webhooks_enabled or not self.session:
            return
        
        payload = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "node": config.node_number,
            "callsign": config.node_callsign,
            "data": data
        }
        
        try:
            async with self.session.post(
                config.n8n_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    logger.info(f"Webhook sent: {event_type}")
                else:
                    logger.warning(f"Webhook failed: {response.status}")
        except Exception as e:
            logger.error(f"Webhook error: {e}")
    
    async def on_node_connect(self, node_number: str, info: str = ""):
        """Handle node connection event."""
        if node_number not in self.connected_nodes:
            self.connected_nodes.add(node_number)
            logger.info(f"Node connected: {node_number}")
            
            await self.send_webhook("node_connected", {
                "connected_node": node_number,
                "info": info
            })
    
    async def on_node_disconnect(self, node_number: str):
        """Handle node disconnection event."""
        if node_number in self.connected_nodes:
            self.connected_nodes.remove(node_number)
            logger.info(f"Node disconnected: {node_number}")
            
            await self.send_webhook("node_disconnected", {
                "disconnected_node": node_number
            })
    
    async def check_node_changes(self):
        """Poll for node connection changes."""
        try:
            current_nodes = await self.ami_client.get_connected_nodes()
            current_set = {node['node'] for node in current_nodes}
            
            # Detect new connections
            for node in current_set - self.connected_nodes:
                node_info = next((n['info'] for n in current_nodes if n['node'] == node), "")
                await self.on_node_connect(node, node_info)
            
            # Detect disconnections
            for node in self.connected_nodes - current_set:
                await self.on_node_disconnect(node)
            
        except Exception as e:
            logger.error(f"Error checking node changes: {e}")
    
    async def monitoring_loop(self):
        """Background task to monitor node changes."""
        logger.info("Starting node monitoring loop")
        
        while True:
            try:
                await self.check_node_changes()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                logger.info("Monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(30)
