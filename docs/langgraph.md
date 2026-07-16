# LangGraph Orchestration

PRism leverages LangGraph to create a deterministic, cyclic graph of agents.

## Nodes
1. `diff_analyzer`: Parses the GitHub diff using Tree-sitter.
2. `security_agent`: Prompts Groq API to check for vulnerabilities.
3. `quality_agent`: Prompts Groq API to check for code smells.
4. `logic_agent`: Prompts Groq API to check for logical bugs.
5. `orchestrator`: Merges all outputs into a single JSON structure.
6. `publisher`: Publishes the final review to GitHub.

## Edges
- The `diff_analyzer` conditionally edges to the parallel agents.
- The parallel agents edge to the `orchestrator`.
- The `orchestrator` edges to the `publisher`.
