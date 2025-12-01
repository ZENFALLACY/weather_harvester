"""
Command-line interface for Weather Harvester.

Provides subcommands for fetching, monitoring, and managing weather data.
"""

import argparse
import sys
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional
from . import __version__
from .logger import setup_logger, get_logger
from .config import load_config, Config
from .cache import Cache
from .fetcher import WeatherFetcher
from .alerts import AlertManager
from .plugins import registry
from .utils import EXIT_SUCCESS, EXIT_GENERAL_ERROR, EXIT_CONFIG_ERROR


logger = None  # Will be initialized in main()


def cmd_fetch(args: argparse.Namespace) -> int:
    """
    Handle the 'fetch' subcommand.
    
    Args:
        args: Parsed command-line arguments
    
    Returns:
        Exit code
    """
    try:
        # Load configuration
        config = load_config(args.config, args.profile)
        
        # Initialize components
        cache = Cache(
            cache_dir=config.get('cache_dir') or None,
            default_ttl=config.get('cache_ttl', 300)
        )
        fetcher = WeatherFetcher(config, cache)
        
        # Fetch weather data
        location = args.location or "London"
        logger.info(f"Fetching weather for: {location}")
        
        weather_data = fetcher.fetch(
            location,
            use_cache=not args.no_cache
        )
        
        # Apply plugins
        for plugin_class in registry.get_all_plugins().values():
            plugin = plugin_class()
            logger.debug(f"Applying plugin: {plugin.name}")
            weather_data = plugin.process(weather_data)
        
        # Output results
        if args.output == 'json':
            print(json.dumps(weather_data, indent=2))
        else:
            _print_weather_summary(weather_data)
        
        logger.info("Fetch completed successfully")
        return EXIT_SUCCESS
    
    except Exception as e:
        logger.error(f"Fetch failed: {e}")
        return EXIT_GENERAL_ERROR


def cmd_monitor(args: argparse.Namespace) -> int:
    """
    Handle the 'monitor' subcommand.
    
    Args:
        args: Parsed command-line arguments
    
    Returns:
        Exit code
    """
    try:
        # Load configuration
        config = load_config(args.config, args.profile)
        
        # Initialize components
        cache = Cache(
            cache_dir=config.get('cache_dir') or None,
            default_ttl=config.get('cache_ttl', 300)
        )
        fetcher = WeatherFetcher(config, cache)
        alert_manager = AlertManager(config)
        
        # Parse locations
        locations = args.locations or ["London"]
        interval = args.interval
        
        logger.info(f"Starting monitoring for {len(locations)} location(s)")
        logger.info(f"Interval: {interval} seconds")
        
        iteration = 0
        
        try:
            while True:
                iteration += 1
                logger.info(f"Monitoring iteration {iteration}")
                
                # Fetch data for all locations (with threading)
                if args.parallel:
                    _monitor_parallel(locations, fetcher, alert_manager)
                else:
                    _monitor_sequential(locations, fetcher, alert_manager)
                
                # Wait for next iteration
                logger.debug(f"Waiting {interval} seconds...")
                time.sleep(interval)
        
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
            return EXIT_SUCCESS
    
    except Exception as e:
        logger.error(f"Monitoring failed: {e}")
        return EXIT_GENERAL_ERROR


def _monitor_sequential(
    locations: List[str],
    fetcher: WeatherFetcher,
    alert_manager: AlertManager
) -> None:
    """Monitor locations sequentially."""
    for location in locations:
        try:
            weather_data = fetcher.fetch(location)
            
            # Apply plugins
            for plugin_class in registry.get_all_plugins().values():
                plugin = plugin_class()
                weather_data = plugin.process(weather_data)
            
            # Check alerts
            alerts = alert_manager.check_and_alert(location, weather_data)
            
            if not alerts:
                logger.info(f"{location}: No alerts")
        
        except Exception as e:
            logger.error(f"Failed to monitor {location}: {e}")


def _monitor_parallel(
    locations: List[str],
    fetcher: WeatherFetcher,
    alert_manager: AlertManager
) -> None:
    """Monitor locations in parallel using ThreadPoolExecutor."""
    def fetch_and_check(location: str):
        try:
            weather_data = fetcher.fetch(location)
            
            # Apply plugins
            for plugin_class in registry.get_all_plugins().values():
                plugin = plugin_class()
                weather_data = plugin.process(weather_data)
            
            # Check alerts
            alerts = alert_manager.check_and_alert(location, weather_data)
            
            if not alerts:
                logger.info(f"{location}: No alerts")
            
            return location, True
        
        except Exception as e:
            logger.error(f"Failed to monitor {location}: {e}")
            return location, False
    
    with ThreadPoolExecutor(max_workers=min(len(locations), 5)) as executor:
        futures = {executor.submit(fetch_and_check, loc): loc for loc in locations}
        
        for future in as_completed(futures):
            location = futures[future]
            try:
                future.result()
            except Exception as e:
                logger.error(f"Unexpected error for {location}: {e}")


