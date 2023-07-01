from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"doctors", views.DoctorViewSet, basename="doctors")
router.register(r"patients", views.PatientViewSet, basename="patients")

urlpatterns = [
    path("login", views.LoginUser.as_view),
    path("signup", views.RegisterUser.as_view),
    path("", include(router.urls)),
]
