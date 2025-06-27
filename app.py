import streamlit as st
from dotenv import load_dotenv
import os
import plotly.graph_objects as go
from datetime import datetime

from utils.weather_aqi_api import get_coordinates, get_weather_data, get_aqi_data
from utils.city_suggestions import get_city_suggestions
from utils.background_logic import get_background_style
from utils.motivational import get_motivational_message

# Load environment variables
load_dotenv()
st.set_page_config(page_title="Smart Weather App", layout="centered")

# Initialize session state for city input if not already set
if 'city_input' not in st.session_state:
    st.session_state.city_input = "Tokyo"

if 'search_performed' not in st.session_state:
    st.session_state.search_performed = False

# Theme toggle
dark_mode = st.toggle("🌗 Toggle Dark Mode", value=False)

# Base styling based on theme
if dark_mode:
    base_bg = "linear-gradient(to top, #0f2027, #203a43, #2c5364)"  # Dark mode background
    text_color = "#f5f5f5"
else:
    base_bg = "linear-gradient(to top, #dfe9f3 0%, white 100%)"
    text_color = "#1a1a1a"

st.markdown(f"""
    <style>
    .main {{
        background: {base_bg};
        font-family: 'Segoe UI', sans-serif;
        color: {text_color};
    }}
    </style>
""", unsafe_allow_html=True)

# --- Search input and suggestions ---
def on_search_click():
    st.session_state.city_input = st.session_state.city_query
    st.session_state.search_performed = True

# Default city query to the last city input
city_query = st.text_input(
    "📍 Enter City Name", 
    value=st.session_state.city_input,
    key="city_query"
)

search_button = st.button("Search", on_click=on_search_click)

# Get city suggestions
if city_query:
    suggestions = get_city_suggestions(city_query)
    if suggestions:
        selected_suggestion = st.selectbox("🔍 Suggestions", [""] + suggestions)
        if selected_suggestion:
            st.session_state.city_input = selected_suggestion
            st.session_state.search_performed = True

