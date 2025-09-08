from django.urls import path
from .views_transportation import transportation_page

urlpatterns = [
    path('transportation/', transportation_page, name='transportation'),
]
