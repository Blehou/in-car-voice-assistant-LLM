import requests

def get_location():
    """
    Retrieve approximate GPS coordinates based on the device's IP address.

    This function uses the ipinfo.io API to infer the user's current location 
    (latitude and longitude) based on their public IP address.
    Note: This method provides only an approximate location (city-level accuracy),
    not precise GPS coordinates.

    Returns:
        tuple or None: A tuple (latitude, longitude) as floats if successful,
                       or None if the request fails.
    """
    try:
        response = requests.get('https://ipinfo.io/json')
        data = response.json()
        latitude, longitude = map(float, data['loc'].split(','))
        return latitude, longitude
    
    except Exception as e:
        print(f"Error: {e}")
        return None


if __name__ == "__main__":
    latlon = get_location()
    print(latlon)