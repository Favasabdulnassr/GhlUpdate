from django.urls import path
from .views import get_match_opportunities

urlpatterns = [

    path('get-match-oppurtunities/',get_match_opportunities,name='match-opportunities')


    # path('update-contacts/', update_contacts, name='update_contacts'),
]
