from django.urls import path, include
from .views import PromptToModel, DocumentAddView, DocumentDeleteView, DocumentUpdateView, QueryAwnserListView
    
urlpatterns = [
    path('prompt/', PromptToModel.as_view(), name='prompt'),
    
    path('documents/add/', DocumentAddView.as_view(), name='add_dooc'),
    path('documents/delete/<str:title>/', DocumentDeleteView.as_view(), name='delete_dooc'),
    path('documents/update/', DocumentUpdateView.as_view(), name='update_dooc'),
    
    path('querylist/', QueryAwnserListView.as_view(), name='query_list'),
]