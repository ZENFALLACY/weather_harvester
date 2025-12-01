"""
Alert system for Weather Harvester.

Supports console and SMTP email alerts based on threshold rules.
"""

import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from .logger import get_logger
from .config import Config


logger = get_logger(__name__)


class AlertManager:
    """
    Manages alerts for weather conditions exceeding thresholds.
    
    Supports console and email alerts with spam prevention.
    """
    
    def __init__(self, config: Config):
        """
        Initialize alert manager.
        
        Args:
            config: Configuration instance
        """
        self.config = config
        
        # Threshold settings
        self.temp_min = config.get('alert_temperature_min', -999)
        self.temp_max = config.get('alert_temperature_max', 999)
        self.humidity_max = config.get('alert_humidity_max', 100)
        self.wind_speed_max = config.get('alert_wind_speed_max', 999)
        
        # SMTP settings
        self.smtp_host = config.get('smtp_host', '')
        self.smtp_port = config.get('smtp_port', 587)
        self.smtp_user = config.get('smtp_user', '')
        self.smtp_password = config.get('smtp_password', '')
        self.smtp_from = config.get('smtp_from', '')
        self.smtp_to = config.get('smtp_to', '')
        
        # Alert history for spam prevention (location -> last alert time)
        self._alert_history: Dict[str, datetime] = {}
        self._alert_cooldown = timedelta(minutes=15)  # Min time between alerts
    
    def check_and_alert(self, location: str, weather_data: Dict[str, Any]) -> List[str]:
        """
        Check weather data against thresholds and trigger alerts.
        
        Args:
            location: Location identifier
            weather_data: Weather data dictionary
        
        Returns:
            List of triggered alert messages
        """
        alerts = []
        
        # Extract weather metrics
        main = weather_data.get('main', {})
        wind = weather_data.get('wind', {})
        
        temp_kelvin = main.get('temp')
        humidity = main.get('humidity')
        wind_speed = wind.get('speed')
        
        # Convert temperature from Kelvin to Celsius
        if temp_kelvin is not None:
            temp_celsius = temp_kelvin - 273.15
            
            if temp_celsius < self.temp_min:
                alerts.append(
                    f"Temperature too low: {temp_celsius:.1f}°C "
                    f"(threshold: {self.temp_min}°C)"
                )
            elif temp_celsius > self.temp_max:
                alerts.append(
                    f"Temperature too high: {temp_celsius:.1f}°C "
                    f"(threshold: {self.temp_max}°C)"
                )
        
        # Check humidity
        if humidity is not None and humidity > self.humidity_max:
            alerts.append(
                f"Humidity too high: {humidity}% "
                f"(threshold: {self.humidity_max}%)"
            )
        
        # Check wind speed
        if wind_speed is not None and wind_speed > self.wind_speed_max:
            alerts.append(
                f"Wind speed too high: {wind_speed} m/s "
                f"(threshold: {self.wind_speed_max} m/s)"
            )
        
        # Trigger alerts if any
        if alerts:
            self._trigger_alerts(location, alerts, weather_data)
        
        return alerts
    
    def _trigger_alerts(
        self,
        location: str,
        alert_messages: List[str],
        weather_data: Dict[str, Any]
    ) -> None:
        """
        Trigger all configured alert handlers.
        
        Args:
            location: Location identifier
            alert_messages: List of alert messages
            weather_data: Full weather data
        """
        # Check cooldown to prevent spam
        if not self._should_alert(location):
            logger.debug(f"Skipping alert for {location} (cooldown active)")
            return
        
        # Update alert history
        self._alert_history[location] = datetime.utcnow()
        
        # Console alert
        self._console_alert(location, alert_messages, weather_data)
        
        # Email alert (if configured)
        if self.smtp_host and self.smtp_to:
            try:
                self._email_alert(location, alert_messages, weather_data)
            except Exception as e:
                logger.error(f"Failed to send email alert: {e}")
    
    def _should_alert(self, location: str) -> bool:
        """
        Check if enough time has passed since last alert for this location.
        
        Args:
            location: Location identifier
        
        Returns:
            True if should alert, False if in cooldown
        """
        last_alert = self._alert_history.get(location)
        if last_alert is None:
            return True
        
        return datetime.utcnow() - last_alert > self._alert_cooldown
    
    def _console_alert(
        self,
        location: str,
        alert_messages: List[str],
        weather_data: Dict[str, Any]
    ) -> None:
        """
        Print alert to console with ANSI colors.
        
        Args:
            location: Location identifier
            alert_messages: List of alert messages
            weather_data: Full weather data
        """
        # ANSI color codes
        RED = '\033[91m'
        YELLOW = '\033[93m'
        BOLD = '\033[1m'
        RESET = '\033[0m'
        
        use_colors = sys.stderr.isatty()
        
        if use_colors:
            header = f"{BOLD}{RED}⚠ WEATHER ALERT{RESET}"
        else:
            header = "⚠ WEATHER ALERT"
        
        print(f"\n{header}", file=sys.stderr)
        print(f"Location: {location}", file=sys.stderr)
        print(f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}", file=sys.stderr)
        print("", file=sys.stderr)
        
        for msg in alert_messages:
            if use_colors:
                print(f"  {YELLOW}•{RESET} {msg}", file=sys.stderr)
            else:
                print(f"  • {msg}", file=sys.stderr)
        
        print("", file=sys.stderr)
        
        logger.warning(f"Alert triggered for {location}: {', '.join(alert_messages)}")
    
    def _email_alert(
        self,
        location: str,
        alert_messages: List[str],
        weather_data: Dict[str, Any]
    ) -> None:
        """
        Send email alert via SMTP.
        
        Args:
            location: Location identifier
            alert_messages: List of alert messages
            weather_data: Full weather data
        """
        # Build email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Weather Alert: {location}'
        msg['From'] = self.smtp_from
        msg['To'] = self.smtp_to
        
        # Plain text body
        text_body = f"""
Weather Alert for {location}
Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

Alerts:
{chr(10).join(f'  • {alert}' for alert in alert_messages)}

Current Conditions:
  Temperature: {weather_data.get('main', {}).get('temp', 'N/A')} K
  Humidity: {weather_data.get('main', {}).get('humidity', 'N/A')}%
  Wind Speed: {weather_data.get('wind', {}).get('speed', 'N/A')} m/s
  Description: {weather_data.get('weather', [{}])[0].get('description', 'N/A')}

---
Weather Harvester Alert System
"""
        
        msg.attach(MIMEText(text_body, 'plain'))
        
        # Send email
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email alert sent to {self.smtp_to}")
        
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            raise
        except Exception as e:
            logger.error(f"Email error: {e}")
            raise


__all__ = ['AlertManager']
