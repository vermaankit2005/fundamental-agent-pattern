# 🧠 The 7 Fundamental Agent Patterns — LangGraph Guide

A complete, runnable guide to every **architectural** agent pattern. Not "X agent"
marketing names — the actual underlying paradigms.

Built against **LangGraph v1.x** (2026 APIs — no deprecated `set_entry_point()`).

---

## 📁 Contents

| # | Notebook | Pattern | Defining feature |
|---|---|---|---|
| 1 | `01_reactive_agent.ipynb` | Reactive | no loop — `state → action`, one pass |
| 2 | `02_react_agent.ipynb` | Reasoning (ReAct) | **the cycle** `agent ⇄ tools` |
| 3 | `03_planning_agent.ipynb` | Planning | **explicit upfront plan** + replan |
| 4 | `04_reflective_agent.ipynb` | Reflective / Learning | **an explicit critic** |
| 5 | `05_memory_agent.ipynb` | Memory / Stateful | **checkpointer + store** |
| 6 | `06_multi_agent.ipynb` | Multi-Agent | **many decision makers** |
| 7 | `07_autonomous_agent.ipynb` | Autonomous Goal-Seeking | **the evaluator** ("am I done?") |

---

## 🚀 Setup

```bash
pip install langgraph langchain-openai langchain-core
export OPENAI_API_KEY=sk-...
jupyter lab
```

Optional extras used in a few cells:

```bash
pip install langgraph-supervisor langgraph-swarm   # notebook 6
pip install langgraph-checkpoint-postgres          # notebook 5, production
```

**Using a different model?** Every notebook has one setup cell. Swap it:

```python
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)
```

---

## 📖 Every notebook follows the same structure

1. 🎯 **Mental model** — the ASCII diagram
2. 📌 **Key properties** — the pointwise table
3. 🤔 **The confusing parts, resolved** — the questions you *would* have asked
4. 🔧 **Build it from scratch** — step by step, heavily commented
5. ⚡ **The prebuilt shortcut** — what you'd actually use at work
6. ⚠️ **Failure modes** — symptom → cause → fix
7. 📋 **Cheat sheet** — the API in one block
8. 🌳 **Decision tree** — when to pick this pattern

---

## 🗺️ How the patterns relate

```
                        ┌─ Reactive (1) ─── state -> action, no loop
                        │
   add a CYCLE ─────────┼─ ReAct (2) ────── discover the path while acting
                        │
   add a PLAN ──────────┼─ Planning (3) ─── decide the path upfront, replan
                        │
   add a CRITIC ────────┼─ Reflective (4) ─ judge & revise the OUTPUT
                        │
   add PERSISTENCE ─────┼─ Memory (5) ───── identity across runs (augments all)
                        │
   add more AGENTS ─────┼─ Multi-agent (6) ─ many decision makers
                        │
   add a GOAL + BUDGET ─┴─ Autonomous (7) ── the agent owns the loop
```

### Everything with a marketing name is a recombination

| "X agent" | = |
|---|---|
| Coding agent | Planning + Tools + Memory + Self-Correction |
| Research agent | ReAct/Planning + RAG + Tools |
| AI assistant | ReAct + Tools + Memory |
| Agentic RAG | ReAct/Planning + Retrieval |
| SWE agent | Planning + Reflection + Tools + exec sandbox |
| Deep research | Autonomous + Multi-agent + Reflection + Memory |

---

## 🧭 Which pattern do I need?

```
Do I know all the steps in advance?
├── YES ──────────────────────────────► REACTIVE (1)
└── NO
    ├── Must discover the path from tool results? ──► REACT (2)   ← start here
    ├── Long horizon / plan needs approval?       ──► PLANNING (3)
    ├── Output QUALITY is the problem?            ──► REFLECTIVE (4)
    ├── Must remember across sessions?            ──► + MEMORY (5)
    ├── >10 tools or parallelisable work?         ──► MULTI-AGENT (6)
    └── Agent owns the loop, goal is measurable?  ──► AUTONOMOUS (7)
```

### Practical build order

```
1. Start with ReAct (2).      It solves ~70% of real problems.
2. Quality issues?      → add Reflection (4).
3. Losing the thread?   → add Planning (3).
4. Forgetting the user? → add Memory (5).
5. Too many tools?      → split into Multi-agent (6).
6. Runs unattended?     → wrap in Autonomous (7) + guardrails.
```

⚠️ **Never start at 7.** Every step up multiplies cost, latency and debugging pain.
Earn each one.

---

## 🔑 The LangGraph API you'll actually use

| Task | Code |
|---|---|
| State | `class S(TypedDict)` / `class S(MessagesState)` |
| Append reducer | `Annotated[list, operator.add]` / `add_messages` |
| Node | `builder.add_node("name", fn)` |
| Fixed edge | `builder.add_edge("a", "b")` |
| Branch | `builder.add_conditional_edges("a", router, ["b","c"])` |
| Entry/exit | `add_edge(START, "a")` / `add_edge("a", END)` |
| Tools | `@tool` + `llm.bind_tools()` + `ToolNode(tools)` |
| ReAct shortcut | `create_react_agent(llm, tools, prompt=...)` |
| Structured out | `llm.with_structured_output(PydanticModel)` |
| Handoff | `Command(goto="x", update={...})` |
| Parallel | `Send("node", {...})` + `operator.add` |
| Short-term mem | `compile(checkpointer=InMemorySaver())` |
| Long-term mem | `compile(store=InMemoryStore())` |
| Pause | `interrupt({...})` → `invoke(Command(resume=v), cfg)` |
| Guard | `config={"recursion_limit": N}` |

---

## ⚠️ The five bugs everyone hits

1. **No reducer** → nodes overwrite state instead of appending. Use `add_messages` / `operator.add`.
2. **No `thread_id`** → checkpointer does nothing.
3. **Router returns a dict** → routers return a **node name (str)**, nodes return state updates.
4. **Missing `Command[Literal[...]]` annotation** → LangGraph can't draw or validate the graph.
5. **No `recursion_limit`** → an infinite loop with a credit card attached.

---

*Generated July 2026 · LangGraph v1.x*
