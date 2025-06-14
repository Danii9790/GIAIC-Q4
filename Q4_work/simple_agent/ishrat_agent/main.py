import os 
from agents import Agent,Runner,AsyncOpenAI,OpenAIChatCompletionsModel
from dotenv import load_dotenv
import chainlit as cl


load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

external_client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai"
)
model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=external_client
)

ishrat_agent = Agent(
    name = "Ishrat Agent",
    instructions="You are a Ishrat agent your work/job/task is to greet everyone with Aslam-ul-alukum form Ishrat-ul-abad if someone says hi,hello your response with friendly greeting message if someone says by then reply Allah Hafiz from Ishrat_ul_abad",
    model=model   
)

# user_question =input("Enter your Question : ")
# result=Runner.run_sync(ishrat_agent,user_question)
# print(result.final_output)


@cl.on_chat_start
async def handle_chat_start():
    cl.user_session.set("history", [])
    await cl.Message(
        content="Hello and welcome! I’m the AI assistant of Ishrat-ul-abad. Would you like to know more about him or explore something specific?"
    ).send()



@cl.on_message
async def handle_message(message: cl.Message):
    history = cl.user_session.get("history")
    history.append({"role": "user", "content": message.content})

    result = await cl.make_async(Runner.run_sync)(ishrat_agent, input=history)

    response_text = result.final_output
    await cl.Message(content=response_text).send()

    history.append({"role": "assistant", "content": response_text})
    cl.user_session.set("history", history)
