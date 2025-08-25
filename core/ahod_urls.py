from django.urls import path
from .views import *

urlpatterns = [
    path("dash/", ahod_dash, name="ahod_dash"),
]
