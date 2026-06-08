import asyncio
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import os 
import httpx

from dotenv import load_dotenv

load_dotenv()
#model="anthropic/claude-opus-4-6"

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")


# --- Tool definitions ---

def get_current_weather(city: str) -> dict:
    """
    Get the current weather for a city.

    Args:
        city: Name of the city.

    Returns:
        Current weather information.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    
    params = {
        "q": city,
        "appid": api_key,
        "units": "imperial"
    }
    
    try:
        response = httpx.get(base_url, params=params, timeout=5)
        data = response.json()
        return {
            "city": data["name"],
            "condition": data["weather"][0]["description"],
            "temp": data["main"]["temp"],
            "humidity": data["main"]["humidity"]
        }
    except Exception as e:
        return {"error": str(e)}

def get_forecast(city: str) -> dict:
    """
    Get the next 3-day weather forecast for a city.

    Args:
        city: Name of the city.

    Returns:
        Forecast information.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    base_url = "https://api.openweathermap.org/data/2.5/forecast"
    
    params = {
        "q": city,
        "appid": api_key,
        "units": "imperial",
        "cnt": 24  # 8 forecasts per day, 3 days = 24
    }
    
    try:
        response = httpx.get(base_url, params=params, timeout=5)
        data = response.json()
        
        # Extract 3-day forecast
        forecasts = []
        for i in range(0, min(24, len(data["list"])), 8):
            forecast = data["list"][i]
            forecasts.append({
                "day": forecast["dt_txt"],
                "condition": forecast["weather"][0]["description"],
                "temp": forecast["main"]["temp"],
                "humidity": forecast["main"]["humidity"]
            })
        
        return {
            "city": data["city"]["name"],
            "forecast": forecasts
        }
    except Exception as e:
        return {"error": str(e)}


# --- Agent with tools --- 
weather_agent = Agent(
    name="weather_agent",
    model="anthropic/claude-opus-4-6",
    description="Weather assistant that provides current conditions and forecasts",
    instruction="""
    You help users with weather questions.
    
    Use:
    - get_current_weather for current conditions
    - get_forecast for future forecasts
    
    Always provide clear, concise weather information.
    """,
    tools=[get_current_weather, get_forecast],
)


# --- Set up runner and session service ---
session_service = InMemorySessionService()
runner = Runner(
    agent=weather_agent,
    app_name="weather_news",
    session_service=session_service,
)


# --- Execute query function ---
async def run_query(query: str) -> str:
    session = await session_service.create_session(
        app_name="weather_news",
        user_id="user_001",
    )
    message = types.Content(
        role="user",
        parts=[types.Part(text=query)],
    )
    final_response = ""
    async for event in runner.run_async(
        user_id="user_001",
        session_id=session.id,
        new_message=message,
    ):
        if event.is_final_response():
            final_response = event.content.parts[0].text
    return final_response


if __name__ == "__main__":
    result = asyncio.run(run_query("What is the weather today in Chicago and what will be the weather in the next 3 days?"))
    print(result)