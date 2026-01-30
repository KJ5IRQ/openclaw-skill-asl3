"""Configuration loader for ASL Agent."""
import yaml
from pathlib import Path
from typing import Dict, Any


class Config:
    """Load and provide access to configuration."""
    
    def __init__(self, config_path: str = "/opt/asl-agent/config.yaml"):
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self.load()
    
    def load(self):
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            self._config = yaml.safe_load(f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        
        return value
    
    @property
    def ami_host(self) -> str:
        return self.get('ami.host', '127.0.0.1')
    
    @property
    def ami_port(self) -> int:
        return self.get('ami.port', 5038)
    
    @property
    def ami_username(self) -> str:
        return self.get('ami.username', 'asl-agent')
    
    @property
    def ami_password(self) -> str:
        return self.get('ami.password', '')
    
    @property
    def node_number(self) -> str:
        return self.get('node.number', '')
    
    @property
    def node_callsign(self) -> str:
        return self.get('node.callsign', '')
    
    @property
    def api_host(self) -> str:
        return self.get('api.host', '0.0.0.0')
    
    @property
    def api_port(self) -> int:
        return self.get('api.port', 8073)
    
    @property
    def api_key(self) -> str:
        return self.get('api.api_key', '')
    
    @property
    def webhooks_enabled(self) -> bool:
        return self.get('webhooks.enabled', False)
    
    @property
    def n8n_url(self) -> str:
        return self.get('webhooks.n8n_url', '')
    
    @property
    def log_level(self) -> str:
        return self.get('logging.level', 'INFO')
    
    @property
    def audit_file(self) -> str:
        return self.get('logging.audit_file', '/opt/asl-agent/audit.log')
    
    @property
    def rate_limit(self) -> int:
        return self.get('security.rate_limit_per_minute', 10)
    
    @property
    def require_confirmation(self) -> list:
        return self.get('security.require_confirmation', [])


# Global config instance
config = Config()
