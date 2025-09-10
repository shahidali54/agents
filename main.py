import os
import chainlit as cl
from agents import Agent, Runner, AsyncOpenAI, RunConfig, OpenAIChatCompletionsModel
from agents.tool import function_tool
from openai.types.responses import ResponseTextDeltaEvent
from dotenv import load_dotenv

# 🌱 Load environment variables
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

# step 1: Provider
provider = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai",

)

# step 2: Model
model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=provider,
)

# step 3: Config
config = RunConfig(
    model=model,
    model_provider=provider,
    tracing_disabled=True,
)

@function_tool("get_weather")
def get_weather(location: str, unit: str = "celsius") -> str:
    """
    get the weather for a given location, return a short description of the weather
    """

 # Example logic
    if unit == "celsius":
        return f"The weather in {location} is sunny with a temperature of 25°C."
    elif unit == "fahrenheit":
        return f"The weather in {location} is sunny with a temperature of 77°F."
    else:
        return f"Weather data for {location} is not available in {unit}."
    

@function_tool("giaic_student_finder")
def giaic_student_finder(name: str) -> str:
    """
    Find a student by name in the GIAIC database.
    """
    # Example logic
    students = {
        "Subhan Kaladi": "Subhan is a student of GIAIC.",
        "Shahid Ali": "Shahid is a student of GIAIC.",
    }
    return students.get(name, f"Student {name} not a student of GIAIC.")
    
# step 4: Agent
agent = Agent(
    name="GIAIC Assistant",
    instructions="You are a helpful assistant that can answer questions about GIAIC students and their activities and can provide weather information.",
    tools=[get_weather, giaic_student_finder],
    model=model,
)


@cl.on_chat_start
async def on_chat_start():
    """
    This function is called when the chat starts.
    it initializes the agent and sends a welvome message.
    """
    cl.user_session.set("history", [])
    await cl.Message(
        content="Welcome to GIAIC Assistant! How can I assist you today?",
        author="GIAIC Assistant",
    ).send()

@cl.on_message
async def handle_message(message: cl.Message):
    """
    This function is called when a message is received.
    it runs the agent and sends the response to the user.
    """
    history = cl.user_session.get("history")

    chat = cl.Message(
        content="",
        author="GIAIC Assistant",
        
    )
    await chat.send()


    history.append({
        "role": "user",
        "content": message.content,
    })
    result = Runner.run_streamed(
        agent,
        input=history,
        run_config=config,
    )

    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            await chat.stream_token(event.data.delta)
    
    history.append({"role": "assistant", "content": result.final_output})
    cl.user_session.set("history", history)


