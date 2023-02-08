from django.contrib import admin
from .models import Client, ProgessInvoiceAllocation, ProgressInvoice
# Register your models here.
admin.site.register(Client)
admin.site.register(ProgessInvoiceAllocation)
admin.site.register(ProgressInvoice)
