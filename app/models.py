from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    query: str = Field(description="The research question to investigate")


class AnalystOutput(BaseModel):
    trends: list[str] = Field(description="Key trends identified from the research")
    risks: list[str] = Field(description="Potential risks or challenges")
    insights: list[str] = Field(description="Actionable insights and observations")


class FinalReport(BaseModel):
    executive_summary: str = Field(
        description="A concise executive summary (2-3 paragraphs)"
    )
    markdown_report: str = Field(
        description="A detailed markdown-formatted report with sections and bullet points"
    )
    follow_up_questions: list[str] = Field(
        description="3-5 follow-up questions for further research"
    )
