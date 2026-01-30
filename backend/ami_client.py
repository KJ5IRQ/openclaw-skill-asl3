"""Asterisk Manager Interface client wrapper."""
import asyncio
import logging
from typing import Dict, List, Optional
from panoramisk import Manager
from config import config

logger = logging.getLogger(__name__)


class AMIClient:
    """Wrapper for AMI connections using panoramisk."""

    def __init__(self):
        self.manager: Optional[Manager] = None
        self.connected = False

    async def connect(self):
        """Establish connection to AMI."""
        try:
            self.manager = Manager(
                host=config.ami_host,
                port=config.ami_port,
                username=config.ami_username,
                secret=config.ami_password,
                ping_delay=60,
                ping_attempts=3
            )

            await self.manager.connect()
            self.connected = True
            logger.info(f"Connected to AMI at {config.ami_host}:{config.ami_port}")

        except Exception as e:
            self.connected = False
            logger.error(f"Failed to connect to AMI: {e}")
            raise

    async def disconnect(self):
        """Close AMI connection."""
        if self.manager:
            await self.manager.close()
            self.connected = False
            logger.info("Disconnected from AMI")

    async def send_command(self, command: str) -> Dict:
        """Send a command to Asterisk and return response."""
        if not self.connected or not self.manager:
            raise RuntimeError("AMI not connected")

        try:
            response = await self.manager.send_action({
                'Action': 'Command',
                'Command': command
            })
            return response
        except Exception as e:
            logger.error(f"Command failed: {command} - {e}")
            raise

    async def get_node_stats(self) -> Dict:
        """Get statistics for the configured node."""
        response = await self.send_command(f"rpt stats {config.node_number}")
        return self._parse_stats_response(response)

    async def get_connected_nodes(self) -> List[Dict]:
        """Get list of connected nodes."""
        response = await self.send_command(f"rpt nodes {config.node_number}")
        return self._parse_nodes_response(response)

    async def connect_node(self, node_number: str, monitor_only: bool = False) -> Dict:
        """Connect to another node."""
        prefix = "*2" if monitor_only else "*3"
        command = f"rpt fun {config.node_number} {prefix}{node_number}"
        response = await self.send_command(command)
        return {"success": True, "command": command, "response": response}

    async def disconnect_node(self, node_number: str) -> Dict:
        """Disconnect from a specific node."""
        command = f"rpt fun {config.node_number} *1{node_number}"
        response = await self.send_command(command)
        return {"success": True, "command": command, "response": response}

    async def disconnect_all(self) -> Dict:
        """Disconnect from all nodes."""
        command = f"rpt fun {config.node_number} *73"
        response = await self.send_command(command)
        return {"success": True, "command": command, "response": response}

    async def execute_macro(self, macro_number: str) -> Dict:
        """Execute a macro from rpt.conf."""
        command = f"rpt fun {config.node_number} *D{macro_number}"
        response = await self.send_command(command)
        return {"success": True, "command": command, "response": response}

    async def send_dtmf(self, sequence: str) -> Dict:
        """Send raw DTMF sequence."""
        command = f"rpt fun {config.node_number} {sequence}"
        response = await self.send_command(command)
        return {"success": True, "command": command, "response": response}

    def _parse_stats_response(self, response: Dict) -> Dict:
        """Parse rpt stats output into structured data."""
        output = response.get('Output', [])
        if isinstance(output, str):
            output = [output]

        stats = {
            "raw_output": output,
            "node": config.node_number,
            "callsign": config.node_callsign
        }

        # Parse key fields from output
        for line in output:
            line = line.strip()
            if "Uptime" in line and ":" in line:
                stats["uptime"] = line.split(":")[-1].strip()
            elif "Keyups today" in line and ":" in line:
                stats["keyups_today"] = line.split(":")[-1].strip()
            elif "Nodes currently connected to us" in line and ":" in line:
                connected = line.split(":")[-1].strip()
                stats["connected_nodes"] = connected if connected != "<NONE>" else "None"

        return stats

    def _parse_nodes_response(self, response: Dict) -> List[Dict]:
        """Parse rpt nodes output into structured data."""
        output = response.get('Output', [])
        if isinstance(output, str):
            output = [output]

        nodes = []
        for line in output:
            line = line.strip()
            # Skip header lines and empty lines
            if not line or line.startswith('*') or '<NONE>' in line:
                continue
            
            # Check if this line contains comma-separated nodes
            # Format: T427060, T516596, T54199, T55553, T60802
            if ',' in line:
                # Split by comma and process each node
                node_entries = line.split(',')
                for entry in node_entries:
                    entry = entry.strip()
                    if entry:
                        # Remove mode prefix (T/M/R) if present
                        mode = ""
                        node_num = entry
                        if entry and entry[0] in ['T', 'M', 'R']:
                            mode = entry[0]
                            node_num = entry[1:]
                        
                        if node_num:  # Only add if we have a node number
                            nodes.append({
                                "node": node_num,
                                "mode": mode,
                                "info": ""
                            })

        return nodes


# Global AMI client instance
ami_client = AMIClient()
