from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from .models import Job


def home(request):
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
