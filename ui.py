# ui.py
import os
import time
import datetime
import requests
import io
import customtkinter as ctk
import pytz
import tzlocal
from customtkinter import CTkImage
from PIL import Image, ImageDraw, ImageFilter
from weather_api import get_weather, get_forecast, extract_daily_forecast

ICON_PATH = os.path.join("assets", "icons")
if not os.path.exists(ICON_PATH):
    os.makedirs(ICON_PATH)

def get_gradient_bg(condition: str):
    cond = (condition or "").lower()
    if "clear" in cond:
        return ("#4facfe", "#00f2fe")  # bright blue
    if "rain" in cond or "drizzle" in cond or "storm" in cond:
        return ("#485563", "#29323c")  # dark grey/blue
    if "cloud" in cond or "overcast" in cond:
        return ("#bdc3c7", "#2c3e50")  # metallic
    if "snow" in cond:
        return ("#e6e9f0", "#eef1f5")  # white/light blue
    return ("#6a11cb", "#2575fc")  # purple/blue

def create_rounded_gradient(width: int, height: int, color1: str, color2: str, radius: int = 32):
    """Return a PIL RGBA image with vertical gradient and rounded corners."""
    img = Image.new("RGBA", (width, height), color1)
    draw = ImageDraw.Draw(img)
    for i in range(height):
        ratio = i / (height - 1) if height > 1 else 0
        r = int(int(color1[1:3], 16) * (1 - ratio) + int(color2[1:3], 16) * ratio)
        g = int(int(color1[3:5], 16) * (1 - ratio) + int(color2[3:5], 16) * ratio)
        b = int(int(color1[5:7], 16) * (1 - ratio) + int(color2[5:7], 16) * ratio)
        draw.line([(0, i), (width, i)], fill=(r, g, b))
    
    mask = Image.new("L", (width, height), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([(0, 0), (width, height)], radius=radius, fill=255)
    img.putalpha(mask)
    return img

class WeatherSnap(ctk.CTk):
    def __init__(self, width=320, height=480):
        super().__init__()
        self.title("WeatherSnap")
        self.geometry(f"{width}x{height}")
        self.minsize(300, 400)
        
        # Make it appear centered on screen
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        pos_x = (screen_w // 2) - (width // 2)
        pos_y = (screen_h // 2) - (height // 2)
        self.geometry(f"+{pos_x}+{pos_y}")

        # State
        self.current_weather = {}
        self.forecast_data = []
        self.use_fahrenheit = False
        self.icon_cache = {}

        # Background
        self.bg_label = ctk.CTkLabel(self, text="")
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Main Container (Glassmorphism effect)
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=20, pady=20)

        # UI Components
        self._setup_ui()
        
        # Initial Refresh
        self.refresh()

    def _setup_ui(self):
        # Header: Date and City
        header = ctk.CTkFrame(self.container, fg_color="transparent")
        header.pack(fill="x", pady=(10, 20))
        
        self.date_label = ctk.CTkLabel(header, text="Monday, 24 Feb", font=("Segoe UI", 14), text_color="white")
        self.date_label.pack(side="top", anchor="w")
        
        self.city_label = ctk.CTkLabel(header, text="Loading...", font=("Segoe UI", 24, "bold"), text_color="white")
        self.city_label.pack(side="top", anchor="w")

        # Main Weather Entry
        main_info = ctk.CTkFrame(self.container, fg_color="transparent")
        main_info.pack(fill="x", pady=10)
        
        self.icon_label = ctk.CTkLabel(main_info, text="", width=100, height=100)
        self.icon_label.pack(side="left")
        
        temp_container = ctk.CTkFrame(main_info, fg_color="transparent")
        temp_container.pack(side="left", padx=20)
        
        self.temp_label = ctk.CTkLabel(temp_container, text="--°", font=("Segoe UI", 64, "bold"), text_color="white")
        self.temp_label.pack(side="top", anchor="w")
        
        self.desc_label = ctk.CTkLabel(temp_container, text="---", font=("Segoe UI", 16), text_color="#E0E0E0")
        self.desc_label.pack(side="top", anchor="w")

        # Stats Row
        stats_frame = ctk.CTkFrame(self.container, fg_color="gray20", corner_radius=15)
        stats_frame.pack(fill="x", pady=20, ipady=10)
        
        self.humidity_lbl = self._create_stat_item(stats_frame, "💧", "Humidity", "--%")
        self.wind_lbl = self._create_stat_item(stats_frame, "💨", "Wind", "-- m/s")
        self.aqi_lbl = self._create_stat_item(stats_frame, "🍃", "AQI", "--")

        # Forecast Title
        ctk.CTkLabel(self.container, text="Daily Forecast", font=("Segoe UI", 16, "bold"), text_color="white").pack(anchor="w", pady=(10, 5))

        # Forecast Container
        self.forecast_container = ctk.CTkFrame(self.container, fg_color="transparent")
        self.forecast_container.pack(fill="both", expand=True)
        self.forecast_items = []
        for _ in range(4):
            item = self._create_forecast_row(self.forecast_container)
            self.forecast_items.append(item)

        # Footer
        footer = ctk.CTkFrame(self.container, fg_color="transparent")
        footer.pack(fill="x", pady=(10, 0))
        
        self.update_btn = ctk.CTkButton(footer, text="Refresh", width=80, height=30, 
                                          fg_color="#3B8ED0", 
                                          hover_color="#36719F",
                                          command=self.refresh)
        self.update_btn.pack(side="left")
        
        self.unit_btn = ctk.CTkButton(footer, text="°C / °F", width=60, height=30,
                                        fg_color="#3B8ED0",
                                        hover_color="#36719F",
                                        command=self._toggle_unit)
        self.unit_btn.pack(side="right")

    def _create_stat_item(self, parent, emoji, title, value):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(side="left", expand=True)
        
        name_lbl = ctk.CTkLabel(frame, text=f"{emoji} {title}", font=("Segoe UI", 10), text_color="#CCCCCC")
        name_lbl.pack()
        
        val_lbl = ctk.CTkLabel(frame, text=value, font=("Segoe UI", 14, "bold"), text_color="white")
        val_lbl.pack()
        return val_lbl

    def _create_forecast_row(self, parent):
        row = ctk.CTkFrame(parent, fg_color="gray15", corner_radius=10)
        row.pack(fill="x", pady=2)
        
        day_lbl = ctk.CTkLabel(row, text="---", width=80, anchor="w", font=("Segoe UI", 12), text_color="white")
        day_lbl.pack(side="left", padx=10)
        
        ico_lbl = ctk.CTkLabel(row, text="", width=40, height=40)
        ico_lbl.pack(side="left")
        
        desc_lbl = ctk.CTkLabel(row, text="---", anchor="w", font=("Segoe UI", 12), text_color="#BBBBBB")
        desc_lbl.pack(side="left", padx=10, expand=True)
        
        temp_lbl = ctk.CTkLabel(row, text="--°", font=("Segoe UI", 14, "bold"), text_color="white")
        temp_lbl.pack(side="right", padx=10)
        
        return {"day": day_lbl, "icon": ico_lbl, "desc": desc_lbl, "temp": temp_lbl}

    def _get_owm_icon(self, icon_id, size=(100, 100)):
        if not icon_id: return None
        
        cache_file = os.path.join(ICON_PATH, f"{icon_id}.png")
        if not os.path.exists(cache_file):
            try:
                url = f"http://openweathermap.org/img/wn/{icon_id}@2x.png"
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                    with open(cache_file, 'wb') as f:
                        f.write(r.content)
            except Exception:
                pass

        if os.path.exists(cache_file):
            pil_img = Image.open(cache_file)
            return CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
        return None

    def refresh(self):
        weather = get_weather()
        if "error" in weather:
            self.city_label.configure(text="Error")
            self.desc_label.configure(text=weather["error"])
            return

        # Update Current Weather
        self.current_weather = weather
        self.city_label.configure(text=weather.get("name", "Unknown"))
        self.date_label.configure(text=datetime.datetime.now().strftime("%A, %d %b"))
        
        temp_c = weather["main"]["temp"]
        self.temp_label.configure(text=f"{round(temp_c)}°")
        self.desc_label.configure(text=weather["weather"][0]["description"].title())
        
        self.humidity_lbl.configure(text=f"{weather['main']['humidity']}%")
        self.wind_lbl.configure(text=f"{weather['wind']['speed']} m/s")
        self.aqi_lbl.configure(text=str(weather.get("aqi", "--")))

        # Update Background
        col1, col2 = get_gradient_bg(weather["weather"][0]["description"])
        bg_pil = create_rounded_gradient(self.winfo_width() or 320, self.winfo_height() or 480, col1, col2)
        bg_ctk = CTkImage(light_image=bg_pil, dark_image=bg_pil, size=(self.winfo_width() or 320, self.winfo_height() or 480))
        self.bg_label.configure(image=bg_ctk)
        
        # Update Icon
        icon_id = weather["weather"][0]["icon"]
        ctk_icon = self._get_owm_icon(icon_id)
        if ctk_icon:
            self.icon_label.configure(image=ctk_icon)

        # Update Forecast
        forecast_raw = get_forecast()
        daily = extract_daily_forecast(forecast_raw)
        for i, data in enumerate(daily):
            if i >= len(self.forecast_items): break
            item_ui = self.forecast_items[i]
            
            # Convert date to Day Name
            date_obj = datetime.datetime.strptime(data["date"], "%Y-%m-%d")
            day_name = date_obj.strftime("%A")
            
            item_ui["day"].configure(text=day_name)
            item_ui["desc"].configure(text=data["desc"])
            item_ui["temp"].configure(text=f"{round(data['temp'])}°")
            
            ico = self._get_owm_icon(data["icon"], size=(40, 40))
            if ico:
                item_ui["icon"].configure(image=ico)

        # Reschedule correctly
        self.after(300000, self.refresh) # 5 minutes

    def _toggle_unit(self):
        # Implementation of unit conversion toggle
        self.use_fahrenheit = not self.use_fahrenheit
        self.refresh() # Simpler to just refresh or manually update labels

    def _update_temps(self):
        # Helper to update all temp labels without API call
        pass

def create_ui():
    app = WeatherSnap()
    app.mainloop()

if __name__ == "__main__":
    create_ui()
