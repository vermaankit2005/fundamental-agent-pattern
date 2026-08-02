"""Notebook 01 (reactive agent) as a plain script, for running outside Jupyter.

    python 01_reactive_agent.py

Same graph as 01_reactive_agent.ipynb: one LLM call classifies the query, then a
conditional edge fans out to a deterministic handler. No cycle == reactive.
"""

import getpass
import os
from typing import Literal, TypedDict

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

load_dotenv()
if not os.environ.get("GROQ_API_KEY"):
    os.environ["GROQ_API_KEY"] = getpass.getpass("GROQ_API_KEY: ")

llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0, reasoning_format="hidden")


class ReactiveState(TypedDict):
    query: str
    category: str
    response: str


class Classification(BaseModel):
    """Forces the LLM into one of four valid categories."""

    category: Literal["billing", "technical", "refund", "general"] = Field(
        description="The support category this query belongs to"
    )


# method="json_schema" constrains decoding to the schema. The default
# ("function_calling") is unreliable on Groq's gpt-oss models.
classifier = llm.with_structured_output(Classification, method="json_schema")


def classify(state: ReactiveState) -> dict:
    result = classifier.invoke(
        f"Classify this customer support query.\n\nQuery: {state['query']}"
    )
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
    """Routers return the NAME of the next node, never a state update."""
    return {
        "billing": "handle_billing",
        "technical": "handle_technical",
        "refund": "handle_refund",
        "general": "handle_general",
    }[state["category"]]


HANDLERS = {
    "handle_billing": handle_billing,
    "handle_technical": handle_technical,
    "handle_refund": handle_refund,
    "handle_general": handle_general,
}

builder = StateGraph(ReactiveState)
builder.add_node("classify", classify)
for name, fn in HANDLERS.items():
    builder.add_node(name, fn)

builder.add_edge(START, "classify")
builder.add_conditional_edges("classify", route, list(HANDLERS))
for name in HANDLERS:
    builder.add_edge(name, END)

graph = builder.compile()


def main() -> None:
    print(graph.get_graph().draw_mermaid())

    queries = [
        "I was charged twice this month!",
        "The app crashes when I open settings",
        "I want my money back for last month's plan",
        "What are your office hours?",
    ]
    for q in queries:
        result = graph.invoke({"query": q})
        print(f"\nQ: {q}\n  -> [{result['category']}] {result['response']}")

    # stream_mode="updates" yields {node_name: state_update} dicts, one per node.
    print("\n--- streaming updates ---")
    for chunk in graph.stream({"query": "My invoice looks wrong"}, stream_mode="updates"):
        print(chunk)


if __name__ == "__main__":
    main()
