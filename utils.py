import datetime

def kelvin_to_celsius(kelvin):
    """Convert Kelvin to Celsius."""
    try:
        return round(float(kelvin) - 273.15, 1)
    except Exception:
        return kelvin

def kelvin_to_fahrenheit(kelvin):
    """Convert Kelvin to Fahrenheit."""
    try:
        return round((float(kelvin) - 273.15) * 9/5 + 32, 1)
    except Exception:
        return kelvin

def format_datetime(dt_str, fmt="%Y-%m-%d %H:%M:%S", out_fmt="%a, %b %d"):
    """Format a datetime string to a more readable format."""
    try:
        dt = datetime.datetime.strptime(dt_str, fmt)
        return dt.strftime(out_fmt)
    except Exception:
        return dt_str

def format_time(dt_str, fmt="%Y-%m-%d %H:%M:%S", out_fmt="%H:%M"):
    """Format a datetime string to just time (for sunrise/sunset)."""
    try:
        dt = datetime.datetime.strptime(dt_str, fmt)
        return dt.strftime(out_fmt)
    except Exception:
        return dt_str

def capitalize_description(desc):
    """Capitalize the first letter of each word in a weather description."""
    if not isinstance(desc, str):
        return desc
    return " ".join(word.capitalize() for word in desc.split())