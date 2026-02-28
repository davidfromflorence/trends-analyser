# Coding Agent Prompt (OpenAI Agents SDK)
Build a modular Jupyter notebook (Python) that implements a research → analysis → report multi-agent workflow using the OpenAI Agents SDK. The notebook must be structured so that the Researcher agent can be swapped out later for a different project without changing the rest of the pipeline.

Requirements
Notebook format: Use clear section headings and separate code/markdown cells.

Dependencies: Include a setup cell installing openai-agents, python-dotenv, pydantic, requests.

Modularity:

Create a dedicated function or class to build the 'Researcher' agent.

The pipeline should accept a research_agent object so it can be replaced later.

Agents:

'Researcher' (uses a web search tool or stub tool).

'Analyst' (summarizes trends/risks/insights).

'Writer' (returns structured output: executive summary, markdown report, follow-up questions).

Tooling:

Implement a real Tavily search function_tool so the Researcher can search online.

The Tavily API key is provided in the environment (TAVILY_API_KEY). Load it via python-dotenv.

Use the Tavily search endpoint with JSON payload: api_key, query, max_results.

Pipeline:

A manager function run_pipeline(user_query, researcher_agent) that orchestrates:

Researcher → summary

Analyst → insights

Writer → final report

Output formatting: Display the executive summary, markdown report, and follow-up questions cleanly.

Example run: Include a sample query and show the output.

Notes
Use the correct import path: from agents import Agent, Runner, function_tool, SQLiteSession

Do not use openai_agents.

Keep the Researcher creation isolated so I can later swap it for a different domain-specific researcher.

Use SQLiteSession to share context between agents and always pass a session_id.

Use Pydantic output models for structured outputs.

Ensure the Researcher's instructions explicitly say to use the Tavily search tool to gather sources before summarizing.
