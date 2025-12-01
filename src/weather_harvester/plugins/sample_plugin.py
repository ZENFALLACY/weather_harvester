"""
Sample plugin demonstrating the Weather Harvester plugin interface.

This plugin converts temperature units and analyzes thresholds.
"""

from typing import Dict, Any
from .base import BasePlugin


class TemperatureConverterPlugin(BasePlugin):
    """
    Plugin that converts temperature from Kelvin to Celsius and Fahrenheit.
    
    Also adds temperature category analysis.
    """
    
    @property
    def name(self) -> str:
        return "TemperatureConverter"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Converts temperature units and categorizes temperature ranges"
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process weather data to add temperature conversions.
        
        Args:
            data: Weather data with temperature in Kelvin
        
        Returns:
            Enhanced data with Celsius and Fahrenheit temperatures
        """
        # Make a copy to avoid modifying original
        result = data.copy()
        
        # Extract temperature in Kelvin
        main = result.get('main', {})
        temp_kelvin = main.get('temp')
        
        if temp_kelvin is not None:
            # Convert to Celsius and Fahrenheit
            temp_celsius = temp_kelvin - 273.15
            temp_fahrenheit = (temp_celsius * 9/5) + 32
            
            # Add converted temperatures
            main['temp_celsius'] = round(temp_celsius, 2)
            main['temp_fahrenheit'] = round(temp_fahrenheit, 2)
            
            # Add temperature category
            main['temp_category'] = self._categorize_temperature(temp_celsius)
            
            result['main'] = main
        
        return result
    
    def _categorize_temperature(self, temp_celsius: float) -> str:
        """
        Categorize temperature into human-readable ranges.
        
        Args:
            temp_celsius: Temperature in Celsius
        
        Returns:
            Category string
        """
        if temp_celsius < -10:
            return "Extremely Cold"
        elif temp_celsius < 0:
            return "Very Cold"
        elif temp_celsius < 10:
            return "Cold"
        elif temp_celsius < 20:
            return "Cool"
        elif temp_celsius < 25:
            return "Comfortable"
        elif temp_celsius < 30:
            return "Warm"
        elif temp_celsius < 35:
            return "Hot"
        else:
            return "Extremely Hot"


class WeatherAnalyzerPlugin(BasePlugin):
    """
    Plugin that analyzes weather conditions and adds insights.
    """
    
    @property
    def name(self) -> str:
        return "WeatherAnalyzer"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Analyzes weather conditions and provides insights"
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze weather data and add insights.
        
        Args:
            data: Weather data
        
        Returns:
            Enhanced data with analysis insights
        """
        result = data.copy()
        
        insights = []
        
        # Analyze humidity
        humidity = data.get('main', {}).get('humidity')
        if humidity is not None:
            if humidity > 80:
                insights.append("High humidity - may feel uncomfortable")
            elif humidity < 30:
                insights.append("Low humidity - air is dry")
        
        # Analyze wind
        wind_speed = data.get('wind', {}).get('speed')
        if wind_speed is not None:
            if wind_speed > 10:
                insights.append("Strong winds - take precautions")
            elif wind_speed < 1:
                insights.append("Calm conditions")
        
        # Analyze visibility
        visibility = data.get('visibility')
        if visibility is not None:
            if visibility < 1000:
                insights.append("Poor visibility - fog or haze")
        
        # Analyze clouds
        clouds = data.get('clouds', {}).get('all')
        if clouds is not None:
            if clouds > 80:
                insights.append("Overcast skies")
            elif clouds < 20:
                insights.append("Clear skies")
        
        # Add insights to result
        if insights:
            result['insights'] = insights
        
        return result


__all__ = ['TemperatureConverterPlugin', 'WeatherAnalyzerPlugin']
