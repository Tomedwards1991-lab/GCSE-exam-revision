from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Avg, Count, F, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DetailView, FormView, ListView, TemplateView

from .forms import AssignmentForm, GenerateQuestionForm, PasswordResetByAdminForm, PracticeAnswerForm, RoleUserCreationForm, UserRoleForm
from .models import GuideArticle, Paper, PracticeAttempt, Question, SpecificationUnit, TeacherStudentAssignment, Topic, UserProfile, WalkthroughStep
from .services import auto_mark_attempt, generate_student_feedback, get_question_generator


def active_language():
    return "en"


def user_role(user):
    if not user.is_authenticated:
        return None
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile.role


class TeacherRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        return user_role(self.request.user) in {UserProfile.ROLE_TEACHER, UserProfile.ROLE_ADMIN}


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        return user_role(self.request.user) == UserProfile.ROLE_ADMIN


class HomeView(TemplateView):
    template_name = "exams/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["unit"] = SpecificationUnit.objects.filter(code="3500U20-1").first()
        context["question_count"] = Question.objects.filter(is_published=True).count()
        context["guide_count"] = GuideArticle.objects.filter(is_published=True).count()
        return context


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "exams/dashboard.html"

    def get_template_names(self):
        role = user_role(self.request.user)
        if role == UserProfile.ROLE_ADMIN:
            return ["exams/admin_dashboard.html"]
        if role == UserProfile.ROLE_TEACHER:
            return ["exams/teacher_dashboard.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        role = user_role(self.request.user)
        context["role"] = role or "guest"
        if role == UserProfile.ROLE_TEACHER:
            return self.get_teacher_context(context)
        if role == UserProfile.ROLE_ADMIN:
            context = self.get_teacher_context(context, include_all=True)
            context["user_count"] = get_user_model().objects.count()
            context["assignment_count"] = TeacherStudentAssignment.objects.filter(is_active=True).count()
            return context
        attempts = PracticeAttempt.objects.all()
        if self.request.user.is_authenticated:
            attempts = attempts.filter(user=self.request.user)
        else:
            attempts = attempts.filter(session_key=self.request.session.session_key or "")
        context["attempts"] = attempts[:6]
        context["papers"] = Paper.objects.annotate(question_total=Count("questions"))
        context["topics"] = Topic.objects.annotate(question_total=Count("questions"))
        return context

    def get_teacher_context(self, context, include_all=False):
        User = get_user_model()
        students = User.objects.filter(profile__role=UserProfile.ROLE_STUDENT)
        if not include_all:
            students = students.filter(assigned_teachers__teacher=self.request.user, assigned_teachers__is_active=True)
        students = students.annotate(
            attempt_total=Count("practiceattempt", distinct=True),
            marks_awarded=Sum("practiceattempt__auto_awarded_marks"),
            marks_available=Sum("practiceattempt__question__marks"),
        ).order_by("last_name", "first_name", "username")
        attempts = PracticeAttempt.objects.filter(user__in=students).select_related("user", "question")[:10]
        context["students"] = students
        context["recent_attempts"] = attempts
        context["average_self_score"] = PracticeAttempt.objects.filter(user__in=students).aggregate(
            average=Avg(100.0 * F("auto_awarded_marks") / F("question__marks"))
        )["average"]
        return context


class QuestionListView(LoginRequiredMixin, ListView):
    model = Question
    template_name = "exams/question_list.html"
    context_object_name = "questions"
    paginate_by = 20

    def get_queryset(self):
        queryset = Question.objects.filter(is_published=True).select_related("unit", "paper").prefetch_related("topics")
        topic = self.request.GET.get("topic")
        source = self.request.GET.get("source")
        if topic:
            queryset = queryset.filter(topics__slug=topic)
        if source:
            queryset = queryset.filter(source=source)
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["topics"] = Topic.objects.all()
        context["selected_topic"] = self.request.GET.get("topic", "")
        context["selected_source"] = self.request.GET.get("source", "")
        context["language_code"] = active_language()
        return context


class QuestionDetailView(LoginRequiredMixin, DetailView):
    model = Question
    template_name = "exams/question_detail.html"
    context_object_name = "question"
    queryset = Question.objects.filter(is_published=True).select_related("unit", "paper").prefetch_related("topics", "walkthrough_steps")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["language_code"] = active_language()
        return context


class AttemptQuestionView(LoginRequiredMixin, FormView):
    template_name = "exams/attempt_question.html"
    form_class = PracticeAnswerForm

    def dispatch(self, request, *args, **kwargs):
        self.question = get_object_or_404(
            Question.objects.filter(is_published=True).prefetch_related("walkthrough_steps"),
            pk=kwargs["pk"],
        )
        if not request.session.session_key:
            request.session.create()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        attempt = PracticeAttempt.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            question=self.question,
            answer_text=form.cleaned_data["answer_text"],
            language_code=active_language(),
            session_key=self.request.session.session_key,
        )
        auto_mark_attempt(attempt)
        messages.success(self.request, "Answer marked. Work through the feedback and model-answer builder below.")
        return redirect(f"{reverse('attempt_question', kwargs={'pk': self.question.pk})}?attempt={attempt.pk}")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempt_id = self.request.GET.get("attempt")
        attempt = None
        if attempt_id:
            attempt = get_object_or_404(
                PracticeAttempt.objects.prefetch_related("feedback_points"),
                pk=attempt_id,
                question=self.question,
            )
        context["question"] = self.question
        context["attempt"] = attempt
        context["language_code"] = active_language()
        return context


