import json
import hashlib
from datetime import timedelta
from uuid import UUID

from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import AnalyticsEvent, GuestbookEntry, Job


def prune_old_analytics():
    if cache.add("careers-analytics-retention-cleanup", True, timeout=86400):
        AnalyticsEvent.objects.filter(created_at__lt=timezone.now() - timedelta(days=90)).delete()


@ensure_csrf_cookie
def home(request):
    prune_old_analytics()
    return render(request, "index.html")


@require_GET
def job_list(request):
    jobs = [
        {
            "id": job.pk,
            "title": job.title,
            "department": job.department,
            "salary": job.salary,
            "lpa": job.lpa,
            "experience": job.experience,
            "requirements": [item for item in job.requirements if isinstance(item, str)] if isinstance(job.requirements, list) else [],
            "location": job.location,
            "employment_type": job.employment_type,
            "vibe": job.vibe,
            "sandwich": job.sandwich,
            "damage": job.damage,
            "printer": job.printer,
            "applicants": job.applicants,
        }
        for job in Job.objects.filter(is_active=True)
    ]
    response = JsonResponse({"jobs": jobs})
    response["Cache-Control"] = "no-store"
    return response


@require_GET
def health(request):
    return HttpResponse("ok", content_type="text/plain")


@require_POST
def analytics_event(request):
    if request.content_type != "application/json" or len(request.body) > 1024:
        return JsonResponse({"error": "Invalid event payload."}, status=400)
    try:
        payload = json.loads(request.body)
        if not isinstance(payload, dict):
            raise ValueError("Event must be a JSON object.")
        if set(payload) != {"analytics_enabled", "visitor_id", "event_type", "event_value"}:
            return JsonResponse({"error": "Invalid event payload."}, status=400)
        if payload.get("analytics_enabled") is not True:
            return JsonResponse({"error": "Analytics are disabled."}, status=403)
        visitor_value = payload["visitor_id"]
        if not isinstance(visitor_value, str):
            raise ValueError("Visitor ID must be a string.")
        visitor_id = UUID(visitor_value)
        event_type = payload["event_type"]
        event_value = payload["event_value"]
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid event payload."}, status=400)

    if not isinstance(event_type, str) or not isinstance(event_value, str):
        return JsonResponse({"error": "Invalid event payload."}, status=400)

    allowed_values = {
        "section": {"home", "careers", "salary", "ceo", "benefits"},
        "filter": {
            "salary:high", "salary:low", "location:Remote", "location:Hybrid", "location:On-site",
            "experience:junior", "experience:senior", "vibe:Questionable", "vibe:Immaculate",
            "sandwich:Expert", "sandwich:Beginner", "damage:Severe", "damage:Manageable",
            "printer:Yes", "printer:No",
        },
        "application": {"start", "captcha", "interview", "continue", "offer"},
        "choice": {
            "captcha:1", "captcha:2", "captcha:3", "captcha:4", "captcha:5", "captcha:6",
            "interview:1", "interview:2", "interview:3",
            "qualification:1", "qualification:2", "qualification:3", "qualification:4", "qualification:5", "qualification:6", "qualification:7",
            "reason:1", "reason:2", "reason:3", "reason:4", "reason:5", "reason:6",
            "availability:1", "availability:2", "availability:3", "availability:4", "availability:5",
            "pressure:1", "pressure:2", "pressure:3",
            "chat:salary", "chat:help", "chat:quit",
        },
        "offer": {"accept", "negotiate", "title", "reconsider", "resign", "print", "share"},
    }
    if event_type == "job_view":
        valid = event_value.isdecimal() and len(event_value) <= 12 and Job.objects.filter(pk=int(event_value), is_active=True).exists()
    else:
        valid = event_value in allowed_values.get(event_type, set())
    if not valid:
        return JsonResponse({"error": "Event is not allowed."}, status=400)

    # shortcut: limits are process-local; use a shared cache if the site runs multiple workers.
    address_hash = hashlib.sha256(request.META.get("REMOTE_ADDR", "").encode()).hexdigest()
    for rate_key, limit in ((f"careers-analytics-session:{visitor_id}", 60), (f"careers-analytics-address:{address_hash}", 120)):
        if cache.add(rate_key, 1, timeout=60):
            continue
        try:
            event_count = cache.incr(rate_key)
        except ValueError:
            cache.set(rate_key, 1, timeout=60)
            event_count = 1
        if event_count > limit:
            return HttpResponse(status=429)

    prune_old_analytics()
    AnalyticsEvent.objects.create(visitor_id=visitor_id, event_type=event_type, event_value=event_value)
    return HttpResponse(status=204)


@require_http_methods(["GET", "POST"])
def guestbook_entries(request):
    if request.method == "GET":
        entries = GuestbookEntry.objects.filter(is_visible=True)[:30]
        response = JsonResponse({"entries": [
            {
                "name": entry.author_name,
                "message": entry.message,
                "is_sample": entry.is_sample,
                "created_at": entry.created_at.isoformat(),
            }
            for entry in entries
        ]})
        response["Cache-Control"] = "no-store"
        return response

    if request.content_type != "application/json" or len(request.body) > 1024:
        return JsonResponse({"error": "Use the name and message fields to sign the guestbook."}, status=400)
    try:
        payload = json.loads(request.body)
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({"error": "The guestbook entry could not be read."}, status=400)
    if not isinstance(payload, dict) or set(payload) != {"name", "message"}:
        return JsonResponse({"error": "Provide only a name and message."}, status=400)

    raw_name, message = payload["name"], payload["message"]
    if not isinstance(raw_name, str) or not isinstance(message, str):
        return JsonResponse({"error": "Name and message must be text."}, status=400)
    name = " ".join(raw_name.split())
    message = message.strip()
    if not name or len(name) > 50:
        return JsonResponse({"error": "Enter a name or nickname of 1 to 50 characters."}, status=400)
    if not message or len(message) > 250:
        return JsonResponse({"error": "Enter a message of 1 to 250 characters."}, status=400)

    # Keep only a short-lived hash for throttling; visitor IPs are not stored with entries.
    address_hash = hashlib.sha256(request.META.get("REMOTE_ADDR", "").encode()).hexdigest()
    rate_key = f"careers-guestbook-address:{address_hash}"
    if not cache.add(rate_key, 1, timeout=60):
        try:
            post_count = cache.incr(rate_key)
        except ValueError:
            cache.set(rate_key, 1, timeout=60)
            post_count = 1
        if post_count > 20:
            return JsonResponse({"error": "Please wait a minute before signing again."}, status=429)

    entry = GuestbookEntry.objects.create(author_name=name, message=message)
    return JsonResponse({
        "entry": {
            "name": entry.author_name,
            "message": entry.message,
            "is_sample": entry.is_sample,
            "created_at": entry.created_at.isoformat(),
        }
    }, status=201)
