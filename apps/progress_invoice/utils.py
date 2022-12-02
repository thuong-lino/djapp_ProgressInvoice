from .models import ProgressInvoice, ProgessInvoiceAllocation
from .cch import get_project_items, get_unapplied_process_invoices


def compare_progress_invoice(cch_invoice: dict,  *args, **kwargs):
    cch_invoice_ident = cch_invoice.get('invoice_ident', None)
    client_ident = cch_invoice.get('client_ident', 'NULL')
    cch_open_amount = cch_invoice['unappliedprog_amt']

    _ref, created = ProgressInvoice.objects.get_or_create(
        invoice_ident=cch_invoice_ident, defaults=cch_invoice)
    new_allocs = get_project_items(client_ident)
    new_allocs += [{
        'project_ident': None,
        'project_name': 'Unassigned',
    }]
    if created:
        [ProgessInvoiceAllocation.objects.create(
            progress_invoice=_ref, **item) for item in new_allocs]
        _ref.auto_allocated()
    else:
        _ref.is_deactive = False
        if _ref.unappliedprog_amt != cch_open_amount:
            _ref.on_change_open_amount(cch_open_amount)


def refresh_all():
    unapplied_invoice = get_unapplied_process_invoices()

    existing_idents = list(item['invoice_ident'] for item in unapplied_invoice)
    for invoice in unapplied_invoice:
        compare_progress_invoice(invoice)
    disappeareds = ProgressInvoice.objects.exclude(
        invoice_ident__in=existing_idents)
    for invoice in disappeareds:
        invoice.is_deactive = True
        invoice.save()
