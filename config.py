import os
from dotenv import load_dotenv

load_dotenv()  # Loads variables from a .env file if present

API_KEY = os.getenv("WEATHER_API_KEY")
if not API_KEY:
    raise ValueError("WEATHER_API_KEY is not set in the .env file.")

BASE_URL = "https://api.openweathermap.org/data/2.5"
CITY = os.getenv("WEATHER_CITY", "Dapoli")  # Can be set via .env or fallback to Dapoli
UNITS = os.getenv("WEATHER_UNITS", "metric")  # 'metric' or 'imperial'