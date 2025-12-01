"""
Base plugin interface for Weather Harvester.

All plugins must inherit from BasePlugin and implement required methods.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BasePlugin(ABC):
    """
    Abstract base class for all Weather Harvester plugins.
    
    Plugins can process, transform, or analyze weather data.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Plugin name.
        
        Returns:
            Plugin name string
        """
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """
        Plugin version.
        
        Returns:
            Version string (e.g., "1.0.0")
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Plugin description.
        
        Returns:
            Brief description of plugin functionality
        """
        pass
    
    @abstractmethod
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process weather data.
        
        This is the main entry point for plugin functionality.
        Plugins can transform, enrich, or analyze the data.
        
        Args:
            data: Weather data dictionary
        
        Returns:
            Processed/transformed data dictionary
        """
        pass
    
    def validate(self) -> bool:
        """
        Validate plugin health/configuration.
        
        Override this method to perform plugin-specific validation.
        
        Returns:
            True if plugin is healthy, False otherwise
        """
        return True
    
    def __repr__(self) -> str:
        """String representation of plugin."""
        return f"<{self.__class__.__name__} v{self.version}: {self.description}>"


__all__ = ['BasePlugin']
