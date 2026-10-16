import json
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Job


class CareersSiteTests(TestCase):
    def setUp(self):
        self.active = Job.objects.create(
            title="COO OF FUCKERY", department="Executive Chaos Operations",
            salary="₹9 Crore + Unlimited Nonsense", lpa=900, experience=0,
            requirements=["Cause a fictional amount of chaos."], location="Remote",
            vibe="Questionable", sandwich="Expert", damage="Severe", printer="Yes",
        )
        Job.objects.create(
            title="Hidden listing", department="Test", salary="None", lpa=0,
            experience=0, location="Remote", vibe="Questionable", sandwich="Expert",
            damage="Severe", printer="No", is_active=False,
        )

    def test_home_serves_existing_careers_page(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Udai Batta")
        self.assertContains(response, "A fictional careers portal")

    def test_api_returns_active_editable_listing_fields_without_applicant_data(self):
        response = self.client.get(reverse("job-list"))
        payload = json.loads(response.content)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual([job["id"] for job in payload["jobs"]], [self.active.pk])
        self.assertEqual(payload["jobs"][0]["requirements"], ["Cause a fictional amount of chaos."])
        self.assertNotIn("email", payload["jobs"][0])
        self.assertNotIn("nickname", payload["jobs"][0])
        self.active.is_active = False
        self.active.save()
        self.assertEqual(self.client.get(reverse("job-list")).json(), {"jobs": []})

    def test_admin_can_update_job_listings(self):
        user = get_user_model().objects.create_superuser("admin", "admin@example.test", "test-password")
        self.client.force_login(user)
        response = self.client.post(reverse("admin:jobs_job_change", args=[self.active.pk]), {
            "title": "Admin-managed position", "department": self.active.department,
            "salary": self.active.salary, "lpa": "900", "experience": "0",
            "requirements": '["Cause a fictional amount of chaos."]', "location": "Remote",
            "employment_type": "Full-time", "vibe": "Questionable", "sandwich": "Expert",
            "damage": "Severe", "printer": "Yes", "applicants": "1,11,030",
            "sort_order": "0", "is_active": "on", "_save": "Save",
        })
        self.assertEqual(response.status_code, 302)
        self.active.refresh_from_db()
        self.assertEqual(self.active.title, "Admin-managed position")

    def test_requirements_must_be_a_list_of_strings(self):
        self.active.requirements = {"unsafe": "not a list"}
        with self.assertRaises(ValidationError):
            self.active.full_clean()

    def test_health_endpoint(self):
        response = self.client.get(reverse("health"))
        self.assertEqual((response.status_code, response.content), (200, b"ok"))


class SeedJobsCommandTests(TestCase):
    def test_seed_runs_once_and_preserves_admin_edits(self):
        call_command("seed_jobs", stdout=StringIO())
        self.assertEqual(Job.objects.count(), 37)
        featured = Job.objects.first()
        self.assertEqual(featured.title, "COO OF FUCKERY")

        featured.title = "Admin-edited listing"
        featured.save()
        call_command("seed_jobs", stdout=StringIO())
        self.assertEqual(Job.objects.count(), 37)
        self.assertEqual(Job.objects.get(pk=featured.pk).title, "Admin-edited listing")
