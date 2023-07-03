from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"doctors", views.DoctorViewSet, basename="doctors")
router.register(r"patients", views.PatientViewSet, basename="patients")
router.register(r"sessions", views.SessionViewSet, basename="sessions")
router.register(r"assignments", views.AssignmentViewSet, basename="assignments")
router.register(r"advices", views.AdviceViewSet, basename="advices")
router.register(r"invites", views.InviteViewSet, basename="invites")

# print(router.get_urls())
urlpatterns = [
    path("login", views.LoginUser.as_view(), name="login-user"),
    path("signup", views.RegisterUser.as_view(), name="register-user"),
    path("", include(router.urls)),
]
