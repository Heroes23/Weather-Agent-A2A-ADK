# A2A Weather & Activity Planning System Architecture

## Overview

This is an **Agent-to-Agent (A2A)** multi-agent system built with **Google ADK** (Agent Development Kit) that orchestrates specialized agents to provide comprehensive travel and activity planning.

The system demonstrates a **sequential coordination pattern** where:
1. A user query is received by an **Orchestrator Agent**
2. The **Orchestrator** delegates to specialized agents
3. Each agent executes its tools and returns results
4. The **Orchestrator** synthesizes all information into a final response

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Query                            │
│         "What should I do in Chicago?"                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │  Orchestrator Agent        │
        │  (Coordinator)             │
        │                            │
        │ - Receives user query      │
        │ - Routes to agents         │
        │ - Synthesizes results      │
        └─────┬──────────────┬───────┘
              │              │
              ▼              ▼
        ┌──────────────┐  ┌──────────────────┐
        │Weather Agent │  │Activity Agent    │
        │              │  │                  │
        │Tools:        │  │Tools:            │
        │- get_current │  │- get_activities  │
        │  _weather    │  │                  │
        │- get_forecast│  │                  │
        └────┬─────────┘  └────┬─────────────┘
             │                 │
             ▼                 ▼
      ┌─────────────────┐  ┌──────────────────┐
      │OpenWeather API  │  │Activity Database │
      │(Real-time data) │  │(Mock data)       │
      └─────────────────┘  └──────────────────┘
             │                 │
             └────┬────────────┘
                  │
                  ▼
        ┌────────────────────────────┐
        │  Synthesized Response      │
        │  (Weather + Activities)    │
        └────────────────────────────┘
                  │
                  ▼
        ┌────────────────────────────┐
        │      User Response         │
        │ "It will be sunny (75°F).  │
        │  Try hiking, beach, etc!"  │
        └────────────────────────────┘
```

---

## Agent Design

### 1. Weather Agent

**Purpose:** Retrieve real-time weather data and forecasts

**Configuration:**
```python
Agent(
    name="weather_agent",
    model="anthropic/claude-opus-4-6",
    description="Retrieves real-time weather data and forecasts for any city",
    tools=[get_current_weather, get_forecast]
)
```

**Tools:**
- `get_current_weather(city)` - Calls OpenWeather API for current conditions
- `get_forecast(city)` - Calls OpenWeather API for 3-day forecast

**Inputs:** City name (string)

**Outputs:** 
```json
{
  "city": "Chicago",
  "condition": "Sunny",
  "temp": 75,
  "humidity": 60,
  "forecast": [...]
}
```

---

### 2. Activity Agent

**Purpose:** Recommend activities based on weather conditions

**Configuration:**
```python
Agent(
    name="activity_agent",
    model="anthropic/claude-opus-4-6",
    description="Recommends activities based on weather conditions",
    tools=[get_activities]
)
```

**Tools:**
- `get_activities(weather_condition, temperature)` - Returns activity recommendations

**Inputs:** Weather condition (string) and temperature (float)

**Outputs:**
```json
{
  "condition": "Sunny",
  "temperature": 75,
  "recommended_activities": [
    "hiking",
    "beach",
    "outdoor sports",
    "picnic"
  ]
}
```

---

### 3. Orchestrator Agent

**Purpose:** Coordinate Weather and Activity agents to provide comprehensive planning

**Configuration:**
```python
Agent(
    name="orchestrator",
    model="anthropic/claude-opus-4-6",
    description="Coordinates weather and activity agents...",
    tools=[
        AgentTool(agent=weather_agent),
        AgentTool(agent=activity_agent)
    ]
)
```

**Tools:**
- `AgentTool(agent=weather_agent)` - Calls Weather Agent
- `AgentTool(agent=activity_agent)` - Calls Activity Agent

**Inputs:** User query (string)

**Outputs:** Comprehensive plan combining weather and activities

---

## Workflow Execution Flow

### Step-by-Step Process

1. **User Query Reception**
   - User asks: "What should I do in Chicago this weekend?"
   - Query sent to Orchestrator

2. **Orchestrator Analysis**
   - Orchestrator recognizes it needs weather data
   - Orchestrator calls `AgentTool(weather_agent)`

3. **Weather Agent Execution**
   - Receives city: "Chicago"
   - Calls `get_current_weather("Chicago")`
   - Receives real-time data from OpenWeather API
   - Returns: Sunny, 75°F, 60% humidity

4. **Activity Agent Invocation**
   - Orchestrator extracts weather info
   - Orchestrator calls `AgentTool(activity_agent)`
   - Passes: condition="Sunny", temperature=75

5. **Activity Recommendations**
   - Activity agent calls `get_activities("Sunny", 75)`
   - Returns: hiking, beach, outdoor sports, picnic

6. **Response Synthesis**
   - Orchestrator combines both results
   - Generates natural language response
   - "It will be sunny and 75°F. Perfect for hiking, beach, or outdoor sports!"

7. **User Response**
   - Final response delivered to user

---

## Data Flow

```
User Input
    │
    ├─ Query Parsing (Orchestrator)
    │
    ├─ Weather Data Retrieval
    │  └─ get_current_weather() → OpenWeather API
    │
    ├─ Activity Recommendations
    │  └─ get_activities() → Local Activity Database
    │
    └─ Response Synthesis (Orchestrator)
        └─ Natural Language Generation
            └─ User Output
