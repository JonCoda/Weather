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
    page_title="Weather Dashboard (US
