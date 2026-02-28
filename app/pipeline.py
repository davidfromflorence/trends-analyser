import json
import os
import uuid
from collections.abc import AsyncGenerator

import requests
from dotenv import load_dotenv

# Import the Google GenAI SDK
from google import genai
from google.genai import types

from app.models import AnalystOutput, FinalReport

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

load_dotenv()

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Initialize the Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)


def tavily_search(query: str, max_results: int = 5) -> str:
    """Search the web using Tavily and return relevant results.
    
    Args:
        query: The search query to send to Tavily
        max_results: Maximum number of results to return
    """
    response = requests.post(
        "https://api.tavily.com/search",
        json={
            "api_key": TAVILY_API_KEY,
            "query": query,
            "max_results": max_results,
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    results = []
    for r in data.get("results", []):
        results.append(
            f"Title: {r['title']}\nURL: {r['url']}\nContent: {r['content']}\n"
        )
    return "\n---\n".join(results) if results else "No results found."


# ---------------------------------------------------------------------------
# Agent Configurations
# ---------------------------------------------------------------------------

# Use gpt-4o equivalent: gemini-2.5-flash for tool use, or gemini-2.5-pro for deep analysis
MODEL_NAME = "gemini-2.5-flash"


def build_researcher_config() -> types.GenerateContentConfig:
    """Build the configuration for the Tavily-backed Researcher."""
    return types.GenerateContentConfig(
        system_instruction=(
            "You are a thorough research assistant. "
            "When given a query, you MUST use the tavily_search tool to gather "
            "real sources from the web before summarizing. "
            "Make multiple searches if needed to cover different angles. "
            "Return a comprehensive research summary that includes key facts, "
            "data points, and source URLs."
        ),
        tools=[tavily_search],
        temperature=0.4,
    )


analyst_config = types.GenerateContentConfig(
    system_instruction=(
        "You are a senior analyst. Given a research summary, identify the most "
        "important trends, potential risks, and actionable insights. "
        "Be specific and back up your analysis with evidence from the research."
    ),
    response_mime_type="application/json",
    response_schema=AnalystOutput,
    temperature=0.3,
)

writer_config = types.GenerateContentConfig(
    system_instruction=(
        "You are an expert report writer. Given an analysis with trends, risks, "
        "and insights, produce a polished final report. "
        "The executive_summary should be 2-3 concise paragraphs. "
        "The markdown_report should be a detailed, well-structured document with "
        "headings, bullet points, and clear sections. "
        "Include 3-5 follow_up_questions that would deepen the research."
    ),
    response_mime_type="application/json",
    response_schema=FinalReport,
    temperature=0.5,
)

# ---------------------------------------------------------------------------
# SSE helpers
# ---------------------------------------------------------------------------


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# ---------------------------------------------------------------------------
# Pipeline (async generator yielding SSE events)
# ---------------------------------------------------------------------------

async def run_pipeline_sse(query: str) -> AsyncGenerator[str, None]:
    """Run the Researcher → Analyst → Writer pipeline, yielding SSE events."""

    session_id = f"pipeline-{uuid.uuid4().hex[:8]}"

    # --- Step 1: Research ---
    yield _sse("stage", {"stage": "researching", "message": "Searching the web..."})

    researcher_config = build_researcher_config()
    
    # We use a chat session to handle multiple tool-call turns automatically
    chat = client.chats.create(model=MODEL_NAME, config=researcher_config)
    
    # Generate the research result
    research_response = chat.send_message(query)
    research_summary = research_response.text

    yield _sse(
        "stage",
        {"stage": "researching", "message": "Research complete", "done": True},
    )

    # --- Step 2: Analysis ---
    yield _sse("stage", {"stage": "analysing", "message": "Analysing findings..."})

    analyst_input = f"Analyse the following research:\n\n{research_summary}"
    analyst_response = client.models.generate_content(
        model=MODEL_NAME,
        contents=analyst_input,
        config=analyst_config,
    )
    
    # Parse the structured JSON output
    analysis_data = json.loads(analyst_response.text)
    analysis = AnalystOutput(**analysis_data)

    yield _sse(
        "stage",
        {"stage": "analysing", "message": "Analysis complete", "done": True},
    )

    # --- Step 3: Report ---
    yield _sse("stage", {"stage": "writing", "message": "Writing report..."})

    writer_input = (
        "Trends:\n" + "\n".join(f"- {t}" for t in analysis.trends) + "\n\n"
        "Risks:\n" + "\n".join(f"- {r}" for r in analysis.risks) + "\n\n"
        "Insights:\n" + "\n".join(f"- {i}" for i in analysis.insights)
    )
    
    writer_response = client.models.generate_content(
        model=MODEL_NAME,
        contents=writer_input,
        config=writer_config,
    )
    
    # Parse the structured JSON output
    report_data = json.loads(writer_response.text)
    report = FinalReport(**report_data)

    yield _sse(
        "stage",
        {"stage": "writing", "message": "Report ready", "done": True},
    )

    # --- Final result ---
    yield _sse("result", report.model_dump())
    yield _sse("done", {})

