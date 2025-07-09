import streamlit as st
import requests
import os

# --- Google Maps API Key ---
# IMPORTANT: For production apps, use Streamlit Secrets for security.
# Go to .streamlit/secrets.toml and add your key like:
# Maps_API_KEY = "YourActualAPIKeyHere"
# Then access it via st.secrets["Maps_API_KEY"]
# For this example, we'll use the key provided in your prompt,
# but strongly recommend using st.secrets for deployed apps.
Maps_API_KEY = "AIzaSyADLZbllg9LIbNpsReyeAtwuEzKXJImpig"

def get_traffic(origin, destination):
    """
    Fetches traffic information between an origin and destination using the Google Maps Directions API.
    """
    if not Maps_API_KEY:
        return {'error': 'Google Maps API Key not configured.'}

    # URL without traffic for base duration
    url_no_traffic = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&key={Maps_API_KEY}"
    # URL with traffic (departure_time=now)
    url_traffic = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&departure_time=now&key={Maps_API_KEY}"

    try:
        # Get duration with traffic
        response_traffic = requests.get(url_traffic)
        response_traffic.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
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

        # Get duration without traffic
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
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        if data['status'] != 'OK':
            return {'error': f"API Error: {data.get('error_message', data['status'])}"}
        if not data['routes']:
            return {'error': 'No routes found for the given origin and destination.'}

        # Extract steps from the first route's first leg
        steps = []
        for step in data['routes'][0]['legs'][0]['steps']:
            # The 'html_instructions' often contain HTML tags; we'll remove them for cleaner display
            import re
            clean_instruction = re.sub(r'<.*?>', '', step['html_instructions'])
            steps.append(f"- {clean_instruction} ({step['distance']['text']})")

        return {'steps': steps}

    except requests.exceptions.RequestException as req_err:
        return {'error': f"Network or API request error: {req_err}"}
    except Exception as e:
        return {'error': f"An unexpected error occurred: {e}"}

# --- Streamlit App Layout ---
st.set_page_config(page_title="Traffic & Directions App", layout="centered")

st.title("🚦 Traffic & Driving Directions")
st.markdown("Get real-time traffic conditions and step-by-step directions.")

st.sidebar.header("Inputs")
origin_input = st.sidebar.text_input("Origin (e.g., 'Worcester, MA')", "Worcester, MA")
destination_input = st.sidebar.text_input("Destination (e.g. 'Boston, MA')", "Boston, MA")

if st.sidebar.button("Get Info"):
    if not origin_input or not destination_input:
        st.error("Please enter both origin and destination.")
    else:
        st.subheader("Traffic Information")
        with st.spinner("Fetching traffic data..."):
            traffic_result = get_traffic(origin_input, destination_input)

            if 'error' in traffic_result:
                st.error(f"Error fetching traffic: {traffic_result['error']}")
            else:
                st.success(f"**Distance:** {traffic_result['distance']}")
                st.info(f"**Duration (Current Traffic):** {traffic_result['duration_in_traffic']}")
                st.write(f"**Duration (No Traffic):** {traffic_result['duration_no_traffic']}")
                st.markdown("---")

        st.subheader("Driving Directions")
        with st.spinner("Fetching directions..."):
            directions_result = get_driving_directions(origin_input, destination_input)

            if 'error' in directions_result:
                st.error(f"Error fetching directions: {directions_result['error']}")
            elif 'steps' in directions_result and directions_result['steps']:
                for step in directions_result['steps']:
                    st.write(step)
            else:
                st.info("No detailed directions found.")

st.markdown("---")
st.write("Powered by Google Maps Directions API")
