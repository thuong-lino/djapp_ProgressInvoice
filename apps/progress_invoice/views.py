from django.shortcuts import render


def index(request):
    # unapplied_invoice = get_unapplied_process_invoices()

    # existing_idents = list(item['invoice_ident'] for item in unapplied_invoice)
    # for invoice in unapplied_invoice:
    #     compare_progress_invoice(invoice)
    # disappeareds = ProgressInvoice.objects.exclude(
    #     invoice_ident__in=existing_idents)
    # for invoice in disappeareds:
    #     invoice.is_deactive = True
    #     invoice.save()
    return render(request, 'apps/index.html')
