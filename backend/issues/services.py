import re

import pandas as pd
from django.db.models import Count
from sklearn.ensemble import IsolationForest

from .models import Issue


# Higher-severity issues cost more of the score than low-severity ones.
SEVERITY_WEIGHT = {
    Issue.Severity.HIGH: 3,
    Issue.Severity.MEDIUM: 2,
    Issue.Severity.LOW: 1,
}


def update_quality_score(dataset):
    """
    Recomputes dataset.quality_score from its currently *unresolved*
    issues (resolved ones no longer count against it), weighted by
    severity relative to the dataset's total cell count. 100 means no
    known problems; it drifts toward 0 as issues pile up or get more
    severe. Saves the result and returns it.
    """

    total_cells = dataset.row_count * dataset.column_count

    if total_cells == 0:
        score = 100.0

    else:
        counts = (
            Issue.objects
            .filter(dataset=dataset, is_resolved=False)
            .values("severity")
            .annotate(count=Count("id"))
        )

        penalty = sum(
            SEVERITY_WEIGHT.get(row["severity"], 1) * row["count"]
            for row in counts
        )

        score = max(0.0, 100.0 - (penalty / total_cells * 100))

    score = round(score, 1)

    dataset.quality_score = score
    dataset.save(update_fields=["quality_score"])

    return score


class IssueDetector:

    def __init__(self, dataset):

        self.dataset = dataset

        self.df = pd.read_csv(
            dataset.file.path
        )

    def run(self):

        issues = []

        issues.extend(
            self.detect_missing_values()
        )

        issues.extend(
            self.detect_duplicates()
        )

        issues.extend(
            self.detect_anomalies()
        )

        issues.extend(
            self.detect_invalid_formats()
        )

        update_quality_score(self.dataset)

        return issues

    def detect_missing_values(self):

        issues = []

        for column in self.df.columns:

            missing_rows = self.df[
                self.df[column].isna()
            ].index.tolist()

            for row in missing_rows:

                issue = Issue.objects.create(
                    dataset=self.dataset,
                    issue_type=Issue.IssueType.MISSING_VALUE,
                    column=column,
                    row=row,
                    severity=Issue.Severity.MEDIUM,
                    description=f"Missing value detected in {column}",
                    details={
                        "column": column,
                        "original_value": None
                    }
                )

                issues.append(issue)

        return issues

    def detect_duplicates(self):

        issues = []

        duplicate_rows = self.df[
            self.df.duplicated()
        ].index.tolist()

        for row in duplicate_rows:

            issue = Issue.objects.create(
                dataset=self.dataset,
                issue_type=Issue.IssueType.DUPLICATE,
                row=row,
                severity=Issue.Severity.MEDIUM,
                description="Duplicate row detected",
                details={
                    "duplicate_row": row
                }
            )

            issues.append(issue)

        return issues

    def detect_anomalies(self):
        """
        Flags anomalous rows using Isolation Forest across all numeric
        columns at once, instead of checking each column in isolation
        (like the old IQR-fence approach did). This also catches rows
        that are only strange in combination - e.g. age=8 and
        income=200k are each unremarkable alone, but odd together.
        """

        issues = []

        numeric_columns = self.df.select_dtypes(
            include="number"
        ).columns

        if len(numeric_columns) == 0:
            return issues

        numeric_df = self.df[numeric_columns]

        # Isolation Forest can't take NaNs. Fill them with the column
        # median just for scoring purposes - this leaves self.df (and
        # every other detector) untouched.
        imputed = numeric_df.fillna(numeric_df.median())

        # Isolation Forest needs enough rows to learn what "normal"
        # looks like; on tiny datasets it isn't meaningful.
        if len(imputed) < 10:
            return issues

        # A fixed, conservative contamination rate keeps this from
        # flagging a large chunk of a small/well-behaved dataset -
        # "auto" tends to be much noisier on smaller samples.
        model = IsolationForest(
            contamination=0.05,
            random_state=42,
        )

        predictions = model.fit_predict(imputed)
        scores = model.decision_function(imputed)

        # Isolation Forest only judges a row as a whole, so z-scores
        # are used to point at which column(s) actually drove that
        # row's anomaly - useful context for the issue record.
        column_means = imputed.mean()
        column_stds = imputed.std().replace(0, 1)
        z_scores = (imputed - column_means) / column_stds

        for position, is_outlier in enumerate(predictions):

            if is_outlier != -1:
                continue

            row = imputed.index[position]

            row_z_scores = z_scores.loc[row].abs().sort_values(
                ascending=False
            )
            top_column = row_z_scores.index[0]

            contributing_columns = row_z_scores[
                row_z_scores > 1
            ].index.tolist()

            value = self.df.loc[row, top_column]

            issue = Issue.objects.create(
                dataset=self.dataset,
                issue_type=Issue.IssueType.ANOMALY,
                column=str(top_column),
                row=int(row),
                severity=Issue.Severity.HIGH,
                description=(
                    f"Anomalous row detected (Isolation Forest), "
                    f"most driven by {top_column}"
                ),
                details={
                    "column": str(top_column),
                    "value": value.item() if hasattr(value, "item") else value,
                    "anomaly_score": float(scores[position]),
                    "contributing_columns": [
                        str(c) for c in contributing_columns
                    ],
                }
            )

            issues.append(issue)

        return issues

    def detect_invalid_formats(self):

        issues = []

        for column in self.df.columns:

            column_name = column.lower().strip()

            if "email" not in column_name:
                continue

            for row, value in self.df[column].items():

                if pd.isna(value):
                    continue

                value = str(value).strip()

                if not self.is_valid_email(value):

                    issue = Issue.objects.create(
                        dataset=self.dataset,
                        issue_type=Issue.IssueType.INVALID_FORMAT,
                        column=column,
                        row=row,
                        severity=Issue.Severity.MEDIUM,
                        description=f"Invalid email format detected in {column}",
                        details={
                            "column": column,
                            "original_value": value
                        }
                    )

                    issues.append(issue)

        return issues

    @staticmethod
    def is_valid_email(value):

        pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

        return bool(
            re.match(pattern, value)
        )