```

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | Google ADK | Agent orchestration and execution |
| **LLM** | Claude (Anthropic) | Agent reasoning and decision-making |
| **External API** | OpenWeather API | Real-time weather data |
| **Runtime** | Python asyncio | Asynchronous execution |
| **Session Management** | InMemorySessionService | Conversation state management |

---

## Key Features

### 1. Agent-to-Agent Communication
- Agents communicate through `AgentTool` wrapper
- Orchestrator controls the flow
- Sequential coordination pattern

### 2. Real-Time Data Integration
- OpenWeather API for current conditions
- Mock activity database (extensible)
- Flexible data sources per agent

### 3. Scalability
- Easy to add new agents
- Each agent has specialized responsibility
- Clear separation of concerns

### 4. Extensibility
- Add new tools to agents
- Create new agents for different domains
- Modify orchestrator logic

---

## Use Cases

### Use Case 1: Weekend Activity Planning
**User Query:** "What should I do in Chicago this weekend?"

**Workflow:**
1. Weather Agent → Gets Chicago weather for the weekend
2. Activity Agent → Recommends activities for that weather
3. Orchestrator → Synthesizes: "Sunny 75°F → Try hiking, beach, sports"

**Output:** Comprehensive weekend plan

---

### Use Case 2: Travel Feasibility Assessment
**User Query:** "Is it a good time to visit Miami?"

**Workflow:**
1. Weather Agent → Gets Miami forecast
2. Activity Agent → Recommends beach/water activities
3. Orchestrator → "Yes! Sunny 82°F, perfect for beach & water sports"

**Output:** Travel recommendation

---

### Use Case 3: Weekly Planning
**User Query:** "Plan my week in New York"

**Workflow:**
1. Weather Agent → Gets 3-day forecast for each day
2. Activity Agent → Recommends activities for each day's weather
3. Orchestrator → Detailed daily plan with activities and weather

**Output:** Day-by-day itinerary

---

## Design Patterns

### 1. Sequential Orchestration
- One agent (Orchestrator) controls execution order
- Agents execute in sequence: Weather → Activity
- Results flow back to Orchestrator

### 2. Tool-Based Delegation
- Agents expose capabilities as tools
- `AgentTool` wraps agent as callable tool
- Enables A2A communication

### 3. Separation of Concerns
- Each agent has single responsibility
- Weather Agent = weather expertise
- Activity Agent = activity expertise
- Orchestrator = coordination logic

### 4. State Management
- `InMemorySessionService` tracks conversation state
- Session ID preserves context across calls
- Multi-turn conversations supported

---

## Conclusion

This A2A system demonstrates a scalable, extensible pattern for multi-agent orchestration using Google ADK. The clear separation of concerns, sequential coordination, and real-time data integration make it suitable for complex planning and recommendation scenarios.

The architecture effectively demonstrates:
- Agent Pattern (orchestration & delegation)
- Agent Cards (role, tools, responsibility)
- Workflow (sequence diagram & execution flow)
- Use Cases (concrete examples)
