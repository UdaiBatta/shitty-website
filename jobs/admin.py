from django.contrib import admin

from .models import AnalyticsEvent, GuestbookEntry, Job


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


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "visitor_id", "event_type", "event_value")
    list_filter = ("event_type", "created_at")
    search_fields = ("visitor_id", "event_value")
    date_hierarchy = "created_at"
    readonly_fields = ("visitor_id", "event_type", "event_value", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.site_header = "Udai Batta and Ayush Sharma co.ltd · Careers"
admin.site.site_title = "Careers Admin"
admin.site.index_title = "Manage the fictional job listings"


@admin.register(GuestbookEntry)
class GuestbookEntryAdmin(admin.ModelAdmin):
    list_display = ("author_name", "message_preview", "is_sample", "is_visible", "created_at")
    list_filter = ("is_sample", "is_visible", "created_at")
    search_fields = ("author_name", "message")
    list_editable = ("is_visible",)
    readonly_fields = ("created_at",)
    ordering = ("-created_at", "-id")

    @admin.display(description="Message")
    def message_preview(self, obj):
        return obj.message[:80]
