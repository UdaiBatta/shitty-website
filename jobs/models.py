from django.db import models
from django.core.exceptions import ValidationError


class Job(models.Model):
    title = models.CharField(max_length=160)
    department = models.CharField(max_length=120)
    salary = models.CharField(max_length=160)
    lpa = models.PositiveIntegerField(help_text="Annual salary in lakhs; used by the salary filter.")
    experience = models.PositiveIntegerField(help_text="Minimum years of experience.")
    requirements = models.JSONField(default=list, blank=True)
    location = models.CharField(max_length=30, choices=[("Remote", "Remote"), ("Hybrid", "Hybrid"), ("On-site", "On-site")])
    employment_type = models.CharField(max_length=80, default="Full-time")
    vibe = models.CharField(max_length=40, choices=[("Questionable", "Questionable"), ("Immaculate", "Immaculate")])
    sandwich = models.CharField(max_length=30, choices=[("Expert", "Expert"), ("Beginner", "Beginner")])
    damage = models.CharField(max_length=30, choices=[("Severe", "Severe"), ("Manageable", "Manageable")])
    printer = models.CharField(max_length=3, choices=[("Yes", "Yes"), ("No", "No")])
    applicants = models.CharField(max_length=30, default="0", help_text="Fictional competitor count shown on the joke site.")
    sort_order = models.PositiveIntegerField(default=1000)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "job listing"
        verbose_name_plural = "job listings"

    def clean(self):
        super().clean()
        if not isinstance(self.requirements, list) or not all(isinstance(item, str) for item in self.requirements):
            raise ValidationError({"requirements": "Enter a JSON array of requirement strings."})

    def __str__(self):
        return self.title
