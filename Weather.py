import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- API Functions ---

def get_coordinates(city_name):
    """
    Fetches latitude and longitude for a given city name using Nominatim (OpenStreetMap).
    This is still used as weather.gov doesn't have a geocoding service.
    """
    url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json&limit=1"
    # IMPORTANT: Replace "your_email@example.com" with your actual email for the User-Agent.
    headers = {"User-Agent": "StreamlitWeatherDashboardApp/1.0 (your_email@example.com)"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Raise an exception for HTTP errors
        location_data = response.json()
        if location_data:
            location = location_data[0]
            lat = float(location['lat'])
            lon = float(location['lon'])
            display_name = location['display_name']
            return lat, lon, display_name
        else:
            st.warning("City not found. Please try a more specific name (e.g., 'Boston, MA'). Note: weather.gov data is primarily for the US.")
            return None, None, None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching coordinates: {e}")
        return None, None, None

def get_grid_data(lat, lon):
    """
    Fetches gridpoint metadata (WFO, gridX, gridY) from weather.gov for given lat/lon.
    """
    url = f"https://api.weather.gov/points/{lat},{lon}"
    # IMPORTANT: Replace "your_email@example.com" with your actual email for the User-Agent.
    headers = {"User-Agent": "StreamlitWeatherDashboardApp/1.0 (your_email@example.com)"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        point_data = response.json()

        # Extract WFO, gridX, gridY, and forecast URLs
        properties = point_data.get('properties', {})
        wfo = properties.get('cwa')
        grid_x = properties.get('gridX')
        grid_y = properties.get('gridY')

        # The API directly provides the hourly forecast URL
        hourly_forecast_url = properties.get('forecastHourly')

        return wfo, grid_x, grid_y, hourly_forecast_url
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching grid data from weather.gov: {e}. This usually means the location is outside the US or an API issue.")
        return None, None, None, None

def get_hourly_forecast_data(hourly_forecast_url):
    """
    Fetches hourly forecast data from weather.gov using the provided hourly forecast URL.
    """
    # IMPORTANT: Replace "your_email@example.com" with your actual email for the User-Agent.
    headers = {"User-Agent": "StreamlitWeatherDashboardApp/1.0 (your_email@example.com)"}
    try:
        response = requests.get(hourly_forecast_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching hourly forecast data: {e}")
        return None

# --- Streamlit App Layout ---

st.set_page_config(
    page_title="Weather.gov Dashboard (US Only)",
    page_icon="🇺🇸",
    layout="wide"
)

st.title("🇺🇸 Simple Weather Dashboard (Powered by weather.gov)")
st.info("This dashboard uses weather.gov data, which is primarily for the United States and its territories.")

# Input for city name
city = st.text_input("Enter city name (e.g., 'Boston, MA' or 'Los Angeles, CA'):", "Holliston, MA")

if city:
    lat, lon, display_name = get_coordinates(city)

    if lat is not None and lon is not None:
        st.subheader(f"Weather for {display_name.split(',')[0]}") # Display simplified city name

        wfo, grid_x, grid_y, hourly_forecast_url = get_grid_data(lat, lon)

        if wfo and grid_x and grid_y and hourly_forecast_url:
            hourly_forecast_raw = get_hourly_forecast_data(hourly_forecast_url)

            if hourly_forecast_raw and 'properties' in hourly_forecast_raw:
                forecast_periods = hourly_forecast_raw['properties']['periods']

                # --- Current Weather (extracted from first forecast period) ---
                st.header("Current/Upcoming Weather")
                if forecast_periods:
                    current_period = forecast_periods[0]

                    st.metric(label="Temperature", value=f"{current_period.get('temperature')}°{current_period.get('temperatureUnit', 'F')}", delta=None)
                    st.write(f"**Short Forecast:** {current_period.get('shortForecast')}")
                    st.write(f"**Detailed Forecast:** {current_period.get('detailedForecast')}")

                    wind_speed = current_period.get('windSpeed')
                    wind_direction = current_period.get('windDirection')
                    if wind_speed:
                        st.metric(label="Wind Speed", value=f"{wind_speed}", delta=None)
                    if wind_direction:
                        st.metric(label="Wind Direction", value=f"{wind_direction}", delta=None)

                    st.warning("Note: Current humidity is not directly provided by weather.gov hourly forecast for the current moment. You might find it in the detailed forecast text or via a separate observation station API call (more complex).")

                st.markdown("---")

                # --- Hourly Forecast ---
                st.header("Hourly Forecast")

                # Parse hourly data into a DataFrame
                hourly_data_list = []
                for period in forecast_periods:
                    # Convert start time to datetime object
                    start_time = pd.to_datetime(period['startTime'])

                    # Extract the numerical part of wind speed if it's a range
                    wind_speed_str = period.get('windSpeed', '0 mph')
                    wind_speed_value = 0.0 # Use float for calculations
                    if ' to ' in wind_speed_str:
                        try:
                            parts = wind_speed_str.split(' to ')
                            lower = float(parts[0].split(' ')[0])
                            upper = float(parts[1].split(' ')[0])
                            wind_speed_value = (lower + upper) / 2
                        except ValueError:
                            # Fallback if parsing fails, e.g., "G30KT" could be "30KT"
                            try:
                                wind_speed_value = float(wind_speed_str.split(' ')[0])
                            except ValueError:
                                pass # Keep as 0.0 if cannot parse
                    else:
                        try:
                            wind_speed_value = float(wind_speed_str.split(' ')[0])
                        except ValueError:
                            pass # Keep as 0.0 if cannot parse

                    hourly_data_list.append({
                        'Time': start_time,
                        'Temperature (°F)': period.get('temperature'),
                        'Wind Speed (mph)': wind_speed_value,
                        'Short Forecast': period.get('shortForecast')
                    })

                hourly_df = pd.DataFrame(hourly_data_list)

                if not hourly_df.empty:
                    # Set 'Time' as index for charting
                    hourly_df = hourly_df.set_index('Time')

                    selected_params = st.multiselect(
                        "Select parameters to view in forecast charts:",
                        ['Temperature (°F)', 'Wind Speed (mph)'],
                        default=['Temperature (°F)']
                    )

                    if selected_params:
                        for param in selected_params:
                            if param in hourly_df.columns:
                                st.subheader(f"{param} Hourly Forecast")
                                # Ensure the column is numeric for plotting
                                st.line_chart(hourly_df[param].astype(float))
                            else:
                                st.warning(f"Data for '{param}' not available in the forecast.")
                    else:
                        st.info("Please select at least one parameter to display the forecast charts.")

                    st.markdown("---")
                    st.subheader("Raw Hourly Forecast Data Table")
                    st.dataframe(hourly_df[['Temperature (°F)', 'Wind Speed (mph)', 'Short Forecast']])


            else:
                st.warning("Could not retrieve detailed forecast data for the specified location.")
        else:
            st.warning("Could not find weather grid information for the specified location. This may occur for locations outside the US or very remote areas.")
