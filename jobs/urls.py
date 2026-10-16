from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("jobs/", views.job_list, name="job-list"),
    path("", views.home, name="home"),
]
