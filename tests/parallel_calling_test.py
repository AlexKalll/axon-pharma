import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client()
client.api_key = os.getenv('GEMINI_API_KEY')

# Define the function declaration
schedule_meeting_function = {
    "name": "schedule_meeting",
    "description": "Schedules a meeting with specified attendees at a given time and date.",
    "parameters": {
        "type": "object",
        "properties": {
            "attendees": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of people attending the meeting.",
            },
            "date": {
                "type": "string",
                "description": "Date of the meeting (e.g., '2024-07-29')",
            },
            "time": {
                "type": "string",
                "description": "Time of the meeting (e.g., '15:00')",
            },
            "topic": {
                "type": "string",
                "description": "The subject or topic of the meeting.",
            },
        },
        "required": ["attendees", "date", "time", "topic"],
    },
}

generate_text_function = {
    "name": "generate_text",
    "description": "Generates text based on a prompt.",
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "The prompt to generate text for.",
            },
        },
        "required": ["prompt"],
    },
}


def schedule_meeting(attendees: list, date: str, time: str, topic: str) -> dict[list, str, str, str]: 
    """
    Schedules a meeting with specified attendees at a given time and date if time is not passed.
    Args:
        attendees: List of people attending the meeting.
        date: Date of the meeting (e.g., '2024-07-29').
        time: Time of the meeting (e.g., '15:00').
        topic: The subject or topic of the meeting.
    Returns:
        A string indicating the meeting has been scheduled if time is not passed.
    """
    return {
        "attendees": attendees,
        "date": date,
        "time": time,
        "topic": topic,
    }
    
def generate_text(prompt: str) -> str:
    """
    Generates text based on a prompt.
    Args:
        prompt: The prompt to generate text for.
    Returns:
        A string containing the generated text.
    """
    return prompt

# Configure the client and tools
client = genai.Client()
tools = types.Tool(function_declarations=[schedule_meeting_function, generate_text_function])
config = types.GenerateContentConfig(tools=[tools])

# Define user prompt
prompt = "Schedule a meeting with Bob and Alice for 03/14/2025 at 10:00 AM about the Q3 planning. Additionaly generate a summary paragraph about Ethiopia"

contents = [
    types.Content(
        role="user", parts=[types.Part(text=prompt)]
    )
]


try:
    # Send request with function declarations
    chat = client.chats.create(model = "gemini-2.5-flash", config=config)
    response = chat.send_message(prompt)

    # print(response.candidates[0].content.parts[0].function_call)
    

    # print("Response:", response)

    
    i = 0
    for fn in response.function_calls:
        tool_call = response.candidates[0].content.parts[i].function_call
        i += 1
        if tool_call.name == "schedule_meeting":
            result = schedule_meeting(**tool_call.args)
            # print(f"Function execution result: {result}")
        elif tool_call.name == "generate_text":
            result = generate_text(tool_call.args)

        function_response_part = types.Part.from_function_response(
            name=tool_call.name,
            response={"result": result},
        )

        # Append function call and result of the function execution to contents
        contents.append(response.candidates[0].content) # Append the content from the model's response.
        contents.append(types.Content(role="user", parts=[function_response_part])) # Append the function response

    final_response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=config,
        contents=contents,
    )

    print(final_response)
    print(final_response.text)
    
except Exception as e:
    print(f"Error: {e}")


# Output
"""
A meeting about Q3 planning has been scheduled with Bob and Alice for March 14, 2025 at 10:00 AM.

Here is a summary paragraph about Ethiopia:
Ethiopia, located in the Horn of Africa, is a landlocked country with a rich and ancient history, often referred to as the "cradle of humanity." It is unique in Africa for never having been formally colonized, maintaining its independence throughout the Scramble for Africa. The country boasts diverse landscapes, from the rugged Simien Mountains to the Danakil Depression, one of the hottest places on Earth. Ethiopia is also the origin of coffee and is renowned for its vibrant cultural heritage, including the rock-hewn churches of Lalibela and the ancient city of Axum, both UNESCO World Heritage sites. Its economy is largely agricultural, with coffee being a major export, and the country is a significant regional power, playing a key role in African diplomacy.
"""