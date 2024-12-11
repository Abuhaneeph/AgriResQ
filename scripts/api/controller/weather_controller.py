class WeatherController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
    
    def get_weather(self, location, date, hour):
        """
        Get weather data from the model and format it via the view.
        
        Args:
            location (str): Location to fetch weather for
            date (str): Date in YYYY-MM-DD format
            hour (str): Hour of the day (0-23)
        
        Returns:
            dict: Formatted weather data or error information
        """
        # Fetch raw data from the model
        raw_data = self.model.fetch_weather_data(location, date, hour)
        
        # Format the data using the view
        return self.view.display_weather(raw_data)