import urllib.request
import urllib.parse
import json
import os
import sys
import ssl

def get_weather(city_name):
    api_key = os.environ.get("CWA_API_KEY")
    if not api_key:
        print("Error: CWA_API_KEY environment variable not set.")
        sys.exit(1)

    # Use O-A0003-001 for observation data
    # StationName is the key to filter
    base_url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001"
    
    params = {
        "Authorization": api_key,
        "format": "JSON",
        "StationName": city_name
    }

    query_string = urllib.parse.urlencode(params)
    full_url = f"{base_url}?{query_string}"

    # Bypass SSL verification if needed
    context = ssl._create_unverified_context()

    try:
        req = urllib.request.Request(full_url)
        with urllib.request.urlopen(req, context=context) as response:
            data = json.loads(response.read().decode("utf-8"))
            
            if data.get("success") == "true":
                records = data.get("records", {}).get("Station", [])
                if not records:
                    # Try a broader search if exact match fails
                    print(f"No exact match for station '{city_name}'. Searching...")
                    return search_nearby_stations(api_key, city_name, context)
                
                return format_output(records[0])
            else:
                return f"API Error: {data.get('message', 'Unknown error')}"

    except Exception as e:
        return f"Request failed: {str(e)}"

def search_nearby_stations(api_key, city_name, context):
    # Fetch all stations and find one that matches the city name or is in the city
    base_url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001"
    params = {
        "Authorization": api_key,
        "format": "JSON"
    }
    query_string = urllib.parse.urlencode(params)
    full_url = f"{base_url}?{query_string}"

    try:
        req = urllib.request.Request(full_url)
        with urllib.request.urlopen(req, context=context) as response:
            data = json.loads(response.read().decode("utf-8"))
            stations = data.get("records", {}).get("Station", [])
            
            # Match by StationName containing the input or CountyName
            match = None
            for s in stations:
                if city_name in s.get("StationName", "") or city_name in s.get("GeoInfo", {}).get("CountyName", ""):
                    match = s
                    break
            
            if match:
                return format_output(match)
            else:
                return f"Could not find weather data for '{city_name}'."
    except Exception as e:
        return f"Search failed: {str(e)}"

def format_output(station):
    name = station.get("StationName")
    county = station.get("GeoInfo", {}).get("CountyName", "")
    obs_time = station.get("ObsTime", {}).get("DateTime")
    elements = station.get("WeatherElement", {})
    
    temp = elements.get("AirTemperature", "N/A")
    humd = elements.get("RelativeHumidity", "N/A")
    weather = elements.get("Weather", "N/A")
    
    # Handle CWA special values (e.g., -990.0 means no rain or data)
    rain = elements.get("Now", {}).get("Precipitation", "0.0")
    if float(rain) < 0:
        rain = "0.0"
    
    output = [
        f"Weather for {name} ({county})",
        f"Time: {obs_time}",
        f"Condition: {weather}",
        f"Temperature: {temp}°C",
        f"Humidity: {humd}%",
        f"Precipitation (Current): {rain}mm"
    ]
    return "\n".join(output)

if __name__ == "__main__":
    # Force UTF-8 for Windows console
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    if len(sys.argv) < 2:
        print("Usage: python get_weather.py <city_name>")
        sys.exit(1)
    
    city = sys.argv[1]
    print(get_weather(city))
