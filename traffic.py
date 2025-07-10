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
    Maps_API_KEY = st.secrets["Maps_API_KEY"]
except KeyError:
    # Fallback to hardcoded key from your prompt for demonstration if not in secrets
    Maps_API_KEY = "AIzaSyADLZbllg9LIbNpsReyeAtwuEzKXJImpig"
    
# --- Pre-defined US Cities for Weather.gov (to avoid external geocoding) ---
# Add more cities as needed
US_CITIES_COORDS = {
    "Boston, MA": {"lat": 42.3601, "lon": -71.0589},
    "New York, NY": {"lat": 40.7128, "lon": -74.0060},
    "Washington, D.C.": {"lat": 38.9072, "lon": -77.0369},
    "Chicago, IL": {"lat": 41.8781, "lon": -87.6298},
    "Los Angeles, CA": {"lat": 34.0522, "lon": -118.2437},
    "Miami, FL": {"lat": 25.7617, "lon": -80.1918},
    "Seattle, WA": {"lat": 47.6062, "lon": -122.3321},
    "Denver, CO": {"lat": 39.7392, "lon": -104.9903},
    "Dallas, TX": {"lat": 32.7767, "lon": -96.7970},
    "Holliston, MA": {"lat": 42.1965, "lon": -71.4284}, # Based on earlier request
    "Somerville, MA": {"lat": 42.3876, "lon": -71.0995} # Current context location
}


# --- Weather.gov API Functions ---

# get_coordinates function is no longer needed as we use pre-defined coords

def get_grid_data(lat, lon):
    """
    Fetches gridpoint metadata (WFO, gridX, gridY) from weather.gov for given lat/lon.
    """
    url = f"https://api.weather.gov/points/{lat},{lon}"
    # IMPORTANT: Replace "your_email@example.com" with your actual email for the User-Agent.
    headers = {"User-Agent": "StreamlitUnifiedDashboard/1.0 (your_email@example.com)"}
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
    headers = {"User-Agent": "StreamlitUnifiedDashboard/1.0 (your_email@example.com)"}
    try:
        response = requests.get(hourly_forecast_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching hourly forecast data: {e}")
        return None

# --- Google Maps Directions API Functions (for Traffic) ---

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

# --- Sidebar for Weather Dashboard Inputs ---
st.sidebar.header("☀️ Weather Dashboard")
# Use a selectbox for pre-defined cities
selected_weather_city = st.sidebar.selectbox(
    "Select city for weather (US only):",
    options=list(US_CITIES_COORDS.keys()),
    index=list(US_CITIES_COORDS.keys()).index("Somerville, MA") # Default to Somerville, MA
)
get_weather_button = st.sidebar.button("Get Weather Forecast")


# --- Sidebar for Traffic & Directions Inputs ---
st.sidebar.markdown("---") # Separator
st.sidebar.header("🚦 Traffic & Driving Directions")
traffic_origin = st.sidebar.text_input("Origin (e.g., 'Worcester, MA'):", "Worcester, MA")
traffic_destination = st.sidebar.text_input("Destination (e.g., 'Boston, MA'):", "Boston, MA")
get_traffic_button = st.sidebar.button("Get Traffic & Directions")


# --- Main Content Area ---
st.write("---") # Separator for main content


if get_weather_button and selected_weather_city:
    st.header("☀️ Weather Information")
    with st.spinner(f"Fetching weather data for {selected_weather_city}..."):
        coords = US_CITIES_COORDS[selected_weather_city]
        lat = coords["lat"]
        lon = coords["lon"]

        wfo, grid_x, grid_y, hourly_forecast_url, city_name_display = get_grid_data(lat, lon)

        if wfo and grid_x and grid_y and hourly_forecast_url:
            hourly_forecast_raw = get_hourly_forecast_data(hourly_forecast_url)

            if hourly_forecast_raw and 'properties' in hourly_forecast_raw:
                forecast_periods = hourly_forecast_raw['properties']['periods']

                st.subheader(f"Weather for {city_name_display} (Pre-defined Lat: {lat:.4f}, Lon: {lon:.4f})")

                st.markdown("#### Current/Upcoming Weather")
                if forecast_periods:
                    current_period = forecast_periods[0]
                    st.metric(label="Temperature", value=f"{current_period.get('temperature')}°{current_period.get('temperatureUnit', 'F')}", delta=None)
                    st.write(f"**Short Forecast:** {current_period.get('shortForecast')}")
                    winds peed =
current_period.get('windSpeed')
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
                        key="weather_params_select"
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

if get_traffic_button and traffic_origin and traffic_destination:
    st.header("🚦 Traffic & Driving Directions")

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
            # You could also add a map here using the Google Maps Embed API or a static map image if you want to visualize the route
            # Note: Displaying interactive Google Maps routes typically requires more complex JavaScript/HTML embedding
        else:
            st.info("No detailed directions found.")

st.markdown("---")
st.write("Powered by weather.gov and Google Maps Directions API")

