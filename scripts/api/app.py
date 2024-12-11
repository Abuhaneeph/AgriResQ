from flask import Flask, request, jsonify
from model.weather_model import WeatherModel
from view.weather_view import WeatherView
from controller.weather_controller import WeatherController
from config import API_KEY

app = Flask(__name__)

# Initialize the model, view, and controller
weather_model = WeatherModel(API_KEY)
weather_view = WeatherView()
weather_controller = WeatherController(weather_model, weather_view)

@app.route("/")
def home():
    """Root endpoint."""
    return jsonify({"message": "Welcome to the Weather API!"})

@app.route("/weather", methods=["GET"])
def get_weather():
    """
    Endpoint to fetch weather data.
    
    Query Parameters:
    - location: Location to fetch weather for (default: Kano)
    - date: Date in YYYY-MM-DD format (default: 2024-01-01)
    - hour: Hour of the day (default: 14)
    """
    # Get query parameters with defaults
    location = request.args.get("location", "Kano")
    date = request.args.get("date", "2024-01-01")
    hour = request.args.get("hour", "14")
    
    # Fetch and format weather data
    try:
        result = weather_controller.get_weather(location, date, hour)
        
        # Check if there's an error in the result
        if "error" in result:
            return jsonify(result), 400
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)