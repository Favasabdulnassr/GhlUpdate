from django.urls import path
from .views import update_contacts

urlpatterns = [
    path('update-contacts/', update_contacts, name='update_contacts'),
]
