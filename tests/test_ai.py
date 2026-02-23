from weather_api import get_weather, get_forecast

def test_weather():
    weather = get_weather()
    assert isinstance(weather, dict), "Weather response is not a dictionary"
    assert "error" not in weather, f"API Error: {weather.get('error')}"
    assert "main" in weather, "Missing 'main' in weather data"
    print("Weather test passed.")

def test_forecast():
    forecast = get_forecast()
    assert isinstance(forecast, dict), "Forecast response is not a dictionary"
    assert "error" not in forecast, f"API Error: {forecast.get('error')}"
    assert "list" in forecast, "Missing 'list' in forecast data"
    print("Forecast test passed.")

if __name__ == "__main__":
    try:
        test_weather()
        test_forecast()
        print("All tests passed.")
    except AssertionError as e:
        print("Test failed:", e)