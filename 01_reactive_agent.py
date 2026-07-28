import getpass
import os
from typing import Literal, TypedDict

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field


def _set(var: str) -> None:
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")


load_dotenv()
_set("GROQ_API_KEY")

llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0.4, reasoning_format="hidden")

# Tagged so the stream loop can pick out only the user-facing answer.
answer_llm = llm.with_config(tags=["final"])


# Models
class ReactiveState(TypedDict):
    query: str
    category: str
    response: str


class Classification(BaseModel):
    category: Literal["billing", "technical", "refund", "general"] = Field(
        description="The support category this query belongs to"
    )


# Nodes
def classify(state: ReactiveState) -> dict:
    structured_llm = llm.with_structured_output(Classification)

    result = structured_llm.invoke(
        f"Classify this customer support query.\n\nQuery: {state['query']}"
    )
    # print(f"  [classify] -> {result.category}")

    return {"category": result.category}


def handle_billing(state: ReactiveState) -> dict:
    return {"response": "Routed to Billing. Avg. response time: 4 hours."}


def handle_technical(state: ReactiveState) -> dict:
    return {"response": "Routed to Tech Support. Please share your error logs."}


def handle_refund(state: ReactiveState) -> dict:
    return {"response": "Refund request created. Processed within 5 business days."}


def handle_general(state: ReactiveState) -> dict:
    return {"response": "Thanks for reaching out! An agent will reply shortly."}


def route(state: ReactiveState) -> str:
    return {
        "billing": "handle_billing",
        "technical": "handle_technical",
        "refund": "handle_refund",
        "general": "handle_general",
    }[state["category"]]


# Graph Building
checkpointer = InMemorySaver()
config = {"configurable": {"thread_id": "thread_1"}}

builder = StateGraph(ReactiveState)

builder.add_node("classify", classify)
builder.add_node("handle_billing", handle_billing)
builder.add_node("handle_technical", handle_technical)
builder.add_node("handle_refund", handle_refund)
builder.add_node("handle_general", handle_general)

builder.add_edge(START, "classify")

builder.add_conditional_edges(
    "classify",
    route,
    ["handle_billing", "handle_technical", "handle_refund", "handle_general"],
)

for handler in ["handle_billing", "handle_technical", "handle_refund", "handle_general"]:
    builder.add_edge(handler, END)

graph = builder.compile(checkpointer=checkpointer)

if __name__ == "__main__":
    result = graph.stream({"query": "I was charged twice this month!"}, config=config, stream_mode="values")

    current_node = None

    for chunk, metadata in result:
        node = metadata.get("langgraph_node")
        if node != current_node:
            current_node = node
            print(f"\n\n--- {node} ---")
        if chunk.content:
            print(f"Result --- {chunk.content}", end="", flush=True)

# @tool(description="Look up the delivery status of an order by its ID.")
# def get_order_status(order_id: str) -> str:
#     return {"A1": "Shipped, arrives Friday", "B2": "Processing"}.get(order_id, "Not found")
#
#
# class ToolState(TypedDict):
#     query: str
#     response: str
#
#
# def reactive_tool_node(state: ToolState) -> dict:
#     model = llm.bind_tools([get_order_status])
#     ai_msg = model.invoke(state["query"])
#
#     if not ai_msg.tool_calls:
#         return {"response": ai_msg.content}
#
#     call = ai_msg.tool_calls[0]
#     tool_result = get_order_status.invoke(call["args"])
#     return {"response": f"Order {call['args']['order_id']}: {tool_result}"}
#
#
# tool_builder = StateGraph(ToolState)
# tool_builder.add_node("act", reactive_tool_node)
# tool_builder.add_edge(START, "act")
# tool_builder.add_edge("act", END)
# tool_graph = tool_builder.compile()
#
#
# def show_graph() -> None:
#     print("\n=== Graph ===")
#     print(graph.get_graph().draw_mermaid())
#
#
# def run_batch() -> None:
#     print("\n=== invoke ===")
#     queries = [
#         "I was charged twice this month!",
#         "The app crashes when I open settings",
#         "I want my money back for last month's plan",
#         "What are your office hours?",
#     ]
#     for q in queries:
#         print(f"\nQ: {q}")
#         result = graph.invoke({"query": q})
#         print(f"  -> [{result['category']}] {result['response']}")
#
#
# def run_stream() -> None:
#     print("\n=== stream (updates) ===")
#     for chunk in graph.stream({"query": "My invoice looks wrong"}, stream_mode="updates"):
#         print(chunk)
#
#
# def run_tool_variant() -> None:
#     print("\n=== single-tool variant ===")
#     print(tool_graph.invoke({"query": "Where is order A1?"})["response"])
#
#
# if __name__ == "__main__":
#     show_graph()
#     run_batch()
#     run_stream()
#     run_tool_variant()
