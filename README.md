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
and constrained structured output reliably.


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
