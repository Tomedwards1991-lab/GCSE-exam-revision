from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import PracticeAttempt, Question, SpecificationUnit, TeacherStudentAssignment, UserProfile


class PracticeFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("learner", password="pass12345")
        unit = SpecificationUnit.objects.create(code="3500U20-1", title_en="Unit 2")
        self.question = Question.objects.create(
            unit=unit,
            prompt_en="State one purpose of validation.",
            marks=1,
            expected_answer_en="Validation checks that input is sensible or allowed.",
        )

    def test_question_list_loads(self):
        self.client.login(username="learner", password="pass12345")
        response = self.client.get(reverse("question_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "State one purpose")

    def test_attempt_creates_record(self):
        self.client.login(username="learner", password="pass12345")
        response = self.client.post(
            reverse("attempt_question", kwargs={"pk": self.question.pk}),
            {"answer_text": "It checks input is sensible."},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.question.attempts.count(), 1)
        attempt = self.question.attempts.first()
        self.assertGreaterEqual(attempt.auto_awarded_marks, 0)
        self.assertGreater(attempt.feedback_points.count(), 0)

    def test_practice_requires_login(self):
        response = self.client.get(reverse("question_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_generate_prefills_from_get(self):
        self.client.login(username="learner", password="pass12345")
        url = reverse("generate_question") + "?pattern=html_tags&topic=pets&marks=6&difficulty=stretch"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Check if form initial values are set correctly
        form = response.context["form"]
        self.assertEqual(form.initial["pattern"], "html_tags")
        self.assertEqual(form.initial["topic"], "pets")
        self.assertEqual(form.initial["marks"], "6")
        self.assertEqual(form.initial["difficulty"], "stretch")

    def test_question_detail_has_generate_similar_link(self):
        self.client.login(username="learner", password="pass12345")
        from .models import Topic
        topic = Topic.objects.create(unit=self.question.unit, name_en="Validation")
        self.question.topics.add(topic)
        self.question.pattern = "html_tags"
        self.question.marks = 5
        self.question.difficulty = "standard"
        self.question.save()

        response = self.client.get(reverse("question_detail", kwargs={"pk": self.question.pk}))
        self.assertEqual(response.status_code, 200)
        expected_url = f"{reverse('generate_question')}?pattern=html_tags&topic=Validation&marks=5&difficulty=standard"
        self.assertContains(response, expected_url)


class RoleDashboardTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.student = User.objects.create_user("student", password="pass12345")
        self.teacher = User.objects.create_user("teacher", password="pass12345")
        self.admin = User.objects.create_user("admin", password="pass12345", is_staff=True)
        self.student.profile.role = UserProfile.ROLE_STUDENT
        self.student.profile.save()
        self.teacher.profile.role = UserProfile.ROLE_TEACHER
        self.teacher.profile.save()
        self.admin.profile.role = UserProfile.ROLE_ADMIN
        self.admin.profile.save()
        TeacherStudentAssignment.objects.create(teacher=self.teacher, student=self.student)
        unit = SpecificationUnit.objects.create(code="3500U20-1", title_en="Unit 2")
        self.question = Question.objects.create(
            unit=unit,
            prompt_en="Explain one use of selection.",
            marks=2,
            expected_answer_en="Selection runs code when a condition is met.",
        )
        PracticeAttempt.objects.create(user=self.student, question=self.question, answer_text="IF score < 40", auto_awarded_marks=1)

    def test_teacher_sees_assigned_student(self):
        self.client.login(username="teacher", password="pass12345")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "exams/teacher_dashboard.html")
        self.assertContains(response, "student")

    def test_admin_can_open_user_management(self):
        self.client.login(username="admin", password="pass12345")
        response = self.client.get(reverse("user_management"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "User management")

    def test_student_cannot_open_user_management(self):
        self.client.login(username="student", password="pass12345")
        response = self.client.get(reverse("user_management"))
        self.assertEqual(response.status_code, 403)
