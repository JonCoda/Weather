import requests
import os


def get_traffic(origin, destination):
    """
    Fetches traffic information between an origin and destination using the Google Maps Directions API.
    """
    api_key = "AIzaSyADLZbllg9LIbNpsReyeAtwuEzKXJImpig"
    if not api_key:
        return {'error': 'GOOGLE_MAPS_API_KEY not found in environment variables.'}

    url_no_traffic = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&key={api_key}"

    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&departure_time=now&key={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        leg = data['routes'][0]['legs'][0]
        traffic_info = {
            'distance': leg.get('distance', {}).get('text', 'N/A'),
            'duration_in_traffic': leg.get('duration_in_traffic', {}).get('text', 'N/A')}

        response_no_traffic = requests.get(url_no_traffic)
        response_no_traffic.raise_for_status()
        data_no_traffic = response_no_traffic.json()
        leg_no_traffic = data_no_traffic['routes'][0]['legs'][0]
        traffic_info['duration_no_traffic'] = leg_no_traffic.get('duration', {}).get('text', 'N/A')


        return traffic_info        

    except Exception as e:
        return {'error': str(e)}


print(get_traffic("40 Holly Lane, Holliston, MA", "61 innerbelt rd, somerville, MA"))
def get_driving_directions(origin, destination):
    """
    Fetches driving directions between an origin and destination using the Google Maps Directions API.
    """
    api_key = "AIzaSyADLZbllg9LIbNpsReyeAtwuEzKXJImpig"
    if not api_key:
        return {'error': 'GOOGLE_MAPS_API_KEY not found in environment variables.'}