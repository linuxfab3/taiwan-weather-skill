import urllib.request
import urllib.parse
import json
import os
import sys
import ssl
from datetime import datetime

def get_api_data(data_id, params, context):
    api_key = os.environ.get("CWA_API_KEY")
    if not api_key:
        print("Error: CWA_API_KEY environment variable not set.")
        sys.exit(1)

    base_url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/{data_id}"
    params["Authorization"] = api_key
    params["format"] = "JSON"

    query_string = urllib.parse.urlencode(params)
    full_url = f"{base_url}?{query_string}"

    try:
        req = urllib.request.Request(full_url)
        with urllib.request.urlopen(req, context=context) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        return {"success": "false", "message": str(e)}

def get_current_weather(city_name, context):
    data = get_api_data("O-A0003-001", {"StationName": city_name}, context)
    
    if data.get("success") == "true":
        records = data.get("records", {}).get("Station", [])
        if not records:
            return search_nearby_stations(city_name, context)
        return format_obs_output(records[0])
    return f"API Error: {data.get('message', 'Unknown error')}"

def get_forecast(city_name, context):
    data = get_api_data("F-D0047-091", {}, context)
    
    if data.get("success") == "true":
        records = data.get("records", {})
        locations_list = records.get("Locations") or records.get("locations") or []
        
        county_match = None
        norm_city = city_name.replace("台", "臺")
        
        for loc_group in locations_list:
            county = loc_group.get("LocationsName") or loc_group.get("locationsName") or ""
            norm_county = county.replace("台", "臺")
            
            locations = loc_group.get("Location") or loc_group.get("location") or []
            for loc in locations:
                town = loc.get("LocationName") or loc.get("locationName") or ""
                norm_town = town.replace("台", "臺")
                
                if norm_city == norm_town or norm_city == norm_county:
                    return format_forecast_output(loc, county)
                if norm_city in norm_town or norm_city in norm_county:
                    if not county_match:
                        county_match = (loc, county)
        
        if county_match:
            return format_forecast_output(county_match[0], county_match[1])
            
        return f"Could not find forecast for '{city_name}'."
    return f"API Error: {data.get('message', 'Unknown error')}"

def search_nearby_stations(city_name, context):
    data = get_api_data("O-A0003-001", {}, context)
    if data.get("success") == "true":
        stations = data.get("records", {}).get("Station", [])
        for s in stations:
            if city_name in s.get("StationName", "") or city_name in s.get("GeoInfo", {}).get("CountyName", ""):
                return format_obs_output(s)
        return f"Could not find weather data for '{city_name}'."
    return f"Search failed: {data.get('message')}"

def format_obs_output(station):
    name = station.get("StationName")
    county = station.get("GeoInfo", {}).get("CountyName", "")
    obs_time = station.get("ObsTime", {}).get("DateTime")
    elements = station.get("WeatherElement", {})
    
    temp = elements.get("AirTemperature", "N/A")
    humd = elements.get("RelativeHumidity", "N/A")
    weather = elements.get("Weather", "N/A")
    
    rain = elements.get("Now", {}).get("Precipitation", "0.0")
    if float(rain) < 0: rain = "0.0"
    
    return f"Weather for {name} ({county})\nTime: {obs_time}\nCondition: {weather}\nTemperature: {temp}°C\nHumidity: {humd}%\nPrecipitation: {rain}mm"

def format_forecast_output(location, county_name):
    loc_name = location.get("LocationName") or location.get("locationName")
    elements = location.get("WeatherElement") or location.get("weatherElement") or []
    
    forecast_data = {} # date -> {MinT, MaxT, Weather}
    
    for elem in elements:
        elem_name = (elem.get("ElementName") or elem.get("elementName") or "")
        
        target = None
        if "最高" in elem_name or "MaxT" in elem_name: target = "MaxT"
        elif "最低" in elem_name or "MinT" in elem_name: target = "MinT"
        elif "天氣現象" in elem_name or "Wx" in elem_name or "Weather" in elem_name: target = "Weather"
        
        if target:
            times = elem.get("Time") or elem.get("time") or []
            for t in times:
                start_str = t.get("StartTime") or t.get("startTime") or t.get("DataTime") or t.get("dataTime")
                if not start_str: continue
                
                date_key = start_str.split("T")[0] if "T" in start_str else start_str.split(" ")[0]
                if date_key not in forecast_data:
                    forecast_data[date_key] = {"MinT": None, "MaxT": None, "Weather": []}
                
                vals = t.get("ElementValue") or t.get("elementValue") or []
                if not vals: continue
                
                # CWA uses specific keys like 'MaxTemperature', 'MinTemperature', 'Weather'
                v_dict = vals[0]
                val = v_dict.get("value") or v_dict.get("Value")
                if val is None:
                    # Fallback to the first value in the dictionary
                    val = list(v_dict.values())[0]
                
                if val is None: val = ""
                
                try:
                    if target == "MinT" and val:
                        curr_min = forecast_data[date_key]["MinT"]
                        if curr_min is None or float(val) < float(curr_min):
                            forecast_data[date_key]["MinT"] = val
                    elif target == "MaxT" and val:
                        curr_max = forecast_data[date_key]["MaxT"]
                        if curr_max is None or float(val) > float(curr_max):
                            forecast_data[date_key]["MaxT"] = val
                    elif target == "Weather" and val:
                        if val not in forecast_data[date_key]["Weather"]:
                            forecast_data[date_key]["Weather"].append(val)
                except ValueError:
                    continue

    output = [f"7-Day Forecast for {loc_name} ({county_name})"]
    for date in sorted(forecast_data.keys()):
        d = forecast_data[date]
        weather = ", ".join(d["Weather"]) if d["Weather"] else "N/A"
        min_t = d["MinT"] if d["MinT"] is not None else "N/A"
        max_t = d["MaxT"] if d["MaxT"] is not None else "N/A"
        output.append(f"{date}: {min_t}°C - {max_t}°C, {weather}")
    
    return "\n".join(output)

if __name__ == "__main__":
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    context = ssl._create_unverified_context()
    
    args = sys.argv[1:]
    is_forecast = "--forecast" in args
    city = next((a for a in args if not a.startswith("--")), None)

    if not city:
        print("Usage: python get_weather.py <city_name> [--forecast]")
        sys.exit(1)

    if is_forecast:
        print(get_forecast(city, context))
    else:
        print(get_current_weather(city, context))
