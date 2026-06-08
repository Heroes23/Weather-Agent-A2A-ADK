import asyncio
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import os 
import httpx

from dotenv import load_dotenv

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# --- Tool definitions for Weather Agent ---

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
        "cnt": 24
    }
    
    try:
        response = httpx.get(base_url, params=params, timeout=5)
        data = response.json()
        
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


# --- Tool definitions for Activity Agent ---

def get_activities(weather_condition: str, temperature: float) -> dict:
    """
    Get activity recommendations based on weather.

    Args:
        weather_condition: Description of weather (e.g., "Sunny", "Rainy")
        temperature: Current temperature in Fahrenheit

    Returns:
        List of recommended activities.
    """
    activities = {
        "Sunny": ["hiking", "beach", "outdoor sports", "picnic"],
        "Cloudy": ["sightseeing", "outdoor photography", "walking"],
        "Rainy": ["indoor museum", "shopping", "movie", "reading"],
        "Snowy": ["skiing", "ice skating", "snowboarding"],
    }
    
    # Simple mapping
    condition_key = weather_condition.split()[0].capitalize() if weather_condition else "Cloudy"
    recommended = activities.get(condition_key, ["indoor activities", "walking"])
    
    # Adjust for temperature
    if temperature > 85:
        recommended.extend(["water park", "swimming"])
    elif temperature < 32:
        recommended.extend(["hot chocolate", "warming up"])
    
    return {
        "condition": weather_condition,
        "temperature": temperature,
        "recommended_activities": recommended
    }


# --- AGENT 1: Weather Agent ---
weather_agent = Agent(
    name="weather_agent",
    model="anthropic/claude-opus-4-6",
    description="Retrieves real-time weather data and forecasts for any city",
    instruction="""
    You are a weather specialist. 
    
    Use these tools to get weather information:
    - get_current_weather: for real-time conditions
    - get_forecast: for 3-day forecasts
    
    Provide clear, accurate weather data.
    """,
    tools=[get_current_weather, get_forecast],
)


# --- AGENT 2: Activity Recommendation Agent ---
activity_agent = Agent(
    name="activity_agent",
    model="anthropic/claude-opus-4-6",
    description="Recommends activities based on weather conditions",
    instruction="""
    You are an activity advisor.
    
    Use the get_activities tool to recommend activities based on:
    - Weather condition (sunny, rainy, snowy, etc.)
    - Temperature
    
    Suggest fun, relevant activities for the given weather.
    """,
    tools=[get_activities],
)


# --- AGENT 3: Orchestrator (A2A Coordinator) ---
weather_tool = AgentTool(agent=weather_agent)
activity_tool = AgentTool(agent=activity_agent)

orchestrator = Agent(
    name="orchestrator",
    model="anthropic/claude-opus-4-6",
    description="Coordinates weather and activity agents to provide comprehensive travel/activity planning",
    instruction="""
    You are a travel and activity planning orchestrator.
    
    To answer user queries:
    1. First, use the weather_agent tool to get weather data for the requested city
    2. Then, use the activity_agent tool to get activity recommendations based on that weather
    3. Synthesize both pieces of information into a comprehensive plan
    
    Always cite specific temperatures, conditions, and activities.
    """,
    tools=[weather_tool, activity_tool],
)


# --- Set up runner and session service ---
session_service = InMemorySessionService()
runner = Runner(
    agent=orchestrator,
    app_name="weather_activity_planning",
    session_service=session_service,
)


# --- Execute query function ---
async def run_query(query: str) -> str:
    session = await session_service.create_session(
        app_name="weather_activity_planning",
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


# --- AGENT CARDS ---
AGENT_CARDS = """
=== A2A WEATHER & ACTIVITY PLANNING SYSTEM ===

AGENT 1: Weather Agent
  Name: weather_agent
  Role: Retrieves real-time weather data
  Tools: get_current_weather, get_forecast
  Responsibility: Fetch accurate weather information from OpenWeather API
  Input: City name
  Output: Current conditions and 3-day forecast

AGENT 2: Activity Agent
  Name: activity_agent
  Role: Recommends activities based on weather
  Tools: get_activities
  Responsibility: Suggest fun activities matching weather conditions
  Input: Weather condition and temperature
  Output: List of recommended activities

AGENT 3: Orchestrator
  Name: orchestrator
  Role: Coordinates agents and synthesizes results
  Tools: AgentTool(weather_agent), AgentTool(activity_agent)
  Responsibility: Orchestrates workflow and provides comprehensive planning advice
  Input: User query about travel/activities
  Output: Complete plan with weather and activity recommendations

=== WORKFLOW ===
User Query
    ↓
Orchestrator receives query
    ↓
Orchestrator calls Weather Agent
    ↓
Weather Agent fetches OpenWeather API data
    ↓
Orchestrator receives weather data
    ↓
Orchestrator calls Activity Agent
    ↓
Activity Agent recommends activities
    ↓
Orchestrator synthesizes both and returns final response
    ↓
User receives comprehensive plan

=== USE CASES ===
1. "What should I do in Chicago this weekend?"
   - Weather agent gets Chicago weather
   - Activity agent recommends activities for that weather
   - Orchestrator combines: "It will be sunny and 75°F. Try hiking, beach, or outdoor sports!"

2. "Is it a good time to visit Chicago?"
   - Weather agent gets Chicago forecast
   - Activity agent recommends beach/water activities
   - Orchestrator: "Yes! It's sunny and 82°F, perfect for beach and water sports!"

3. "Plan my week in Chicago"
   - Weather agent gets 3-day forecast
   - Activity agent recommends activities for each day's weather
   - Orchestrator: Detailed daily plan with activities
"""


if __name__ == "__main__":
    # Print agent cards for presentation
    print(AGENT_CARDS)
    print("\n" + "="*60 + "\n")
    
    # Run example query
    result = asyncio.run(run_query("What should I do in Chicago this weekend? What's the weather?"))
    print("ORCHESTRATOR RESPONSE:")
    print(result)