import requests

class WeatherModel:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://api.weatherapi.com/v1/history.json"
    
    def fetch_weather_data(self, location, date, hour):
        """
        Fetch weather data from WeatherAPI
        
        Args:
            location (str): Location to fetch weather for
            date (str): Date in YYYY-MM-DD format
            hour (str): Hour of the day (0-23)
        
        Returns:
            dict: Weather data or error information
        """
        try:
            params = {
                "key": self.api_key,
                "q": location,
                "dt": date,
                "hour": hour
            }
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
        except requests.RequestException as e:
            return {"error": f"Failed to fetch data: {str(e)}"}