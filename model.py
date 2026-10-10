
from tools import (
    web_search,
    local_search,
    send_mail,
    read_emails,
    calculator,
    create_report,
)
import json

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import HumanMessage, SystemMessage ,ToolMessage

from dotenv import load_dotenv
import os


load_dotenv()

google_api_key = os.environ.get("google_api_key")
CONNECTION_store = os.environ.get("CONNECTION_store")

if not google_api_key:
    raise ValueError("google_api_key is missing from .env")

if not CONNECTION_store:
    raise ValueError("CONNECTION_store is missing from .env")


model = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    temperature=0,
    google_api_key=google_api_key,
)

tools = [
    web_search,
    local_search,
    send_mail,
    read_emails,
    calculator,
    create_report,
]

llm = model.bind_tools(tools)


def llm_node(state: MessagesState):
    response = llm.invoke(state["messages"])

    return {
        "messages": [response]
    }


tool_node = ToolNode(tools)

graph = StateGraph(MessagesState)

graph.add_node("llm", llm_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "llm")
graph.add_edge("tools", "llm")


def route(state: MessagesState):
    last_message = state["messages"][-1]

    if last_message.tool_calls:
        return "tools"

    return "end"


graph.add_conditional_edges(
    "llm",
    route,
    {
        "tools": "tools",
        "end": END,
    },
)


# Keep the PostgreSQL connection/checkpointer open
cm = PostgresSaver.from_conn_string(CONNECTION_store)
checkpointer = cm.__enter__()

checkpointer.setup()

app = graph.compile(checkpointer=checkpointer)


def model_app(content, thread_id: str):
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    previous_state = app.get_state(config)
    old_messages = previous_state.values.get("messages", [])
    old_count = len(old_messages)

    message = HumanMessage(content=content)

    out = app.invoke(
        {"messages": [message]},
        config=config,
    )

    new_messages = out["messages"][old_count:]

    answer = out["messages"][-1].content
    report = None

    for msg in reversed(new_messages):
        if isinstance(msg, ToolMessage) and msg.name == "create_report":
            try:
                data = json.loads(msg.content)

                if data.get("status") == "success":
                    report = {
                        "file_name": data["file_name"],
                        "file_type": data["file_type"],
                    }

            except (json.JSONDecodeError, TypeError, KeyError):
                pass

            break

    return {
        "answer": answer,
        "report": report,
    }
