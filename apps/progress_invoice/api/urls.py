from django.urls import path
from .views import get_allocations, put_allocation, refresh_db_view

urlpatterns = [
    path('data/', get_allocations),
    path('data/<int:alloc_id>/', put_allocation, name='put_allocation'),
    path('refresh_db/', refresh_db_view, name='refresh_all'),
]
