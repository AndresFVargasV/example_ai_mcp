from mcp.server.fastmcp import FastMCP
import httpx
from typing import Any, Dict, Optional

# Initialize FastMCP server
mcp = FastMCP("weather")

# Get constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = 'weather-app/1.0'

# Tools for execution
@mcp.tool()
async def getAlerts(state: str) -> str:
    """Get weather alerts for a US state."""
    
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await makeNwsRequest(url)
    
    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."
    
    if not data["features"]:
        return "No active alerts for this state."

    alerts = [formatAlert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)

@mcp.tool()
async def getForecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location"""
    
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await makeNwsRequest(points_url)
    
    if not points_data:
        return "Unable to fetch forecast data for this location."

    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await makeNwsRequest(forecast_url)
    
    if not forecast_data:
        return "Unable to fetch detailed forecast."
    
    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = f"""
            {period['name']}:
            Temperature: {period['temperature']}°{period['temperatureUnit']}
            Wind: {period['windSpeed']} {period['windDirection']}
            Forecast: {period['detailedForecast']}
            """
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)
    
async def makeNwsRequest(url: str) -> Optional[Dict[str, Any]]:
    """Make a request to the NWS API with proper error handling"""
    
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error making request to {url}: {str(e)}")
            return None
        
def formatAlert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    
    props = feature["properties"]
    return f"""
    Event: {props.get('event', 'Unknown')}
    Area: {props.get('areaDesc', 'Unknown')}
    Severity: {props.get('severity', 'Unknown')}
    Description: {props.get('description', 'No description available')}
    Instructions: {props.get('instruction', 'No specific instructions provided')}
    """

if __name__ == "__main__":
    import logging
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize and run the server
    print("Iniciando servidor MCP para información meteorológica...")
    mcp.run()