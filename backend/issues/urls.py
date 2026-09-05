from django.urls import path

from .views import (
    DatasetIssueView,
    AnalyzeIssueView,
    IssueAnalysisView,
    DatasetIssueSummaryView,
    ApplyIssueFixView,
    ApplyAllIssuesFixView,
)


urlpatterns = [

    path(
        "<slug:slug>/issues/",
        DatasetIssueView.as_view(),
        name="dataset-issues"
    ),

    path(
        "<int:issue_id>/analyze/",
        AnalyzeIssueView.as_view(),
        name="analyze-issue"
    ),

    path(
        "<int:issue_id>/analysis/",
        IssueAnalysisView.as_view(),
        name="issue-analysis"
    ),

    path(
        "<int:issue_id>/apply-fix/",
        ApplyIssueFixView.as_view(),
        name="apply-issue-fix"
    ),

    path(
        "<slug:slug>/apply-all/",
        ApplyAllIssuesFixView.as_view(),
        name="apply-all-issues-fix"
    ),

    path(
        "<slug:slug>/summary/",
        DatasetIssueSummaryView.as_view(),
        name="dataset-issue-summary"
    ),
]