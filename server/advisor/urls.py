from django.urls import path

from .views import CardAdviceView

urlpatterns = [
    path("suggest/", CardAdviceView.as_view(), name="advisor-suggest"),
]
