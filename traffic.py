# main_app.py
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import re # Needed for cleaning HTML in directions

# --- Google Maps API Key ---
# IMPORTANT: For production apps, use Streamlit Secrets for security.
# Go to .streamlit/secrets.toml and add your key like:
# Maps_API_KEY = "YourActualAPIKeyHere"
# Then access it via st.secrets["Maps_API_KEY"]
try:
    Maps_API_KEY = st.secrets["AIzaSyADLZbllg9LIbNpsReyeAtwuEzKXJImpig"]
except KeyError:
    # Fallback to hardcoded key from your prompt for demonstration if not in secrets
    Maps_API_KEY = "AIzaSyADLZbllg9LIbNpsReyeAtwuEzKXJImpig"
    st.warning("Maps_API_KEY not found in Streamlit secrets. Using hardcoded key (NOT RECOMMENDED for production).")

# --- Weather.gov API Functions (Copied from 1_Weather_Dashboard.py) ---

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

        properties = point_data.get('properties', {})
        wfo = properties.get('cwa')
        grid_x = properties.get('gridX')
        grid_y = properties.get('gridY')
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

# --- Traffic & Directions Functions (Copied from 2_Traffic_Directions.py) ---

def get_traffic(origin, destination):
    """
    Fetches traffic information between an origin and destination using the Google Maps Directions API.
    """
    if not Maps_API_KEY:
        return {'error': 'Google Maps API Key not configured.'}

    url_no_traffic = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&key={Maps_API_KEY}"
    url_traffic = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&departure_time=now&key={Maps_API_KEY}"

    try:
        response_traffic = requests.get(url_traffic)
        response_traffic.raise_for_status()
        data_traffic = response_traffic.json()

        if data_traffic['status'] != 'OK':
            return {'error': f"API Error (Traffic): {data_traffic.get('error_message', data_traffic['status'])}"}
        if not data_traffic['routes']:
            return {'error': 'No routes found for the given origin and destination (with traffic).'}

        leg_traffic = data_traffic['routes'][0]['legs'][0]
        traffic_info = {
            'distance': leg_traffic.get('distance', {}).get('text', 'N/A'),
            'duration_in_traffic': leg_traffic.get('duration_in_traffic', {}).get('text', 'N/A')
        }

        response_no_traffic = requests.get(url_no_traffic)
        response_no_traffic.raise_for_status()
        data_no_traffic = response_no_traffic.json()

        if data_no_traffic['status'] != 'OK':
            return {'error': f"API Error (No Traffic): {data_no_traffic.get('error_message', data_no_traffic['status'])}"}
        if not data_no_traffic['routes']:
            return {'error': 'No routes found for the given origin and destination (no traffic).'}

        leg_no_traffic = data_no_traffic['routes'][0]['legs'][0]
        traffic_info['duration_no_traffic'] = leg_no_traffic.get('duration', {}).get('text', 'N/A')

        return traffic_info

    except requests.exceptions.RequestException as req_err:
        return {'error': f"Network or API request error: {req_err}"}
    except Exception as e:
        return {'error': f"An unexpected error occurred: {e}"}

def get_driving_directions(origin, destination):
    """
    Fetches driving directions between an origin and destination using the Google Maps Directions API.
    Returns a list of human-readable steps.
    """
    if not Maps_API_KEY:
        return {'error': 'Google Maps API Key not configured.'}

    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&key={Maps_API_KEY}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if data['status'] != 'OK':
            return {'error': f"API Error: {data.get('error_message', data['status'])}"}
        if not data['routes']:
            return {'error': 'No routes found for the given origin and destination.'}

        steps = []
        for step in data['routes'][0]['legs'][0]['steps']:
            clean_instruction = re.sub(r'<.*?>', '', step['html_instructions'])
            steps.append(f"- {clean_instruction} ({step['distance']['text']})")

        return {'steps': steps}

    except requests.exceptions.RequestException as req_err:
        return {'error': f"Network or API request error: {req_err}"}
    except Exception as e:
        return {'error': f"An unexpected error occurred: {e}"}

# --- Streamlit App Layout ---
st.set_page_config(
    page_title="Unified Geo-Information Dashboard",
    page_icon="🗺️",
    layout="wide"
)

