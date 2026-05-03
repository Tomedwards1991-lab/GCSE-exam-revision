from django.contrib import admin

from .models import (
    GuideArticle,
    AttemptFeedbackPoint,
    Paper,
    PracticeAttempt,
    Question,
    SpecificationUnit,
    TeacherStudentAssignment,
    Topic,
    UserProfile,
    WalkthroughStep,
)


class WalkthroughStepInline(admin.TabularInline):
    model = WalkthroughStep
    extra = 1
    fields = ["order", "title_en", "body_en", "write_this_en", "source_hint_en", "mark_focus_en"]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "role", "created_at"]
    list_filter = ["role"]
    search_fields = ["user__username", "user__first_name", "user__last_name", "user__email"]


@admin.register(TeacherStudentAssignment)
class TeacherStudentAssignmentAdmin(admin.ModelAdmin):
    list_display = ["teacher", "student", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["teacher__username", "student__username", "student__first_name", "student__last_name"]


@admin.register(SpecificationUnit)
class SpecificationUnitAdmin(admin.ModelAdmin):
    list_display = ["code", "title_en", "is_active"]
    search_fields = ["code", "title_en", "title_cy"]


@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
    list_display = ["series", "code", "unit", "exam_board"]
    list_filter = ["unit", "exam_board", "series"]
    search_fields = ["series", "code", "title"]


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ["name_en", "unit", "slug"]
    prepopulated_fields = {"slug": ("name_en",)}
    list_filter = ["unit"]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["reference", "unit", "paper", "source", "marks", "difficulty", "is_published"]
    list_filter = ["unit", "source", "difficulty", "is_published", "topics"]
    search_fields = ["reference", "prompt_en", "prompt_cy", "expected_answer_en"]
    filter_horizontal = ["topics"]
    inlines = [WalkthroughStepInline]


@admin.register(PracticeAttempt)
class PracticeAttemptAdmin(admin.ModelAdmin):
    list_display = ["question", "user", "auto_awarded_marks", "self_assessed_marks", "language_code", "created_at"]
    list_filter = ["language_code", "created_at"]
    search_fields = ["answer_text", "question__prompt_en"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(AttemptFeedbackPoint)
class AttemptFeedbackPointAdmin(admin.ModelAdmin):
    list_display = ["attempt", "order", "label", "awarded", "marks"]
    list_filter = ["awarded"]
    search_fields = ["label", "evidence", "improvement"]


@admin.register(GuideArticle)
class GuideArticleAdmin(admin.ModelAdmin):
    list_display = ["title_en", "unit", "order", "is_published"]
    list_filter = ["unit", "is_published"]
    prepopulated_fields = {"slug": ("title_en",)}
    search_fields = ["title_en", "title_cy", "body_en"]
