from typing import TypedDict

import pandas as pd
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END

from issues.models import Issue
from .llm import llm


class AIAnalysis(BaseModel):
    explanation: str = Field(
        description="Explain the data quality issue clearly"
    )

    root_cause: str = Field(
        description="Likely reason why this issue occurred"
    )

    recommendation: str = Field(
        description="Recommended action to fix or handle the issue"
    )

    confidence: float = Field(
        description="Confidence in the analysis between 0 and 1"
    )

    suggested_value: str | None = Field(
        default=None,
        description=(
            "The exact corrected value that should replace the problematic "
            "cell, as plain text (e.g. '42', 'jane@example.com'). This gets "
            "written directly into the dataset, so commit to one concrete "
            "value - if `recommendation` proposes a specific replacement or "
            "placeholder, put that same value here too, don't leave this "
            "null while only describing it in `recommendation`. Only leave "
            "it null for a DUPLICATE issue (the fix there is to remove the "
            "row) or when truly no reasonable value exists."
        )
    )


class AnalysisState(TypedDict):
    issue_id: int
    issue: str
    analysis: AIAnalysis | None


def load_issue(state: AnalysisState):

    issue = Issue.objects.get(
        id=state["issue_id"]
    )

    column_context = ""

    if issue.column:

        try:
            df = pd.read_csv(issue.dataset.file.path)

            if issue.column in df.columns:

                series = df[issue.column].dropna()

                if pd.api.types.is_numeric_dtype(series) and not series.empty:

                    column_context = (
                        f"Other values in this column -> "
                        f"mean: {series.mean():.4g}, "
                        f"median: {series.median():.4g}, "
                        f"min: {series.min():.4g}, "
                        f"max: {series.max():.4g}"
                    )

                elif not series.empty:

                    mode = series.mode()

                    if not mode.empty:
                        column_context = (
                            f"Most common value in this column: {mode.iloc[0]!r}"
                        )

        except Exception:
            column_context = ""

    issue_text = f"""
    Issue Type: {issue.issue_type}
    Column: {issue.column}
    Row: {issue.row}
    Severity: {issue.severity}
    Description: {issue.description}
    Details: {issue.details}
    {column_context}
    """

    return {
        "issue": issue_text
    }


def analyze_issue(state: AnalysisState):

    structured_llm = llm.with_structured_output(
        AIAnalysis
    )

    prompt = f"""
    You are a data quality analyst.

    Analyze this data quality issue:

    {state["issue"]}

    Provide:
    1. A clear explanation
    2. The likely root cause
    3. A recommendation to fix it
    4. Your confidence from 0 to 1
    5. suggested_value: the exact value that should replace the problematic
       cell, grounded in the other values shown for this column, if any.
       This will be written directly into the dataset, so commit to one
       concrete value rather than describing options in prose - if your
       recommendation proposes a specific replacement or placeholder (e.g.
       a statistical imputation, a corrected format, a sentinel like
       "unknown"), put that exact value here too, don't leave it null while
       describing it only in the recommendation text.
       Only leave suggested_value null for a DUPLICATE issue (the fix there
       is to remove the row) or in the rare case no reasonable value or
       placeholder exists at all.
    """

    response = structured_llm.invoke(prompt)

    return {
        "analysis": response
    }


def save_analysis(state: AnalysisState):

    issue = Issue.objects.get(
        id=state["issue_id"]
    )

    analysis = state["analysis"]

    issue.ai_explanation = analysis.explanation
    issue.ai_root_cause = analysis.root_cause
    issue.ai_recommendation = analysis.recommendation
    issue.ai_confidence = analysis.confidence
    issue.ai_suggested_value = analysis.suggested_value

    issue.save()

    return {}


graph_builder = StateGraph(AnalysisState)


graph_builder.add_node(
    "load_issue",
    load_issue
)

graph_builder.add_node(
    "analyze_issue",
    analyze_issue
)

graph_builder.add_node(
    "save_analysis",
    save_analysis
)


graph_builder.add_edge(
    START,
    "load_issue"
)

graph_builder.add_edge(
    "load_issue",
    "analyze_issue"
)

graph_builder.add_edge(
    "analyze_issue",
    "save_analysis"
)

graph_builder.add_edge(
    "save_analysis",
    END
)


graph = graph_builder.compile()