st.title("🗺️ Unified Geo-Information Dashboard")
st.info("Remember to replace placeholder emails and API keys with your actual values for production use.")


# --- Sidebar for Weather Dashboard Inputs ---
st.sidebar.header("☀️ Weather Dashboard")
weather_city = st.sidebar.text_input("Enter city for weather (US only):", "Holliston, MA")
get_weather_button = st.sidebar.button("Get Weather")

# --- Sidebar for Traffic & Directions Inputs ---
st.sidebar.markdown("---") # Separator
st.sidebar.header("🚦 Traffic & Driving Directions")
traffic_origin = st.sidebar.text_input("Origin:", "Worcester, MA")
traffic_destination = st.sidebar.text_input("Destination:", "Boston, MA")
get_traffic_button = st.sidebar.button("Get Traffic & Directions")


# --- Main Content Area ---
st.write("---") # Separator for main content

if get_weather_button and weather_city:
    st.header("☀️ Weather Information")
    with st.spinner("Fetching weather data..."):
        lat, lon, display_name = get_coordinates(weather_city)

        if lat is not None and lon is not None:
            st.subheader(f"Weather for {display_name.split(',')[0]}")

            wfo, grid_x, grid_y, hourly_forecast_url = get_grid_data(lat, lon)

            if wfo and grid_x and grid_y and hourly_forecast_url:
                hourly_forecast_raw = get_hourly_forecast_data(hourly_forecast_url)

                if hourly_forecast_raw and 'properties' in hourly_forecast_raw:
                    forecast_periods = hourly_forecast_raw['properties']['periods']

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
                            key="weather_params_select" # Added unique key
                        )

                        if selected_params:
                            for param in selected_params:
                                if param in hourly_df.columns:
                                    st.write(f"**{param} Hourly Forecast**") # Using st.write for smaller title
                                    st.line_chart(hourly_df[param].astype(float))
                                else:
                                    st.warning(f"Data for '{param}' not available in the forecast.")
                        else:
                            st.info("Please select at least one parameter to display the forecast charts.")

                        st.markdown("---")
                        st.markdown("#### Raw Hourly Forecast Data Table")
                        st.dataframe(hourly_df[['Temperature (°F)', 'Wind Speed (mph)', 'Short Forecast']])

                    st.markdown("---")
                    st.markdown("#### City Location Map")
                    m = folium.Map(location=[lat, lon], zoom_start=10)
                    folium.Marker([lat, lon], popup=display_name).add_to(m)
                    st_folium(m, width=700, height=500, key="weather_map") # Added unique key

                else:
                    st.warning("Could not retrieve detailed forecast data for the specified location.")
            else:
                st.warning("Could not find weather grid information for the specified location. This may occur for locations outside the US or very remote areas.")
        else:
            st.info("Enter a city name above to get weather information.")

elif get_traffic_button and traffic_origin and traffic_destination:
    st.header("🚦 Traffic & Driving Directions")
    st.warning("Note: The Google Maps API Key provided in the prompt is **not** recommended for production use. Please use Streamlit secrets (`.streamlit/secrets.toml`) for secure storage.")

    st.subheader("Traffic Information")
    with st.spinner("Fetching traffic data..."):
        traffic_result = get_traffic(traffic_origin, traffic_destination)

        if 'error' in traffic_result:
            st.error(f"Error fetching traffic: {traffic_result['error']}")
        else:
            st.success(f"**Distance:** {traffic_result['distance']}")
            st.info(f"**Duration (Current Traffic):** {traffic_result['duration_in_traffic']}")
            st.write(f"**Duration (No Traffic):** {traffic_result['duration_no_traffic']}")
            st.markdown("---")

    st.subheader("Driving Directions")
    with st.spinner("Fetching directions..."):
        directions_result = get_driving_directions(traffic_origin, traffic_destination)

        if 'error' in directions_result:
            st.error(f"Error fetching directions: {directions_result['error']}")
        elif 'steps' in directions_result and directions_result['steps']:
            for step in directions_result['steps']:
                st.write(step)
        else:
            st.info("No detailed directions found.")

st.markdown("---")
st.write("Powered by Google Maps Directions API and weather.gov")
