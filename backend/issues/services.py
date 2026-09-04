import re

import pandas as pd
from django.db.models import Count
from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import KNNImputer
from sklearn.metrics.pairwise import cosine_similarity

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

        numeric_columns = self.df.select_dtypes(
            include="number"
        ).columns

        imputed_values = self._knn_impute_numeric(numeric_columns)

        for column in self.df.columns:

            missing_rows = self.df[
                self.df[column].isna()
            ].index.tolist()

            for row in missing_rows:

                suggested_value = None

                if column in imputed_values.columns:

                    candidate = imputed_values.loc[row, column]

                    if not pd.isna(candidate):
                        suggested_value = round(float(candidate), 4)

                issue = Issue.objects.create(
                    dataset=self.dataset,
                    issue_type=Issue.IssueType.MISSING_VALUE,
                    column=column,
                    row=row,
                    severity=Issue.Severity.MEDIUM,
                    description=f"Missing value detected in {column}",
                    # Pre-fill numeric suggestions from KNN imputation so
                    # "Apply Fix" works immediately, without waiting on an
                    # LLM call. Non-numeric columns are left for AI analysis.
                    ai_suggested_value=(
                        str(suggested_value)
                        if suggested_value is not None else None
                    ),
                    details={
                        "column": column,
                        "original_value": None,
                        "suggested_value": suggested_value,
                        "suggested_value_source": (
                            "knn_imputer" if suggested_value is not None
                            else None
                        ),
                    }
                )

                issues.append(issue)

        return issues

    def _knn_impute_numeric(self, numeric_columns):
        """
        Estimates missing numeric cells with a KNN Imputer: each missing
        value is filled from the average of its k nearest rows (by their
        other numeric columns), which is a better guess than a flat
        column mean/median. Returns a DataFrame of the same shape as
        self.df[numeric_columns] with NaNs filled in; non-numeric columns
        aren't included.
        """

        if len(numeric_columns) == 0:
            return pd.DataFrame(index=self.df.index)

        numeric_df = self.df[numeric_columns]

        # Needs at least a couple of rows to have any neighbors to
        # learn from.
        if len(numeric_df) < 2:
            return pd.DataFrame(index=self.df.index)

        n_neighbors = min(5, len(numeric_df) - 1)

        imputer = KNNImputer(n_neighbors=n_neighbors)

        imputed_array = imputer.fit_transform(numeric_df)

        return pd.DataFrame(
            imputed_array,
            columns=numeric_columns,
            index=numeric_df.index,
        )

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
                    "duplicate_row": row,
                    "match_type": "exact",
                }
            )

            issues.append(issue)

        # Exact matching only catches rows that are byte-for-byte
        # identical. Rows already caught above are excluded so the same
        # row never gets flagged twice.
        issues.extend(
            self._detect_near_duplicates(exclude_rows=set(duplicate_rows))
        )

        return issues

    def _detect_near_duplicates(self, exclude_rows, threshold=0.9):
        """
        Catches rows that are effectively the same record with small
        differences - a typo, different casing, extra whitespace - which
        exact matching above misses (e.g. "Jon Smith" vs "John Smith").

        Each row is flattened into one text blob, TF-IDF vectorized, and
        compared pairwise with cosine similarity. A row scoring at or
        above `threshold` against an earlier row is flagged as a
        DUPLICATE, same as an exact match, so it's handled the same way
        by the rest of the app (e.g. "Apply Fix" removes the row).
        """

        issues = []

        candidate_rows = self.df.drop(
            index=list(exclude_rows), errors="ignore"
        )

        # Comparing every row against every other row is O(n^2) - fine
        # for typical dataset sizes, but capped to avoid a huge/slow
        # comparison on very large uploads.
        if len(candidate_rows) < 2 or len(candidate_rows) > 3000:
            return issues

        row_text = candidate_rows.fillna("").astype(str).agg(" ".join, axis=1)

        # Character n-grams (rather than whole-word tokens) are what
        # make this robust to typos like "Jon" vs "John" - a one-letter
        # edit still shares most of its n-grams, whereas word-level
        # TF-IDF would treat "Jon" and "John" as two unrelated tokens.
        vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))

        try:
            matrix = vectorizer.fit_transform(row_text)
        except ValueError:
            # e.g. every row is blank - nothing meaningful to compare.
            return issues

        similarity = cosine_similarity(matrix)

        index_list = candidate_rows.index.tolist()
        already_flagged = set()

        for i in range(len(index_list)):

            if index_list[i] in already_flagged:
                continue

            for j in range(i + 1, len(index_list)):

                row = index_list[j]

                if row in already_flagged:
                    continue

                score = similarity[i, j]

                if score < threshold:
                    continue

                issue = Issue.objects.create(
                    dataset=self.dataset,
                    issue_type=Issue.IssueType.DUPLICATE,
                    row=int(row),
                    severity=Issue.Severity.LOW,
                    description=(
                        f"Near-duplicate of row {index_list[i]} detected "
                        f"({score:.0%} similar)"
                    ),
                    details={
                        "duplicate_row": int(row),
                        "matched_row": int(index_list[i]),
                        "match_type": "near",
                        "similarity": round(float(score), 4),
                    }
                )

                issues.append(issue)
                already_flagged.add(row)

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