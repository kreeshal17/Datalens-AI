from django.urls import path
from .views import DatasetView,AnalyzeDatasetView,DownloadDatasetView


urlpatterns = [
    path("", DatasetView.as_view(), name="datasets"),
    path(
    "<slug:slug>/analyze/",
    AnalyzeDatasetView.as_view(),
    name="analyze-dataset"
),
    path(
        "<slug:slug>/download/",
        DownloadDatasetView.as_view(),
        name="download-dataset"
    ),

]