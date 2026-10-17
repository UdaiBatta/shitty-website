from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("jobs/", views.job_list, name="job-list"),
    path("analytics/events/", views.analytics_event, name="analytics-event"),
    path("guestbook/", views.guestbook_entries, name="guestbook-entries"),
    path("", views.home, name="home"),
]
