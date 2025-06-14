import chainlit as cl
import os
from agents import Agent,Runner,AsyncOpenAI,OpenAIChatCompletionsModel,RunConfig
from dotenv import load_dotenv
from openai.types.responses import ResponseTextDeltaEvent
# @cl.on_message
# async def handle_message(message : cl.Message):  # User Message
#     await cl.Message(content=f"Hello {message.content}").send()  # AI Message
# # Async means def agent processing to creating the context after the context is ready then response to user
load_dotenv()
gemini_api_key=os.getenv("GEMINI_API_KEY")

# Check if the api key is present , If not raise an error
if not gemini_api_key:
    raise ValueError("Gemini Api key is not set.")

# AsyncOpenAI function () is used to connect sever api key or model's 
external_client=AsyncOpenAI(
    api_key=gemini_api_key,
    # Base url means where (LLM) is deploy or simple LLM deploy Url and Developer can find this url on offical docs gemini google model.
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",  # Third party model not openai.Openai supports third party models
    openai_client=external_client
)

config = RunConfig(
    model=model,
    model_provider=external_client,
    tracing_disabled = True
)

# Agent Responsiblity's ==> user_input,Dividing_into_subtasks,Used available_tool,if failer occur try again,Collect all the data and response final output
agent = Agent(
    model=model,
    name="Assistant",
    instructions="you are a helpful assistant" # Set persona( mean kis ky assistant ho.example:governor ky ho,Sir zia ky assitant ho , ya kisi or ky )
 )
# By default Runner is Async . (Sync) => mean agent ko task da di ab jb bi task complete ho jb mujy response do chahiye 5 minute lagy ya 10 minute .
# (Async) mean task bi ho raha hn is ky sath baki or km bi chl raha hn.jb task complete ho ga await kr ky reponse da ga.
# result = Runner.run_sync(agent,"write 10 words on ai",run_config=config) # Runner is used to communicate between client to server (sync,async) 
# print(result.final_output)

@cl.on_chat_start
async def handle_chat_start():
    cl.user_session.set("history",[])
    await cl.Message(content="Hello i am Daniyal Assistant how can i help you ?").send()
        


@cl.on_message
async def handle_message(message : cl.Message):
    history = cl.user_session.get("history")
    msg = cl.Message(content="")
    await msg.send()
    history.append({"role":"user","content":message.content})
    result = Runner.run_streamed(
        agent,
        input = history,
        run_config=config
    )
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data ,ResponseTextDeltaEvent):
            await msg.stream_token(event.data.delta)
    history.append({"role":"assistant","content":result.final_output})