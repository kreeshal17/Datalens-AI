from django.http import FileResponse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from issues.models import Issue
from issues.services import IssueDetector

from .models import Dataset
from .serializers import DatasetSerializer

from profiling.services import ProfilerService

from ai_analysis.graph import graph


class DatasetView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = DatasetSerializer(
            data=request.data
        )

        if serializer.is_valid():

            dataset = serializer.save(
                owner=request.user
            )

            ProfilerService(dataset).run()

            IssueDetector(dataset).run()

            return Response(
                DatasetSerializer(dataset).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def get(self, request):

        datasets = Dataset.objects.filter(
            owner=request.user
        )

        serializer = DatasetSerializer(
            datasets,
            many=True
        )

        return Response(serializer.data)


class AnalyzeDatasetView(APIView):
    """
    Runs AI analysis on every unresolved issue in a dataset, one LLM call
    per issue (the graph doesn't support batching multiple issues into a
    single call). Already-resolved issues are skipped - there's nothing
    left to act on for those.

    Each issue is analyzed independently: one failing (e.g. a transient
    API error) doesn't abort the rest of the batch, unlike a plain loop
    that re-raises - it's reported back per-issue instead, alongside
    every issue that did succeed.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, slug):

        try:
            dataset = Dataset.objects.get(
                owner=request.user,
                slug=slug
            )

        except Dataset.DoesNotExist:
            return Response(
                {"error": "Dataset not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        issues = Issue.objects.filter(
            dataset=dataset,
            is_resolved=False
        )

        if not issues.exists():

            return Response({
                "dataset": dataset.name,
                "analyzed_count": 0,
                "failed_count": 0,
                "issues": [],
                "failed": [],
            })

        analyzed = []
        failed = []

        for issue in issues:

            try:

                graph.invoke({
                    "issue_id": issue.id,
                    "issue": "",
                    "analysis": None
                })

            except Exception as error:

                failed.append({
                    "issue_id": issue.id,
                    "details": str(error),
                })

                continue

            issue.refresh_from_db()

            analyzed.append({
                "issue_id": issue.id,
                "ai_explanation": issue.ai_explanation,
                "ai_root_cause": issue.ai_root_cause,
                "ai_recommendation": issue.ai_recommendation,
                "ai_confidence": issue.ai_confidence,
            })

        return Response({
            "dataset": dataset.name,
            "analyzed_count": len(analyzed),
            "failed_count": len(failed),
            "issues": analyzed,
            "failed": failed,
        })


class DownloadDatasetView(APIView):
    """
    Streams the dataset's current CSV file - reflecting any fixes applied
    through ApplyIssueFixView, since those write directly into this same
    file. Goes through Django (not a raw /media/ URL) so ownership is
    actually checked; nginx's /media/ location bypasses auth entirely.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, slug):

        try:
            dataset = Dataset.objects.get(
                owner=request.user,
                slug=slug
            )

        except Dataset.DoesNotExist:
            return Response(
                {"error": "Dataset not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        response = FileResponse(
            dataset.file.open("rb"),
            as_attachment=True,
            filename=f"{dataset.slug}.csv",
            content_type="text/csv"
        )

        return response