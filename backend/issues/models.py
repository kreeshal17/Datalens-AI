from django.db import models
from datasets.models import Dataset


class Issue(models.Model):

    class IssueType(models.TextChoices):
        MISSING_VALUE = "MISSING_VALUE", "Missing Value"
        DUPLICATE = "DUPLICATE", "Duplicate"
        ANOMALY = "ANOMALY", "Anomaly"
        INVALID_FORMAT = "INVALID_FORMAT", "Invalid Format"

    class Severity(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"

    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name="issues"
    )

    issue_type = models.CharField(
        max_length=30,
        choices=IssueType.choices
    )
    ai_explanation = models.TextField(
    null=True,
    blank=True
)

    ai_root_cause = models.TextField(
    null=True,
    blank=True
)

    ai_recommendation = models.TextField(
    null=True,
    blank=True
)

    ai_confidence = models.FloatField(
    null=True,
    blank=True
)

    ai_suggested_value = models.TextField(
        null=True,
        blank=True,
        help_text="AI-suggested replacement value for the affected cell. "
                   "Empty for DUPLICATE issues, whose fix is to remove the row."
    )

    is_resolved = models.BooleanField(
        default=False
    )

    resolved_at = models.DateTimeField(
        null=True,
        blank=True
    )

    column = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    row = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    severity = models.CharField(
        max_length=10,
        choices=Severity.choices
    )

    description = models.TextField()

    details = models.JSONField(
        default=dict,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.issue_type} - {self.dataset.name}"