class StudentDetailView(TeacherRequiredMixin, DetailView):
    model = get_user_model()
    template_name = "exams/student_detail.html"
    context_object_name = "student"

    def get_queryset(self):
        queryset = get_user_model().objects.filter(profile__role=UserProfile.ROLE_STUDENT)
        if user_role(self.request.user) == UserProfile.ROLE_ADMIN:
            return queryset
        return queryset.filter(assigned_teachers__teacher=self.request.user, assigned_teachers__is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempts = PracticeAttempt.objects.filter(user=self.object).select_related("question", "question__paper").prefetch_related("question__topics")
        context["attempts"] = attempts
        context["attempt_total"] = attempts.count()
        context["marks_awarded"] = attempts.aggregate(total=Sum("auto_awarded_marks"))["total"] or 0
        context["marks_available"] = attempts.aggregate(total=Sum("question__marks"))["total"] or 0
        context["feedback"] = generate_student_feedback(self.object, attempts)
        context["topic_metrics"] = Topic.objects.filter(questions__attempts__user=self.object).annotate(
            attempt_total=Count("questions__attempts", distinct=True),
            marks_awarded=Sum("questions__attempts__auto_awarded_marks"),
            marks_available=Sum("questions__attempts__question__marks"),
        ).distinct()
        return context


class GenerateQuestionView(LoginRequiredMixin, FormView):
    template_name = "exams/generate_question.html"
    form_class = GenerateQuestionForm

    def form_valid(self, form):
        unit = get_object_or_404(SpecificationUnit, code="3500U20-1")
        draft = get_question_generator().generate(**form.cleaned_data)
        topic, _ = Topic.objects.get_or_create(
            unit=unit,
            slug=draft.topic_name.lower().replace(" ", "-"),
            defaults={"name_en": draft.topic_name.title()},
        )
        question = Question.objects.create(
            unit=unit,
            source="generated",
            prompt_en=draft.prompt_en,
            expected_answer_en=draft.expected_answer_en,
            marks=draft.marks,
            difficulty=draft.difficulty,
            reference="Generated practice",
        )
        question.topics.add(topic)
        for index, step in enumerate(draft.walkthrough_steps, start=1):
            WalkthroughStep.objects.create(
                question=question,
                order=index,
                title_en=step["title"],
                body_en=step["body"],
                mark_focus_en=step["mark_focus"],
                write_this_en=step.get("write_this", ""),
                source_hint_en=step.get("source_hint", ""),
            )
        messages.success(self.request, "Generated a new practice question.")
        return redirect(question.get_absolute_url())


class UserManagementView(AdminRequiredMixin, TemplateView):
    template_name = "exams/user_management.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        User = get_user_model()
        context["users"] = User.objects.select_related("profile").order_by("profile__role", "username")
        context["assignments"] = TeacherStudentAssignment.objects.select_related("teacher", "student").order_by("teacher__username", "student__username")
        context["create_form"] = RoleUserCreationForm()
        context["assignment_form"] = AssignmentForm()
        return context


class CreateUserView(AdminRequiredMixin, FormView):
    template_name = "exams/user_form.html"
    form_class = RoleUserCreationForm

    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, f"Created {user.username}.")
        return redirect("user_management")


class UpdateUserRoleView(AdminRequiredMixin, FormView):
    template_name = "exams/user_role_form.html"
    form_class = UserRoleForm

    def dispatch(self, request, *args, **kwargs):
        self.user_object = get_object_or_404(get_user_model().objects.select_related("profile"), pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        return {"role": self.user_object.profile.role, "is_active": self.user_object.is_active}

    def form_valid(self, form):
        self.user_object.profile.role = form.cleaned_data["role"]
        self.user_object.profile.save(update_fields=["role", "updated_at"])
        self.user_object.is_active = form.cleaned_data["is_active"]
        self.user_object.is_staff = form.cleaned_data["role"] == UserProfile.ROLE_ADMIN
        self.user_object.save(update_fields=["is_active", "is_staff"])
        messages.success(self.request, f"Updated {self.user_object.username}.")
        return redirect("user_management")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["managed_user"] = self.user_object
        return context


class AdminPasswordResetView(AdminRequiredMixin, FormView):
    template_name = "exams/password_reset_form.html"
    form_class = PasswordResetByAdminForm

    def dispatch(self, request, *args, **kwargs):
        self.user_object = get_object_or_404(get_user_model(), pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.user_object.set_password(form.cleaned_data["new_password"])
        self.user_object.save(update_fields=["password"])
        messages.success(self.request, f"Password reset for {self.user_object.username}.")
        return redirect("user_management")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["managed_user"] = self.user_object
        return context


class CreateAssignmentView(AdminRequiredMixin, FormView):
    template_name = "exams/assignment_form.html"
    form_class = AssignmentForm

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Assignment saved.")
        return redirect("user_management")


class GuideListView(ListView):
    model = GuideArticle
    template_name = "exams/guide_list.html"
    context_object_name = "articles"
    queryset = GuideArticle.objects.filter(is_published=True).select_related("unit")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["language_code"] = active_language()
        return context


class GuideDetailView(DetailView):
    model = GuideArticle
    template_name = "exams/guide_detail.html"
    context_object_name = "article"
    queryset = GuideArticle.objects.filter(is_published=True).select_related("unit")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["language_code"] = active_language()
        return context