def cmd_list_plugins(args: argparse.Namespace) -> int:
    """
    Handle the 'list-plugins' subcommand.
    
    Args:
        args: Parsed command-line arguments
    
    Returns:
        Exit code
    """
    plugins = registry.get_all_plugins()
    
    if not plugins:
        print("No plugins found.")
        return EXIT_SUCCESS
    
    print(f"Available plugins ({len(plugins)}):\n")
    
    for plugin_class in plugins.values():
        plugin = plugin_class()
        print(f"  • {plugin.name} v{plugin.version}")
        print(f"    {plugin.description}")
        print()
    
    return EXIT_SUCCESS


def cmd_test_config(args: argparse.Namespace) -> int:
    """
    Handle the 'test-config' subcommand.
    
    Args:
        args: Parsed command-line arguments
    
    Returns:
        Exit code
    """
    try:
        config = load_config(args.config, args.profile)
        
        print(f"[OK] Configuration loaded successfully")
        print(f"  Profile: {args.profile}")
        print(f"  File: {args.config}")
        print()
        
        # Validate configuration
        if config.validate():
            print("[OK] Configuration is valid")
            
            if args.verbose:
                print("\nConfiguration values:")
                for key, value in sorted(config.get_all().items()):
                    # Mask sensitive values
                    if 'password' in key.lower() or 'key' in key.lower():
                        value = '***' if value else ''
                    print(f"  {key}: {value}")
            
            return EXIT_SUCCESS
        else:
            print("[FAIL] Configuration validation failed")
            return EXIT_CONFIG_ERROR
    
    except SystemExit as e:
        return e.code
    except Exception as e:
        print(f"[ERROR] {e}")
        return EXIT_CONFIG_ERROR


def _print_weather_summary(data: dict) -> None:
    """
    Print a human-readable weather summary.
    
    Args:
        data: Weather data dictionary
    """
    location = data.get('name', 'Unknown')
    main = data.get('main', {})
    weather = data.get('weather', [{}])[0]
    wind = data.get('wind', {})
    
    print(f"\n{'='*50}")
    print(f"Weather Report: {location}")
    print(f"{'='*50}")
    
    # Temperature
    temp_c = main.get('temp_celsius', main.get('temp', 0) - 273.15)
    temp_f = main.get('temp_fahrenheit', temp_c * 9/5 + 32)
    print(f"Temperature: {temp_c:.1f}°C ({temp_f:.1f}°F)")
    
    if 'temp_category' in main:
        print(f"  Category: {main['temp_category']}")
    
    # Conditions
    print(f"Conditions: {weather.get('description', 'N/A').title()}")
    print(f"Humidity: {main.get('humidity', 'N/A')}%")
    print(f"Pressure: {main.get('pressure', 'N/A')} hPa")
    print(f"Wind Speed: {wind.get('speed', 'N/A')} m/s")
    
    # Insights (if added by plugins)
    if 'insights' in data:
        print(f"\nInsights:")
        for insight in data['insights']:
            print(f"  • {insight}")
    
    print(f"{'='*50}\n")


def main(argv: Optional[List[str]] = None) -> int:
    """
    Main entry point for the CLI.
    
    Args:
        argv: Command-line arguments (default: sys.argv)
    
    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        prog='weather-harvester',
        description='Resilient weather data fetching and monitoring tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    # Global options
    parser.add_argument(
        '--config',
        default='configs/example.ini',
        help='Path to configuration file (default: configs/example.ini)'
    )
    
    parser.add_argument(
        '--profile',
        default='default',
        help='Configuration profile to use (default: default)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Fetch subcommand
    fetch_parser = subparsers.add_parser('fetch', help='Fetch weather data once')
    fetch_parser.add_argument(
        '--location', '-l',
        help='Location (city name or "lat,lon")'
    )
    fetch_parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Bypass cache and fetch fresh data'
    )
    fetch_parser.add_argument(
        '--output', '-o',
        choices=['json', 'summary'],
        default='summary',
        help='Output format (default: summary)'
    )
    
    # Monitor subcommand
    monitor_parser = subparsers.add_parser('monitor', help='Monitor weather continuously')
    monitor_parser.add_argument(
        '--locations', '-l',
        nargs='+',
        help='Locations to monitor (city names or "lat,lon")'
    )
    monitor_parser.add_argument(
        '--interval', '-i',
        type=int,
        default=300,
        help='Monitoring interval in seconds (default: 300)'
    )
    monitor_parser.add_argument(
        '--parallel', '-p',
        action='store_true',
        help='Fetch locations in parallel'
    )
    
    # List plugins subcommand
    subparsers.add_parser('list-plugins', help='List available plugins')
    
    # Test config subcommand
    test_config_parser = subparsers.add_parser('test-config', help='Validate configuration')
    
    # Parse arguments
    args = parser.parse_args(argv)
    
    # Set up logging
    global logger
    logger = setup_logger(
        level=args.log_level,
        console_output=True
    )
    
    if args.verbose:
        logger.setLevel('DEBUG')
    
    # Handle subcommands
    if args.command == 'fetch':
        return cmd_fetch(args)
    elif args.command == 'monitor':
        return cmd_monitor(args)
    elif args.command == 'list-plugins':
        return cmd_list_plugins(args)
    elif args.command == 'test-config':
        return cmd_test_config(args)
    else:
        parser.print_help()
        return EXIT_SUCCESS


if __name__ == '__main__':
    sys.exit(main())


__all__ = ['main']