# --- Weather Logic ---
if st.session_state.city_input:
    # Display a loading message
    with st.spinner(f"Fetching weather data for {st.session_state.city_input}..."):
        lat, lon, city, country = get_coordinates(st.session_state.city_input)

        if lat is None:
            st.error(f"City not found: '{st.session_state.city_input}'. Please try a different search.")
        else:
            weather_data = get_weather_data(lat, lon)
            aqi_data = get_aqi_data(lat, lon)

            if not weather_data or not weather_data.get("main"):
                st.error("Weather data could not be retrieved. Please check your API key or try again later.")
            else:
                temp = weather_data["main"]["temp"]
                desc = weather_data["weather"][0]["description"].title()
                icon = weather_data["weather"][0]["icon"]

                # --- Dynamic weather-based background override ---
                style = get_background_style(desc)
                themed_bg = style["background"] if not dark_mode else base_bg

                st.markdown(f"""
                    <style>
                    .main {{
                        background: {themed_bg};
                        font-family: 'Segoe UI', sans-serif;
                        color: {text_color};
                    }}
                    </style>
                """, unsafe_allow_html=True)

                # --- Weather Display ---
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.image(f"http://openweathermap.org/img/wn/{icon}@2x.png", width=100)
                with col2:
                    st.markdown(f"## 🌤️ {temp}°C — {desc}")
                    st.markdown(f"**Location**: {city}, {country}")
                
                message = get_motivational_message(desc)
                st.markdown(f"> **{message}**")

                # --- AQI Display ---
                try:
                    aqi_index = aqi_data["list"][0]["main"]["aqi"]
                    components = aqi_data["list"][0]["components"]
                    
                    # Extract individual pollutant values
                    co = components.get("co", "N/A")
                    no2 = components.get("no2", "N/A")
                    o3 = components.get("o3", "N/A")
                    pm10 = components.get("pm10", "N/A")
                    pm2_5 = components.get("pm2_5", "N/A")
                    so2 = components.get("so2", "N/A")
                    
                    # Calculate approximate AQI number (rough estimate based on EPA standards)
                    aqi_number = None
                    if pm2_5 != "N/A":
                        # Rough estimation based on PM2.5 concentration
                        if pm2_5 <= 12:
                            aqi_number = int(50 * pm2_5 / 12)
                        elif pm2_5 <= 35.4:
                            aqi_number = int(50 + (50 * (pm2_5 - 12) / (35.4 - 12)))
                        elif pm2_5 <= 55.4:
                            aqi_number = int(100 + (50 * (pm2_5 - 35.4) / (55.4 - 35.4)))
                        elif pm2_5 <= 150.4:
                            aqi_number = int(150 + (50 * (pm2_5 - 55.4) / (150.4 - 55.4)))
                        elif pm2_5 <= 250.4:
                            aqi_number = int(200 + (100 * (pm2_5 - 150.4) / (250.4 - 150.4)))
                        else:
                            aqi_number = int(300 + (200 * (pm2_5 - 250.4) / (350.4 - 250.4)))
                            if aqi_number > 500:
                                aqi_number = 500
                    
                    aqi_map = {
                        1: ("Good", "🟢", "0-50"),
                        2: ("Fair", "🟡", "51-100"),
                        3: ("Moderate", "🟠", "101-150"),
                        4: ("Poor", "🔴", "151-200"),
                        5: ("Very Poor", "🟣", "201-300+")
                    }
                    aqi_text, aqi_icon, aqi_range = aqi_map.get(aqi_index, ("Unknown", "⚪", "N/A"))
                    
                    # Display overall AQI
                    if aqi_number is not None:
                        st.markdown(f"### Air Quality Index: {aqi_icon} {aqi_number} - {aqi_text}")
                    else:
                        st.markdown(f"### Air Quality Index: {aqi_icon} {aqi_text} (Level {aqi_index}, Range {aqi_range})")
                    
                    # Display specific pollutant values in a two-column layout
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("#### Pollutant Values:")
                        st.markdown(f"- CO: **{co} μg/m³**")
                        st.markdown(f"- NO₂: **{no2} μg/m³**")
                        st.markdown(f"- O₃: **{o3} μg/m³**")
                    
                    with col2:
                        st.markdown("&nbsp;")  # Add some spacing to align with the first column
                        st.markdown(f"- PM10: **{pm10} μg/m³**")
                        st.markdown(f"- PM2.5: **{pm2_5} μg/m³**")
                        st.markdown(f"- SO₂: **{so2} μg/m³**")
                        
                except (KeyError, IndexError, TypeError) as e:
                    st.info(f"AQI data not available for this location. Error: {e}")

                # --- Hourly Forecast ---
                st.markdown("### ⏱️ Hourly Forecast (Next 24 Hours)")
                hourly = weather_data.get("hourly", [])
                if hourly:
                    # Create 4 columns for forecast display
                    cols = st.columns(4)
                    for i, hour_data in enumerate(hourly[:8]):  # Display up to 8 entries
                        try:
                            col_idx = i % 4  # Determine which column to use
                            with cols[col_idx]:
                                hour_temp = hour_data["main"]["temp"]
                                hour_icon = hour_data["weather"][0]["icon"]
                                hour_desc = hour_data["weather"][0]["description"].title()
                                hour_time = datetime.fromtimestamp(hour_data["dt"]).strftime("%I %p")

                                st.markdown(f"**{hour_time}**")
                                st.image(f"http://openweathermap.org/img/wn/{hour_icon}.png", width=40)
                                st.markdown(f"{hour_temp}°C — {hour_desc}")
                        except KeyError as e:
                            st.error(f"Error displaying hour {i}: {e}")
                            continue
                else:
                    st.info("Hourly forecast data not available.")

                # --- Additional Weather Details ---
                st.markdown("---")
                st.markdown("### 🧭 Additional Weather Details")
                
                col1, col2 = st.columns(2)
                with col1:
                    humidity = weather_data["main"]["humidity"]
                    pressure = weather_data["main"]["pressure"]
                    st.markdown(f"- 💧 Humidity: **{humidity}%**")
                    st.markdown(f"- 🔽 Pressure: **{pressure} hPa**")
                
                with col2:
                    wind_speed = weather_data["wind"]["speed"]
                    st.markdown(f"- 🌬️ Wind Speed: **{wind_speed} m/s**")
                    
                    # Check if sunrise/sunset data is available
                    if "sys" in weather_data and "sunrise" in weather_data["sys"] and "sunset" in weather_data["sys"]:
                        sunrise = weather_data["sys"]["sunrise"]
                        sunset = weather_data["sys"]["sunset"]

                        def convert_to_local_time(utc_time, tz_offset):
                            return datetime.utcfromtimestamp(utc_time + tz_offset).strftime("%I:%M %p")

                        tz_offset = weather_data.get("timezone", 0)
                        sunrise_local = convert_to_local_time(sunrise, tz_offset)
                        sunset_local = convert_to_local_time(sunset, tz_offset)
                        
                        st.markdown(f"- 🌅 Sunrise: **{sunrise_local}**")
                        st.markdown(f"- 🌇 Sunset: **{sunset_local}**")

                # --- Hourly Temperature Plot ---
                if hourly:
                    st.markdown("---")
                    st.markdown("### 📈 Temperature Forecast (Next 24 Hours)")

                    try:
                        times = [datetime.fromtimestamp(hour["dt"]).strftime("%I %p") for hour in hourly[:8]]
                        temps = [hour["main"]["temp"] for hour in hourly[:8]]

                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=times,
                            y=temps,
                            mode='lines+markers',
                            line=dict(color='royalblue', width=2),
                            marker=dict(size=6),
                            name="Temp (°C)"
                        ))

                        fig.update_layout(
                            xaxis_title="Time",
                            yaxis_title="Temperature (°C)",
                            xaxis=dict(tickmode="linear"),
                            margin=dict(l=20, r=20, t=40, b=20),
                            height=400,
                            hovermode="x unified",
                            template="plotly_dark" if dark_mode else "plotly_white"
                        )

                        st.plotly_chart(fig, use_container_width=True)
                    except (KeyError, IndexError, TypeError) as e:
                        st.info(f"Unable to display temperature chart with the available data: {e}")