# Libraries: 
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


# --- Tool definitions ---

def get_current_weather(city: str) -> dict:
    """
    Get the current weather for a city.

    Args:
        city: Name of the city.

    Returns:
        Current weather information.
    """

    # Mock implementation
    return {
        "city": city,
        "current": {
            "condition": "Sunny",
            "temp": 82,
            "humidity": 65
        }
    }
    
def get_forecast(city: str) -> dict:
    """
    Get the next 3-day weather forecast for a city .

    Args:
        city: Name of the city.

    Returns:
        Forecast information.
    """

    # Mock implementation for now
    return {
        "city": city,
        "forecast": [
            {"day": "Monday", "condition": "Sunny", "high": 82},
            {"day": "Tuesday", "condition": "Partly Cloudy", "high": 79},
            {"day": "Wednesday", "condition": "Rain", "high": 74},
        ]
    }

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

    Always provide clear, concise weather information
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

# 