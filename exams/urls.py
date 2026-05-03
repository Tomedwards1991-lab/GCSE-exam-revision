from django.urls import path

from . import views


urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("questions/", views.QuestionListView.as_view(), name="question_list"),
    path("questions/<int:pk>/", views.QuestionDetailView.as_view(), name="question_detail"),
    path("questions/<int:pk>/attempt/", views.AttemptQuestionView.as_view(), name="attempt_question"),
    path("students/<int:pk>/", views.StudentDetailView.as_view(), name="student_detail"),
    path("generate/", views.GenerateQuestionView.as_view(), name="generate_question"),
    path("guides/", views.GuideListView.as_view(), name="guide_list"),
    path("guides/<slug:slug>/", views.GuideDetailView.as_view(), name="guide_detail"),
    path("manage/users/", views.UserManagementView.as_view(), name="user_management"),
    path("manage/users/create/", views.CreateUserView.as_view(), name="create_user"),
    path("manage/users/<int:pk>/role/", views.UpdateUserRoleView.as_view(), name="update_user_role"),
    path("manage/users/<int:pk>/password/", views.AdminPasswordResetView.as_view(), name="admin_password_reset"),
    path("manage/assignments/create/", views.CreateAssignmentView.as_view(), name="create_assignment"),
]
