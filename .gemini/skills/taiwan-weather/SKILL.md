---
name: taiwan-weather
description: Fetches current weather data for cities in Taiwan using the CWA Open Data API. Use this when users ask for real-time weather information in Taiwan locations like Taipei, Tainan, or Taichung.
---

# Taiwan Weather Skill

This skill allows you to retrieve real-time weather observation data from the Taiwan Central Weather Administration (CWA).

## Prerequisites

- **API Key**: You must have a CWA Open Data API key. Get it from [https://opendata.cwa.gov.tw/user/authkey](https://opendata.cwa.gov.tw/user/authkey).
- **Environment Variable**: Set your API key in the `CWA_API_KEY` environment variable.

## Usage

When a user asks for weather in a Taiwan city, execute the bundled Python script:

```bash
python scripts/get_weather.py <city_name>
```

### Examples

- "What's the weather in Taipei?" -> `python scripts/get_weather.py 臺北`
- "Tainan weather check" -> `python scripts/get_weather.py 臺南`

### Implementation Details

- **Script**: `scripts/get_weather.py`
- **API Endpoint**: `O-A0003-001` (Automated Weather Station Observation)
- **Dependencies**: None (Uses only Python standard libraries `urllib`, `json`, `os`, `sys`).
