import json
import requests
import datetime
import re
    
def get_boston_alerts(latitude, longitude):
    """Fetches and displays weather alerts from the NWS API."""

    try:
        alerts_url = f"https://api.weather.gov/alerts/active?point={longitude},{latitude}"

        headers = {'User-Agent': 'BostonWeatherDashboard/1.0 (your_email@example.com)'}

        alerts_response = requests.get(alerts_url, headers=headers)
        alerts_response.raise_for_status()
        alerts_data = alerts_response.json()

        if alerts_data["features"]:
            print("\nWeather Alerts:")
            for alert in alerts_data["features"]:
                print(f"  {alert['properties']['headline']}: {alert['properties']['description']}")
        else: 
            print("\nNo active weather alerts.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching alert data: {e}")
    except json.JSONDecodeError as e:
        print(f"Error: Could not parse the weather data. {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def get_coordinates(location):
        """
        Gets latitude and longitude for a given location (city or zip code).
        This is a simplified example and might not be very accurate.
        For production, use a proper geocoding service.
        """
        # Example using a very basic lookup (replace with a real geocoding service)
        location_data = {
            "Boston": (42.3601, -71.0589),
            "New York": (40.7128, -74.0060),
            "Los Angeles": (34.0522, -118.2437),
            "02115": (42.3456, -71.0964)  # Example zip code
        }

        # Check if the input is a zip code using regex
        zip_code_match = re.fullmatch(r"\d{5}", location)

        if zip_code_match:
            # For simplicity, we'll use a fixed location for any zip code for now
            return (42.3456, -71.0964)  # Example location for zip codes
        elif location in location_data:
            return location_data[location]
        else:
         return None

def get_boston_forecast(latitude, longitude):
    """Fetches and displays a detailed forecast from the NWS API."""

    base_url = "https://api.weather.gov/points/"
    points_url = f"{base_url}{latitude},{longitude}"

    headers = {'User-Agent': 'BostonWeatherDashboard/1.0 (your_email@example.com)'}

    try:
        # Get the forecast URL from the points endpoint.
        points_response = requests.get(points_url, headers=headers)
        points_response.raise_for_status()
        points_data = points_response.json()
        forecast_url = points_data["properties"]["forecast"]

        # Get the forecast data.
        forecast_response = requests.get(forecast_url, headers=headers)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()

        # Print the forecast.
        print("Weather Forecast:")
        for period in forecast_data["properties"]["periods"]:
            print(f"  {period['name']}:")
            print(f"    Short Forecast: {period['shortForecast']}")
            print(f"    Temperature: {period.get('temperature', 'N/A')}°{period.get('temperatureUnit', '')}")
            print(f"    Wind: {period.get('windSpeed', 'N/A')} {period.get('windDirection', '')}")
            print(f"    Probability of Precipitation: {period.get('probabilityOfPrecipitation', {}).get('value', 'N/A')}%")
            print(f"    Detailed Forecast: {period['detailedForecast']}")
            print("-" * 20)  # Separator between periods

    except requests.exceptions.RequestException as e:
        print(f"Error fetching forecast data: {e}")
    except json.JSONDecodeError as e:
        print(f"Error: Could not parse the weather data. {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def main():
    location = input("Enter a city or zip code: ")
    coordinates = get_coordinates(location)

    if coordinates:
        latitude, longitude = coordinates
        print(f"Getting weather for {location} (Lat: {latitude}, Lon: {longitude})")
        get_boston_forecast(latitude, longitude)
        get_boston_alerts(latitude, longitude)
    else:
        print(f"Could not find coordinates for {location}.")

if __name__ == "__main__":
    main()
