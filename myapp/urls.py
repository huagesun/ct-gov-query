from django.urls import path
from .views import my_view
from .views import outcome_structured

urlpatterns = [
    path('', my_view, name='my-view'),
    path('export', outcome_structured, name='export_xml_csv')
]
