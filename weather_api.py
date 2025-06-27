import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")  # Use environment variable instead of hardcoded key

def get_weather(coords):
    lat, lon = coords
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        weather_data = {
            "temp": round(data["main"]["temp"]),
            "description": data["weather"][0]["description"],
            "icon": data["weather"][0]["icon"],
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "wind_speed": data["wind"]["speed"]
        }

        return weather_data

    except Exception as e:
        print("Error fetching weather data:", e)
        return None