from django.contrib import admin

from .models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "department", "salary", "location", "is_active", "sort_order", "updated_at")
    list_filter = ("is_active", "department", "location", "vibe", "damage")
    search_fields = ("title", "department", "salary")
    list_editable = ("is_active", "sort_order")
    ordering = ("sort_order", "id")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("The position", {"fields": ("title", "department", "is_active", "sort_order")} ),
        ("Details", {"fields": ("salary", "lpa", "experience", "requirements", "location", "employment_type")} ),
        ("Corporate compatibility", {"fields": ("vibe", "sandwich", "damage", "printer", "applicants")} ),
        ("History", {"fields": ("created_at", "updated_at")} ),
    )


admin.site.site_header = "Udai Batta and Ayush Sharma co.ltd · Careers"
admin.site.site_title = "Careers Admin"
admin.site.index_title = "Manage the fictional job listings"
