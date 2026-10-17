import json
from datetime import timedelta
from io import StringIO
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import AnalyticsEvent, GuestbookEntry, Job


class CareersSiteTests(TestCase):
    def setUp(self):
        self.active = Job.objects.create(
            title="Test chaos coordinator", department="Test Operations",
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
        self.assertContains(response, "Ayush Sharma")
        self.assertContains(response, 'id="hero-coo"')
        self.assertContains(response, "SECOND-BEST BOSS AFTER UDAI")
        self.assertContains(response, "CO-FOUNDER &amp; CHIEF OPERATING OFFICER")
        self.assertContains(response, "static/jobs/assets/ayush-sharma.png")
        self.assertContains(response, "A fictional careers portal")
        self.assertContains(response, "ANALYTICS ON BY DEFAULT")
        self.assertContains(response, 'id="analytics-toggle"')
        self.assertContains(response, 'id="guest-name"')
        self.assertContains(response, 'id="guest-input"')
        self.assertContains(response, "PUBLIC POSTS · SAMPLE ENTRIES MARKED")

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


class GuestbookEndpointTests(TestCase):
    def setUp(self):
        cache.clear()

    def post_entry(self, **payload):
        return self.client.post(
            reverse("guestbook-entries"),
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_signing_guestbook_persists_and_returns_public_entry(self):
        response = self.post_entry(name="  Ada   Lovelace ", message="  Hello, company!  ")
        self.assertEqual(response.status_code, 201)
        entry = GuestbookEntry.objects.get(is_sample=False)
        self.assertEqual((entry.author_name, entry.message), ("Ada Lovelace", "Hello, company!"))
        self.assertTrue(entry.is_visible)
        self.assertEqual(response.json()["entry"]["name"], "Ada Lovelace")
        self.assertEqual(response.json()["entry"]["message"], "Hello, company!")

        listing = self.client.get(reverse("guestbook-entries"))
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing["Cache-Control"], "no-store")
        self.assertEqual(listing.json()["entries"][0]["message"], "Hello, company!")

    def test_guestbook_shows_saved_name_and_message_as_text_data(self):
        message = "<script>alert('hello')</script>"
        self.post_entry(name="Friend", message=message)
        entries = self.client.get(reverse("guestbook-entries")).json()["entries"]
        entry = next(item for item in entries if item["name"] == "Friend")
        self.assertEqual(entry["message"], message)
        self.assertFalse(entry["is_sample"])

    def test_guestbook_rejects_blank_oversized_and_extra_fields(self):
        self.assertEqual(self.post_entry(name=" ", message="Hi").status_code, 400)
        self.assertEqual(self.post_entry(name="Friend", message=" ").status_code, 400)
        self.assertEqual(self.post_entry(name="n" * 51, message="Hi").status_code, 400)
        self.assertEqual(self.post_entry(name="Friend", message="m" * 251).status_code, 400)
        self.assertEqual(self.post_entry(name="Friend", message="Hi", email="a@b.test").status_code, 400)
        self.assertFalse(GuestbookEntry.objects.filter(is_sample=False).exists())

    def test_hidden_entries_are_not_returned(self):
        GuestbookEntry.objects.create(author_name="Hidden", message="Review pending", is_visible=False)
        entries = self.client.get(reverse("guestbook-entries")).json()["entries"]
        self.assertNotIn("Hidden", [entry["name"] for entry in entries])
        self.assertTrue(all(entry["is_sample"] for entry in entries))

    def test_fictional_sample_entries_are_visible_with_staggered_timestamps(self):
        samples = GuestbookEntry.objects.filter(is_sample=True)
        self.assertEqual(samples.count(), 5)
        timestamps = list(samples.values_list("created_at", flat=True))
        self.assertGreater(max(timestamps) - min(timestamps), timedelta(days=2))
        response = self.client.get(reverse("guestbook-entries"))
        sample_entries = [entry for entry in response.json()["entries"] if entry["is_sample"]]
        self.assertEqual(len(sample_entries), 5)
        self.assertTrue(all(entry["created_at"] for entry in sample_entries))

    def test_guestbook_requires_csrf_for_posts(self):
        client = Client(enforce_csrf_checks=True)
        client.get(reverse("home"))
        payload = json.dumps({"name": "Friend", "message": "Hi"})
        rejected = client.post(reverse("guestbook-entries"), data=payload, content_type="application/json")
        self.assertEqual(rejected.status_code, 403)
        token = client.cookies["csrftoken"].value
        accepted = client.post(
            reverse("guestbook-entries"), data=payload, content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(accepted.status_code, 201)


class SeedJobsCommandTests(TestCase):
    def test_seed_runs_once_and_preserves_admin_edits(self):
        call_command("seed_jobs", stdout=StringIO())
        self.assertEqual(Job.objects.count(), 35)
        featured = Job.objects.first()
        self.assertEqual(featured.title, "BITCHY MANAGER")
        self.assertFalse(Job.objects.filter(title__in=["COO OF FUCKERY", "FUCKERY POTTER LIKE HARRY POTTER"]).exists())

        featured.title = "Admin-edited listing"
        featured.save()
        call_command("seed_jobs", stdout=StringIO())
        self.assertEqual(Job.objects.count(), 35)
        self.assertEqual(Job.objects.get(pk=featured.pk).title, "Admin-edited listing")


class AnalyticsEndpointTests(TestCase):
    def setUp(self):
        cache.clear()
        self.active = Job.objects.create(
            title="Anonymous test role", department="Operations", salary="Potatoes",
            lpa=10, experience=0, location="Remote", vibe="Questionable",
            sandwich="Expert", damage="Severe", printer="Yes",
        )

    def post_event(self, **overrides):
        payload = {
            "analytics_enabled": True,
            "visitor_id": str(uuid4()),
            "event_type": "filter",
            "event_value": "location:Remote",
        }
        payload.update(overrides)
        return self.client.post(reverse("analytics-event"), data=json.dumps(payload), content_type="application/json")

    def test_valid_opted_in_categorical_event_is_saved(self):
        visitor_id = uuid4()
        response = self.post_event(visitor_id=str(visitor_id))
        event = AnalyticsEvent.objects.get()
        self.assertEqual(response.status_code, 204)
        self.assertEqual((event.visitor_id, event.event_type, event.event_value), (visitor_id, "filter", "location:Remote"))

    def test_disabled_analytics_is_not_saved(self):
        self.assertEqual(self.post_event(analytics_enabled=False).status_code, 403)
        self.assertEqual(self.post_event(analytics_enabled=None).status_code, 403)
        self.assertFalse(AnalyticsEvent.objects.exists())

    def test_free_text_and_unknown_values_are_rejected(self):
        response = self.post_event(event_type="choice", event_value="nickname:real name")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(AnalyticsEvent.objects.exists())

    def test_job_view_accepts_only_active_listing_ids(self):
        self.assertEqual(self.post_event(event_type="job_view", event_value=str(self.active.pk)).status_code, 204)
        self.active.is_active = False
        self.active.save()
        self.assertEqual(self.post_event(event_type="job_view", event_value=str(self.active.pk)).status_code, 400)
        self.assertEqual(AnalyticsEvent.objects.count(), 1)

    def test_malformed_visitor_id_returns_400(self):
        self.assertEqual(self.post_event(visitor_id=[]).status_code, 400)
        self.assertFalse(AnalyticsEvent.objects.exists())

    def test_session_rate_limit_caps_events_at_60_per_minute(self):
        visitor_id = str(uuid4())
        responses = [self.post_event(visitor_id=visitor_id) for _ in range(61)]
        self.assertEqual(responses[-1].status_code, 429)
        self.assertEqual(AnalyticsEvent.objects.filter(visitor_id=visitor_id).count(), 60)

    def test_address_rate_limit_catches_rotating_session_ids(self):
        responses = [self.post_event() for _ in range(121)]
        self.assertEqual(responses[-1].status_code, 429)
        self.assertEqual(AnalyticsEvent.objects.count(), 120)

    def test_old_events_are_pruned_during_page_traffic(self):
        cache.clear()
        old_event = AnalyticsEvent.objects.create(visitor_id=uuid4(), event_type="section", event_value="home")
        AnalyticsEvent.objects.filter(pk=old_event.pk).update(created_at=timezone.now() - timedelta(days=91))
        self.client.get(reverse("home"))
        self.assertFalse(AnalyticsEvent.objects.exists())

    def test_csrf_protection_is_active_for_event_endpoint(self):
        client = Client(enforce_csrf_checks=True)
        client.get(reverse("home"))
        payload = {"analytics_enabled": True, "visitor_id": str(uuid4()), "event_type": "section", "event_value": "home"}
        rejected = client.post(reverse("analytics-event"), data=json.dumps(payload), content_type="application/json")
        self.assertEqual(rejected.status_code, 403)
        token = client.cookies["csrftoken"].value
        accepted = client.post(reverse("analytics-event"), data=json.dumps(payload), content_type="application/json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(accepted.status_code, 204)
