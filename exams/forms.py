from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import TeacherStudentAssignment, UserProfile


class PracticeAnswerForm(forms.Form):
    answer_text = forms.CharField(
        label=_("Your answer"),
        widget=forms.Textarea(
            attrs={
                "class": "form-control answer-box",
                "rows": 8,
                "placeholder": _("Write your answer as you would in the exam..."),
            }
        ),
    )


class GenerateQuestionForm(forms.Form):
    pattern = forms.ChoiceField(
        label=_("Question pattern"),
        choices=[
            ("html_tags", _("HTML tags and structure")),
            ("html_draft", _("HTML draft web page")),
            ("greenfoot_create", _("Greenfoot create a scenario")),
            ("greenfoot_complete", _("Greenfoot complete a world")),
            ("greenfoot_identify", _("Greenfoot identify code elements")),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    topic = forms.CharField(
        label=_("Topic"),
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": _("e.g. pets, cars, advert, aquarium")}),
    )
    marks = forms.IntegerField(
        label=_("Marks"),
        min_value=1,
        max_value=13,
        initial=4,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 13}),
    )
    difficulty = forms.ChoiceField(
        label=_("Difficulty"),
        choices=[("foundation", _("Foundation")), ("standard", _("Standard")), ("stretch", _("Stretch"))],
        initial="standard",
        widget=forms.Select(attrs={"class": "form-select"}),
    )


class RoleUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(
        label=_("Role"),
        choices=UserProfile.ROLE_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    email = forms.EmailField(
        label=_("Email"),
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    first_name = forms.CharField(
        label=_("First name"),
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    last_name = forms.CharField(
        label=_("Last name"),
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "first_name", "last_name", "email", "role")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if self.cleaned_data["role"] == UserProfile.ROLE_ADMIN:
            user.is_staff = True
        if commit:
            user.save()
            user.profile.role = self.cleaned_data["role"]
            user.profile.save(update_fields=["role", "updated_at"])
        return user


class UserRoleForm(forms.Form):
    role = forms.ChoiceField(
        label=_("Role"),
        choices=UserProfile.ROLE_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    is_active = forms.BooleanField(
        label=_("Active"),
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = TeacherStudentAssignment
        fields = ["teacher", "student", "is_active"]
        widgets = {
            "teacher": forms.Select(attrs={"class": "form-select"}),
            "student": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        User = get_user_model()
        self.fields["teacher"].queryset = User.objects.filter(profile__role__in=[UserProfile.ROLE_TEACHER, UserProfile.ROLE_ADMIN]).order_by("username")
        self.fields["student"].queryset = User.objects.filter(profile__role=UserProfile.ROLE_STUDENT).order_by("username")


class PasswordResetByAdminForm(forms.Form):
    new_password = forms.CharField(
        label=_("New password"),
        min_length=8,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
