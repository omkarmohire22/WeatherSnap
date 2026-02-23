import requests
from config import API_KEY, BASE_URL, CITY, UNITS

def get_weather(city=None):
    """Fetch current weather data for the specified city (or default)."""
    city = city or CITY
    try:
        url = f"{BASE_URL}/weather?q={city}&appid={API_KEY}&units={UNITS}"
        response = requests.get(url, timeout=8)
        response.raise_for_status()
        data = response.json()
        
        # Add AQI if possible
        if "coord" in data:
            lat = data["coord"]["lat"]
            lon = data["coord"]["lon"]
            aqi_data = get_aqi_by_coords(lat, lon)
            data["aqi"] = aqi_data
            
        return data
    except requests.RequestException as e:
        try:
            return {"error": response.json().get("message", str(e))}
        except Exception:
            return {"error": str(e)}

def get_aqi_by_coords(lat, lon):
    """Fetch AQI data from OpenWeatherMap Air Pollution API."""
    try:
        url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if "list" in data and len(data["list"]) > 0:
            return data["list"][0]["main"]["aqi"]
    except Exception:
        pass
    return None

def get_forecast(city=None):
    """Fetch 5-day/3-hour forecast data for the specified city (or default)."""
    city = city or CITY
    try:
        url = f"{BASE_URL}/forecast?q={city}&appid={API_KEY}&units={UNITS}"
        response = requests.get(url, timeout=8)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        try:
            return {"error": response.json().get("message", str(e))}
        except Exception:
            return {"error": str(e)}

def extract_daily_forecast(forecast_json, days=4):
    """
    Extracts daily forecast summary from OpenWeatherMap 3-hourly forecast.
    """
    if not forecast_json or "list" not in forecast_json:
        return []
    
    daily = {}
    for entry in forecast_json["list"]:
        # Get date string (YYYY-MM-DD)
        dt = entry["dt_txt"].split()
        date_str = dt[0]
        
        # We want the mid-day forecast for the icon/temp (around 12:00:00 or 15:00:00)
        time_str = dt[1]
        
        if date_str not in daily:
            daily[date_str] = {
                "temp": entry["main"]["temp"],
                "desc": entry["weather"][0]["description"],
                "icon": entry["weather"][0]["icon"],
                "time": time_str
            }
        else:
            # Prefer midday for representative daily weather
            if "12:00:00" <= time_str <= "15:00:00":
                daily[date_str] = {
                    "temp": entry["main"]["temp"],
                    "desc": entry["weather"][0]["description"],
                    "icon": entry["weather"][0]["icon"],
                    "time": time_str
                }
    
    # Sort and skip today
    today = forecast_json["list"][0]["dt_txt"].split()[0]
    sorted_days = sorted(daily.keys())
    
    result = []
    for d in sorted_days:
        if d == today: continue
        result.append({
            "date": d,
            "temp": daily[d]["temp"],
            "desc": daily[d]["desc"].capitalize(),
            "icon": daily[d]["icon"]
        })
        if len(result) >= days:
            break
            
    return result

def get_aqi(city=None):
    """Fallback if coords not available."""
    return {"aqi": None}

def get_sun_times(weather_data=None):
    """Extract sunrise/sunset from main weather response."""
    if weather_data and "sys" in weather_data:
        import datetime
        from tzlocal import get_localzone
        
        try:
            local_tz = get_localzone()
            sr = datetime.datetime.fromtimestamp(weather_data["sys"]["sunrise"], local_tz).strftime("%H:%M")
            ss = datetime.datetime.fromtimestamp(weather_data["sys"]["sunset"], local_tz).strftime("%H:%M")
            return {"sunrise": sr, "sunset": ss}
        except Exception:
            return {"sunrise": "--:--", "sunset": "--:--"}
    return {"sunrise": "--:--", "sunset": "--:--"}
