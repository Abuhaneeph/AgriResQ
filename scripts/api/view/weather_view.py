# view/weather_view.py
class WeatherView:
    def display_weather(self, weather_data):
        """
        Format weather data for display
        
        Args:
            weather_data (dict): Raw weather data from the API
        
        Returns:
            dict: Formatted weather information
        """
        if "error" in weather_data:
            return {"error": weather_data["error"]}
        
        try:
            # Extract forecast and hour data
            forecast = weather_data.get('forecast', {}).get('forecastday', [{}])[0]
            hour_data = forecast.get('hour', [{}])[0]
            day_data = forecast.get('day', {})
            
            return {
                "time": hour_data.get('time', ''),
                "temperature": f"{hour_data.get('temp_c', '')}°C",
                "feels_like": f"{hour_data.get('feelslike_c', '')}°C",
                "rainfall": f"{hour_data.get('precip_mm', 0.0)} mm",
                "chance_of_rain": f"{hour_data.get('chance_of_rain', 0)}%",
                "wind_speed": f"{hour_data.get('wind_kph', 0.0)} kph",
                "humidity": f"{hour_data.get('humidity', 0)}%",
                "uv_index": hour_data.get('uv', 0.0),
                "cloud_cover": f"{hour_data.get('cloud', 0)}%",
                "condition": hour_data.get('condition', {}).get('text', ''),
                "condition_icon_url": hour_data.get('condition', {}).get('icon', '')
            }
        except Exception as e:
            return {"error": f"Error formatting weather data: {str(e)}"}