# The 7 agent patterns, in LangGraph

My working notes from building every **architectural** agent pattern from scratch — not
"X agent" marketing names, the actual underlying paradigms. Each notebook builds the
pattern by hand first, then shows the prebuilt shortcut I'd really use.

Built against **LangGraph 1.2** / **LangChain 1.3** (2026 APIs).

Notebooks are committed **without outputs** so diffs stay reviewable — run them yourself.
Verification status at the time of commit: 1, 2, 3 and 4 have been executed end to end with
no failures; 5 and 6 executed cleanly except for cells that hit the provider's daily token
cap; 7 has not yet had a full run.

## The notebooks

| # | notebook | pattern | the defining feature |
|---|---|---|---|
| 1 | `01_reactive_agent.ipynb` | Reactive | no loop — `state -> action`, one pass |
| 2 | `02_react_agent.ipynb` | Reasoning (ReAct) | **the cycle**, `agent <-> tools` |
| 3 | `03_planning_agent.ipynb` | Planning | an **explicit upfront plan** + replan |
| 4 | `04_reflective_agent.ipynb` | Reflective / learning | an **explicit critic** |
| 5 | `05_memory_agent.ipynb` | Memory / stateful | **checkpointer + store** |
| 6 | `06_multi_agent.ipynb` | Multi-agent | **many decision makers** |
| 7 | `07_autonomous_agent.ipynb` | Autonomous goal-seeking | **the evaluator** ("am I done?") |

`01_reactive_agent.py` is notebook 1 as a plain script, for running outside Jupyter.

## Setup

```bash
uv sync             # or: pip install -e .
```

Create a `.env` in the repo root (it's gitignored):

```
GROQ_API_KEY=gsk_...
```

Then `jupyter lab`.

All seven notebooks run on **`gpt-oss-120b`**, which handles both the multi-step tool loops
and constrained structured output reliably. Two models I tried first did not:
`llama-3.3-70b-versatile` produced malformed tool calls in 4 of 5 runs of the dependent
two-tool loop in notebook 2, and `qwen/qwen3-32b` no longer exists on Groq.

**Rate limits.** Groq's free tier caps at 200k tokens/day per model, and re-running these
notebooks burns through that fast. The same model is served by Cerebras, so every setup
cell takes a provider switch:

```bash
LLM_PROVIDER=cerebras jupyter lab      # needs CEREBRAS_API_KEY in .env
```

**Any other provider?** Each notebook has exactly one setup cell. Replace the `llm = ...`
line and nothing else changes:

```python
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0)
```

## How the patterns relate

```
                        +- Reactive (1) ---- state -> action, no loop
                        |
   add a CYCLE ---------+- ReAct (2) ------- discover the path while acting
                        |
   add a PLAN ----------+- Planning (3) ---- decide the path upfront, replan
                        |
   add a CRITIC --------+- Reflective (4) -- judge & revise the OUTPUT
                        |
   add PERSISTENCE -----+- Memory (5) ------ identity across runs (augments the rest)
                        |
   add more AGENTS -----+- Multi-agent (6) - many decision makers
                        |
   add a GOAL + BUDGET -+- Autonomous (7) -- the agent owns the loop
```

Everything with a marketing name is a recombination:

| "X agent" | = |
|---|---|
| coding agent | Planning + Tools + Memory + Self-Correction |
| research agent | ReAct/Planning + RAG + Tools |
| AI assistant | ReAct + Tools + Memory |
| agentic RAG | ReAct/Planning + Retrieval |
| SWE agent | Planning + Reflection + Tools + exec sandbox |
| deep research | Autonomous + Multi-agent + Reflection + Memory |

## Which one do I need?

```
Do I know all the steps in advance?
├── YES ----------------------------------------> REACTIVE (1)
└── NO
    ├── Must discover the path from tool results? -> REACT (2)   <- start here
    ├── Long horizon / plan needs approval?        -> PLANNING (3)
    ├── Output QUALITY is the problem?             -> REFLECTIVE (4)
    ├── Must remember across sessions?             -> + MEMORY (5)
    ├── >10 tools or parallelisable work?          -> MULTI-AGENT (6)
    └── Agent owns the loop, goal is measurable?   -> AUTONOMOUS (7)
```

Practical build order: start at ReAct (2), which handles most real problems. Add
Reflection (4) for quality issues, Planning (3) when it loses the thread, Memory (5) when it
forgets the user, Multi-agent (6) when there are too many tools, Autonomous (7) only when it
must run unattended.

**Never start at 7.** Every step up multiplies cost, latency and debugging pain.

## The LangGraph API you'll actually use

| task | code |
|---|---|
| state | `class S(TypedDict)` / `class S(MessagesState)` |
| append reducer | `Annotated[list, operator.add]` / `add_messages` |
| node | `builder.add_node("name", fn)` |
| fixed edge | `builder.add_edge("a", "b")` |
| branch | `builder.add_conditional_edges("a", router, ["b", "c"])` |
| entry / exit | `add_edge(START, "a")` / `add_edge("a", END)` |
| tools | `@tool` + `llm.bind_tools()` + `ToolNode(tools)` |
| prebuilt agent | `create_agent(model, tools, system_prompt=...)` |
| structured out | `llm.with_structured_output(Model, method="json_schema")` |
| handoff | `Command(goto="x", update={...})` |
| parallel | `Send("node", {...})` + `operator.add` |
| short-term memory | `compile(checkpointer=InMemorySaver())` |
| long-term memory | `compile(store=InMemoryStore())` |
| pause | `interrupt({...})` -> `invoke(Command(resume=v), cfg)` |
| guard | `config={"recursion_limit": N}` |

## Bugs I hit while writing these

1. **No reducer** → nodes overwrite state instead of appending. Use `add_messages` /
   `operator.add`. With parallel `Send` branches it's an outright `InvalidUpdateError`
   (notebook 6).
2. **No `thread_id`** → the checkpointer does nothing (notebook 5).
3. **A router returning a dict** → routers return a node **name** (`str`); nodes return
   state updates (notebook 1).
4. **Missing `Command[Literal[...]]` annotation** → LangGraph can't draw or validate the
   graph (notebook 6).
5. **No `recursion_limit`** → an infinite loop with a credit card attached (notebook 2).
6. **`Union[...]` in a structured-output schema** → the model nests the payload under the
   class name and every parse fails. Flatten it to a boolean discriminator (notebook 3).
7. **`with_structured_output` defaulting to `function_calling`** → 400s on anything bigger
   than one field. Pass `method="json_schema"` (notebook 1).
