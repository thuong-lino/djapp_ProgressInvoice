from django.contrib import admin
from django.urls import path, include
from apps.progress_invoice.views import index

urlpatterns = [
    path('admin/', admin.site.urls, name='admin_view'),
    path('api/', include('apps.progress_invoice.api.urls')),
    path('', index, name='index'),
]
