import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- API Functions ---

# Removed get_coordinates function as we are now taking lat/lon directly

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

        properties = point_data.get('properties', {})
        wfo = properties.get('cwa')
        grid_x = properties.get('gridX')
        grid_y = properties.get('gridY')
        hourly_forecast_url = properties.get('forecastHourly')

        # NWS API returns a specific 'relativeLocation' that includes city/state
        location_properties = properties.get('relativeLocation', {}).get('properties', {})
        city_name_display = f"{location_properties.get('city', 'Unknown City')}, {location_properties.get('state', 'Unknown State')}"

        return wfo, grid_x, grid_y, hourly_forecast_url, city_name_display
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching grid data from weather.gov: {e}. This usually means the location is outside the US or an API issue.")
        return None, None, None, None, None

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
    page_title="Weather Dashboard (US Only - Lat/Lon Input)",
    page_icon="☀️",
    layout="wide"
)

st.title("☀️ Weather Dashboard (Powered by weather.gov - Lat/Lon Input)")
st.info("This dashboard directly uses weather.gov data by requiring Latitude and Longitude. Weather.gov data is primarily for the United States and its territories.")

# --- Sidebar for Weather Dashboard Inputs ---
st.sidebar.header("Enter Location (Latitude & Longitude)")
# Provide common US city coordinates as defaults or examples
default_lat = 42.3876 # Somerville, MA
default_lon = -71.0995 # Somerville, MA

try:
    latitude_input = st.sidebar.number_input("Latitude:", value=default_lat, format="%.4f")
    longitude_input = st.sidebar.number_input("Longitude:", value=default_lon, format="%.4f")
except Exception:
    st.sidebar.error("Please enter valid numerical values for Latitude and Longitude.")
    latitude_input = None
    longitude_input = None


get_weather_button = st.sidebar.button("Get Weather")

# --- Main Content Area for Weather Results ---

if get_weather_button and latitude_input is not None and longitude_input is not None:
    st.header("Weather Information")
    with st.spinner("Fetching weather data..."):
        # We no longer need get_coordinates
        # Direct call to get_grid_data with user provided lat/lon
        wfo, grid_x, grid_y, hourly_forecast_url, city_name_display = get_grid_data(latitude_input, longitude_input)

        if wfo and grid_x and grid_y and hourly_forecast_url:
            hourly_forecast_raw = get_hourly_forecast_data(hourly_forecast_url)

            if hourly_forecast_raw and 'properties' in hourly_forecast_raw:
                forecast_periods = hourly_forecast_raw['properties']['periods']

                st.subheader(f"Weather for {city_name_display} (Lat: {latitude_input:.4f}, Lon: {longitude_input:.4f})")

                st.markdown("#### Current/Upcoming Weather")
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

                st.markdown("#### Hourly Forecast Charts")
                hourly_data_list = []
                for period in forecast_periods:
                    start_time = pd.to_datetime(period['startTime'])
                    wind_speed_str = period.get('windSpeed', '0 mph')
                    wind_speed_value = 0.0
                    if ' to ' in wind_speed_str:
                        try:
                            parts = wind_speed_str.split(' to ')
                            lower = float(parts[0].split(' ')[0])
                            upper = float(parts[1].split(' ')[0])
                            wind_speed_value = (lower + upper) / 2
                        except ValueError:
                            try:
                                wind_speed_value = float(wind_speed_str.split(' ')[0])
                            except ValueError:
                                pass
                    else:
                        try:
                            wind_speed_value = float(wind_speed_str.split(' ')[0])
                        except ValueError:
                            pass

                    hourly_data_list.append({
                        'Time': start_time,
                        'Temperature (°F)': period.get('temperature'),
                        'Wind Speed (mph)': wind_speed_value,
                        'Short Forecast': period.get('shortForecast')
                    })

                hourly_df = pd.DataFrame(hourly_data_list)
                if not hourly_df.empty:
                    hourly_df = hourly_df.set_index('Time')

                    selected_params = st.multiselect(
                        "Select parameters to view in forecast charts:",
                        ['Temperature (°F)', 'Wind Speed (mph)'],
                        default=['Temperature (°F)'],
                        key="weather_params_select" # Unique key
                    )

                    if selected_params:
                        for param in selected_params:
                            if param in hourly_df.columns:
                                st.write(f"**{param} Hourly Forecast**")
                                st.line_chart(hourly_df[param].astype(float))
                            else:
                                st.warning(f"Data for '{param}' not available in the forecast.")
                    else:
                        st.info("Please select at least one parameter to display the forecast charts.")

                    st.markdown("---")
                    st.markdown("#### Raw Hourly Forecast Data Table")
                    st.dataframe(hourly_df[['Temperature (°F)', 'Wind Speed (mph)', 'Short Forecast']])

                st.markdown("---")
                st.markdown("#### Location Map")
                # Use the provided lat/lon for the map
                m = folium.Map(location=[latitude_input, longitude_input], zoom_start=10)
                # Display the derived city_name_display on the marker
                folium.Marker([latitude_input, longitude_input], popup=city_name_display).add_to(m)
                st_folium(m, width=700, height=500, key="weather_map")

            else:
                st.warning("Could not retrieve detailed forecast data for the specified location.")
        else:
            st.warning("Could not find weather grid information for the specified location. This may occur for locations outside the US or very remote areas.")
else:
    st.info("Enter Latitude and Longitude in the sidebar and click 'Get Weather' to see the forecast.")

st.markdown("---")
st.write("Powered by weather.gov")
