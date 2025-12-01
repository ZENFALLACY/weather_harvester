"""
Plugin system for Weather Harvester.

This module handles dynamic discovery and loading of plugins.
"""

import os
import sys
import importlib.util
from typing import List, Dict, Type
from .base import BasePlugin


class PluginRegistry:
    """Registry for managing and discovering plugins."""
    
    def __init__(self):
        self._plugins: Dict[str, Type[BasePlugin]] = {}
    
    def register(self, plugin_class: Type[BasePlugin]) -> None:
        """Register a plugin class."""
        if not issubclass(plugin_class, BasePlugin):
            raise TypeError(f"{plugin_class.__name__} must inherit from BasePlugin")
        self._plugins[plugin_class.__name__] = plugin_class
    
    def get_plugin(self, name: str) -> Type[BasePlugin]:
        """Get a plugin by name."""
        return self._plugins.get(name)
    
    def list_plugins(self) -> List[str]:
        """List all registered plugin names."""
        return list(self._plugins.keys())
    
    def get_all_plugins(self) -> Dict[str, Type[BasePlugin]]:
        """Get all registered plugins."""
        return self._plugins.copy()


# Global plugin registry
registry = PluginRegistry()


def discover_plugins() -> None:
    """
    Dynamically discover and load all plugins from the plugins directory.
    
    Scans for .py files (excluding __init__.py and base.py) and imports them.
    Each plugin module should define a class inheriting from BasePlugin.
    """
    plugins_dir = os.path.dirname(__file__)
    
    for filename in os.listdir(plugins_dir):
        if not filename.endswith('.py'):
            continue
        if filename in ('__init__.py', 'base.py'):
            continue
        
        module_name = filename[:-3]  # Remove .py extension
        module_path = os.path.join(plugins_dir, filename)
        
        try:
            # Load module dynamically
            spec = importlib.util.spec_from_file_location(
                f"weather_harvester.plugins.{module_name}",
                module_path
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                spec.loader.exec_module(module)
                
                # Find and register plugin classes
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, BasePlugin) and 
                        attr is not BasePlugin):
                        registry.register(attr)
        
        except Exception as e:
            # Log error but continue loading other plugins
            print(f"Warning: Failed to load plugin {module_name}: {e}", file=sys.stderr)


# Auto-discover plugins on import
discover_plugins()


__all__ = ["BasePlugin", "PluginRegistry", "registry", "discover_plugins"]
