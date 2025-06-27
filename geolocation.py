import requests
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

API_KEY = os.getenv("OPENWEATHER_API_KEY")  # ✅ Read the key from .env

def get_coordinates(city_name):
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={API_KEY}"  # ✅ Use the variable
    response = requests.get(url).json()

    if response and isinstance(response, list) and len(response) > 0:
        return response[0]["lat"], response[0]["lon"], response[0]["name"], response[0]["country"]
    else:
        return None, None, None, None
