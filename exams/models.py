from django.conf import settings
from django.db.models.signals import post_save
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.dispatch import receiver


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserProfile(TimestampedModel):
    ROLE_STUDENT = "student"
    ROLE_TEACHER = "teacher"
    ROLE_ADMIN = "admin"
    ROLE_CHOICES = [
        (ROLE_STUDENT, "Student"),
        (ROLE_TEACHER, "Teacher"),
        (ROLE_ADMIN, "Admin"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default=ROLE_STUDENT)

    class Meta:
        ordering = ["user__last_name", "user__first_name", "user__username"]

    def __str__(self):
        return f"{self.user.get_username()} ({self.get_role_display()})"

    @property
    def can_teach(self):
        return self.role in {self.ROLE_TEACHER, self.ROLE_ADMIN}

    @property
    def can_manage_users(self):
        return self.role == self.ROLE_ADMIN


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


class TeacherStudentAssignment(TimestampedModel):
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assigned_students")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assigned_teachers")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["teacher__username", "student__username"]
        unique_together = [("teacher", "student")]

    def __str__(self):
        return f"{self.teacher.get_username()} -> {self.student.get_username()}"


class SpecificationUnit(TimestampedModel):
    code = models.CharField(max_length=24, unique=True)
    title_en = models.CharField(max_length=160)
    title_cy = models.CharField(max_length=160, blank=True)
    description_en = models.TextField(blank=True)
    description_cy = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.title_en}"

    def title(self, language_code=None):
        return self.title_en


class Paper(TimestampedModel):
    EXAM_BOARD_CHOICES = [("wjec", "WJEC")]

    unit = models.ForeignKey(SpecificationUnit, on_delete=models.PROTECT, related_name="papers")
    exam_board = models.CharField(max_length=24, choices=EXAM_BOARD_CHOICES, default="wjec")
    series = models.CharField(max_length=24)
    code = models.CharField(max_length=40)
    title = models.CharField(max_length=180)
    source_pdf_path = models.CharField(max_length=500, blank=True)
    mark_scheme_pdf_path = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["-series", "code"]
        unique_together = [("series", "code")]

    def __str__(self):
        return f"{self.series} {self.code}"


class Topic(TimestampedModel):
    unit = models.ForeignKey(SpecificationUnit, on_delete=models.CASCADE, related_name="topics")
    name_en = models.CharField(max_length=120)
    name_cy = models.CharField(max_length=120, blank=True)
    slug = models.SlugField(max_length=140)

    class Meta:
        ordering = ["unit__code", "name_en"]
        unique_together = [("unit", "slug")]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name_en)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name_en

    def name(self, language_code=None):
        return self.name_en


class Question(TimestampedModel):
    SOURCE_CHOICES = [
        ("past_paper", "Past paper"),
        ("generated", "Generated"),
    ]
    DIFFICULTY_CHOICES = [
        ("foundation", "Foundation"),
        ("standard", "Standard"),
        ("stretch", "Stretch"),
    ]

    unit = models.ForeignKey(SpecificationUnit, on_delete=models.PROTECT, related_name="questions")
    paper = models.ForeignKey(Paper, on_delete=models.SET_NULL, null=True, blank=True, related_name="questions")
    topics = models.ManyToManyField(Topic, blank=True, related_name="questions")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="past_paper")
    reference = models.CharField(max_length=80, blank=True)
    prompt_en = models.TextField()
    prompt_cy = models.TextField(blank=True)
    marks = models.PositiveSmallIntegerField(default=1)
    expected_answer_en = models.TextField()
    expected_answer_cy = models.TextField(blank=True)
    examiner_note_en = models.TextField(blank=True)
    examiner_note_cy = models.TextField(blank=True)
    difficulty = models.CharField(max_length=24, choices=DIFFICULTY_CHOICES, default="standard")
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["unit__code", "paper__series", "reference", "id"]

    def __str__(self):
        ref = self.reference or f"Question {self.pk}"
        return f"{self.unit.code} {ref}"

    def get_absolute_url(self):
        return reverse("question_detail", kwargs={"pk": self.pk})

    def prompt(self, language_code=None):
        return self.prompt_en

    def expected_answer(self, language_code=None):
        return self.expected_answer_en

    def examiner_note(self, language_code=None):
        return self.examiner_note_en


class WalkthroughStep(TimestampedModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="walkthrough_steps")
    order = models.PositiveSmallIntegerField()
    title_en = models.CharField(max_length=160)
    title_cy = models.CharField(max_length=160, blank=True)
    body_en = models.TextField()
    body_cy = models.TextField(blank=True)
    mark_focus_en = models.CharField(max_length=220, blank=True)
    mark_focus_cy = models.CharField(max_length=220, blank=True)
    write_this_en = models.TextField(blank=True)
    write_this_cy = models.TextField(blank=True)
    source_hint_en = models.TextField(blank=True)
    source_hint_cy = models.TextField(blank=True)

    class Meta:
        ordering = ["question", "order"]
        unique_together = [("question", "order")]

    def __str__(self):
        return f"{self.question} step {self.order}"

    def title(self, language_code=None):
        return self.title_en

    def body(self, language_code=None):
        return self.body_en

    def mark_focus(self, language_code=None):
        return self.mark_focus_en

    def write_this(self, language_code=None):
        return self.write_this_en

    def source_hint(self, language_code=None):
        return self.source_hint_en


class PracticeAttempt(TimestampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="attempts")
    answer_text = models.TextField()
    self_assessed_marks = models.PositiveSmallIntegerField(default=0)
    auto_awarded_marks = models.PositiveSmallIntegerField(default=0)
    auto_feedback_summary = models.TextField(blank=True)
    language_code = models.CharField(max_length=8, default="en")
    session_key = models.CharField(max_length=80, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Attempt {self.pk} on {self.question}"


class AttemptFeedbackPoint(TimestampedModel):
    attempt = models.ForeignKey(PracticeAttempt, on_delete=models.CASCADE, related_name="feedback_points")
    order = models.PositiveSmallIntegerField()
    label = models.CharField(max_length=180)
    awarded = models.BooleanField(default=False)
    marks = models.PositiveSmallIntegerField(default=1)
    evidence = models.TextField(blank=True)
    improvement = models.TextField(blank=True)
    source_hint = models.TextField(blank=True)

    class Meta:
        ordering = ["attempt", "order"]
        unique_together = [("attempt", "order")]

    def __str__(self):
        state = "awarded" if self.awarded else "missed"
        return f"{self.attempt_id} {self.order} {state}"


class GuideArticle(TimestampedModel):
    unit = models.ForeignKey(SpecificationUnit, on_delete=models.PROTECT, related_name="guide_articles")
    title_en = models.CharField(max_length=180)
    title_cy = models.CharField(max_length=180, blank=True)
    slug = models.SlugField(max_length=180)
    summary_en = models.TextField(blank=True)
    summary_cy = models.TextField(blank=True)
    body_en = models.TextField()
    body_cy = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "title_en"]
        unique_together = [("unit", "slug")]

    def __str__(self):
        return self.title_en

    def get_absolute_url(self):
        return reverse("guide_detail", kwargs={"slug": self.slug})

    def title(self, language_code=None):
        return self.title_en

    def summary(self, language_code=None):
        return self.summary_en

    def body(self, language_code=None):
        return self.body_en
