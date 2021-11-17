from django.urls import path
from ..v1 import api as core_api


urlpatterns = [
    path('get_questions/', core_api.QuestionsListView.as_view()),
    path('legal_docs/', core_api.legal_docs),
    path('advices/', core_api.AdvicesListView.as_view()),
    path('benefits/', core_api.BenefitListView.as_view()),
    path('tariffs/', core_api.TariffsListView.as_view()),
]
