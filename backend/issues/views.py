import pandas as pd

from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from datasets.models import Dataset
from profiling.services import ProfilerService

from .models import Issue
from .serializers import IssueSerializer
from .services import IssueDetector, update_quality_score

from ai_analysis.graph import graph


class DatasetIssueView(APIView):

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

        issues = Issue.objects.filter(
            dataset=dataset
        )

        serializer = IssueSerializer(
            issues,
            many=True
        )

        return Response(serializer.data)


class AnalyzeIssueView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, issue_id):

        try:
            issue = Issue.objects.get(
                id=issue_id,
                dataset__owner=request.user
            )

        except Issue.DoesNotExist:
            return Response(
                {"error": "Issue not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        try:

            graph.invoke({
                "issue_id": issue.id,
                "issue": "",
                "analysis": None
            })

        except Exception as error:

            return Response(
                {
                    "error": "AI analysis failed",
                    "details": str(error)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        issue.refresh_from_db()

        serializer = IssueSerializer(issue)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class IssueAnalysisView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, issue_id):

        try:
            issue = Issue.objects.get(
                id=issue_id,
                dataset__owner=request.user
            )

        except Issue.DoesNotExist:
            return Response(
                {"error": "Issue not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            "issue_id": issue.id,
            "ai_explanation": issue.ai_explanation,
            "ai_root_cause": issue.ai_root_cause,
            "ai_recommendation": issue.ai_recommendation,
            "ai_confidence": issue.ai_confidence,
        })


class DatasetIssueSummaryView(APIView):

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

        issues = Issue.objects.filter(
            dataset=dataset
        )

        summary = {
            "total": issues.count(),

            "missing_values": issues.filter(
                issue_type=Issue.IssueType.MISSING_VALUE
            ).count(),

            "duplicates": issues.filter(
                issue_type=Issue.IssueType.DUPLICATE
            ).count(),

            "anomalies": issues.filter(
                issue_type=Issue.IssueType.ANOMALY
            ).count(),

            "invalid_formats": issues.filter(
                issue_type=Issue.IssueType.INVALID_FORMAT
            ).count(),

            "high": issues.filter(
                severity=Issue.Severity.HIGH
            ).count(),

            "medium": issues.filter(
                severity=Issue.Severity.MEDIUM
            ).count(),

            "low": issues.filter(
                severity=Issue.Severity.LOW
            ).count(),
        }

        return Response(summary)


class ApplyIssueFixView(APIView):
    """
    Applies the AI-suggested fix for a single issue directly to the
    dataset's CSV file:

    - For value-level issues (missing value, invalid format, anomaly),
      the affected cell is overwritten with `ai_suggested_value`.
    - For DUPLICATE issues, the offending row is removed instead, since
      there is no single value to correct.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, issue_id):

        try:
            issue = Issue.objects.get(
                id=issue_id,
                dataset__owner=request.user
            )

        except Issue.DoesNotExist:
            return Response(
                {"error": "Issue not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if issue.is_resolved:
            return Response(
                {"error": "This issue has already been fixed"},
                status=status.HTTP_400_BAD_REQUEST
            )

        is_duplicate = issue.issue_type == Issue.IssueType.DUPLICATE

        if not is_duplicate and not issue.ai_suggested_value:
            return Response(
                {
                    "error": "No AI suggestion available yet. "
                             "Run AI analysis on this issue first."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        dataset = issue.dataset

        try:
            df = pd.read_csv(dataset.file.path)

        except Exception as error:
            return Response(
                {
                    "error": "Unable to read dataset file",
                    "details": str(error)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        if issue.row is None or issue.row not in df.index:
            return Response(
                {
                    "error": "The row referenced by this issue no longer "
                             "exists. Try re-analyzing the dataset."
                },
                status=status.HTTP_409_CONFLICT
            )

        applied_value = None

        if is_duplicate:

            df = df.drop(index=issue.row)

        else:

            if not issue.column or issue.column not in df.columns:
                return Response(
                    {
                        "error": "The column referenced by this issue "
                                 "no longer exists."
                    },
                    status=status.HTTP_409_CONFLICT
                )

            applied_value = self._cast_value(
                df[issue.column].dtype,
                issue.ai_suggested_value
            )

            df.loc[issue.row, issue.column] = applied_value

        df.to_csv(dataset.file.path, index=False)

        issue.is_resolved = True
        issue.resolved_at = timezone.now()

        issue.save(
            update_fields=["is_resolved", "resolved_at"]
        )

        rescanned = False

        if is_duplicate:

            # Removing a row shifts the position of every row after it,
            # so any other unresolved issue's stored row number is now
            # unreliable. Drop them and re-detect against the updated
            # file instead of leaving stale row references around.
            Issue.objects.filter(
                dataset=dataset,
                is_resolved=False
            ).exclude(
                id=issue.id
            ).delete()

            ProfilerService(dataset).run()
            IssueDetector(dataset).run()

            rescanned = True

        else:

            ProfilerService(dataset).run()

            # The duplicate branch already gets this from IssueDetector.run()
            # above; a plain value fix needs it recomputed explicitly since
            # a resolved issue should stop counting against the score.
            update_quality_score(dataset)

        return Response({
            "issue_id": issue.id,
            "issue_type": issue.issue_type,
            "applied_value": applied_value,
            "is_resolved": True,
            "resolved_at": issue.resolved_at,
            "rescanned": rescanned,
            "quality_score": dataset.quality_score,
        })

    @staticmethod
    def _cast_value(dtype, raw_value):

        raw_value = str(raw_value).strip()

        try:

            if pd.api.types.is_integer_dtype(dtype):
                return int(round(float(raw_value)))

            if pd.api.types.is_float_dtype(dtype):
                return float(raw_value)

        except (TypeError, ValueError):
            pass

        return raw_value


class ApplyAllIssuesFixView(APIView):
    """
    Applies every currently-fixable unresolved issue for a dataset in one
    request, instead of one at a time via ApplyIssueFixView:

    - DUPLICATE issues: every flagged row is collected up front and
      dropped from the dataframe in a single `df.drop(index=[...])` call
      at the end, rather than one row at a time - dropping them
      one-by-one (like the single-issue endpoint does) would shift every
      later row's index out from under the rest of this same batch.
    - Other issues that already have an `ai_suggested_value` (numeric
      missing values get one automatically from KNN imputation; anything
      else needs AI analysis run on it first) get that value written
      into their cell.
    - Issues with no fix available yet are left untouched and reported
      back as skipped, rather than silently doing nothing.

    If anything was actually fixed, the dataset is re-profiled and fully
    rescanned for issues afterward - same reasoning as the single-issue
    endpoint's duplicate-removal path: row numbers shift, so every
    remaining unresolved issue's row/column reference is unreliable and
    needs to be regenerated fresh rather than left stale.
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

        issues = list(
            Issue.objects.filter(
                dataset=dataset,
                is_resolved=False
            )
        )

        if not issues:
            return Response({
                "fixed_count": 0,
                "skipped_count": 0,
                "skipped": [],
                "quality_score": dataset.quality_score,
            })

        try:
            df = pd.read_csv(dataset.file.path)

        except Exception as error:
            return Response(
                {
                    "error": "Unable to read dataset file",
                    "details": str(error)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        rows_to_drop = set()
        fixed_issues = []
        skipped = []

        for issue in issues:

            is_duplicate = issue.issue_type == Issue.IssueType.DUPLICATE

            if issue.row is None or issue.row not in df.index:
                skipped.append({
                    "issue_id": issue.id,
                    "reason": "The row referenced by this issue no "
                              "longer exists.",
                })
                continue

            if is_duplicate:
                rows_to_drop.add(issue.row)
                fixed_issues.append(issue)
                continue

            if not issue.ai_suggested_value:
                skipped.append({
                    "issue_id": issue.id,
                    "reason": "No AI suggestion available yet - run AI "
                              "analysis on this issue first.",
                })
                continue

            if not issue.column or issue.column not in df.columns:
                skipped.append({
                    "issue_id": issue.id,
                    "reason": "The column referenced by this issue no "
                              "longer exists.",
                })
                continue

            df.loc[issue.row, issue.column] = ApplyIssueFixView._cast_value(
                df[issue.column].dtype,
                issue.ai_suggested_value
            )

            fixed_issues.append(issue)

        if rows_to_drop:
            df = df.drop(index=list(rows_to_drop))

        if fixed_issues:

            df.to_csv(dataset.file.path, index=False)

            now = timezone.now()

            for issue in fixed_issues:
                issue.is_resolved = True
                issue.resolved_at = now

            Issue.objects.bulk_update(
                fixed_issues,
                ["is_resolved", "resolved_at"]
            )

            # Every other unresolved issue (including ones just skipped
            # above) points at a row/column in the *old* file - once rows
            # have shifted or values changed, those references can no
            # longer be trusted. Clear them and let a fresh scan below
            # regenerate accurate ones, exactly like the single-issue
            # endpoint does after a duplicate row removal.
            Issue.objects.filter(
                dataset=dataset,
                is_resolved=False
            ).delete()

            ProfilerService(dataset).run()
            IssueDetector(dataset).run()

            dataset.refresh_from_db()

        return Response({
            "fixed_count": len(fixed_issues),
            "skipped_count": len(skipped),
            "skipped": skipped,
            "quality_score": dataset.quality_score,
        })