from .models import ProgressInvoice, ProgessInvoiceAllocation, Client
from .cch import get_project_items, get_unapplied_process_invoices


def compare_progress_invoice(cch_invoice: dict,  *args, **kwargs):
    cch_invoice_ident = cch_invoice.get('invoice_ident', None)
    cch_open_amount = cch_invoice['unappliedprog_amt']
    client_ident = cch_invoice.pop('client_ident')
    client_name = cch_invoice.pop('client_name')
    client_full_id = cch_invoice.pop('client_full_id')
    client, _ = Client.objects.get_or_create(client_ident=client_ident, defaults={
        'client_name': client_name, 'client_full_id': client_full_id})
    cch_invoice.update({'client': client})
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

    else:
        _ref.is_deactive = False
        # refresh project
        [ProgessInvoiceAllocation.objects.update_or_create(
            progress_invoice=_ref, project_ident=item['project_ident'], project_name=item['project_name'], defaults=item) for item in new_allocs]
        current_app_projects = ProgessInvoiceAllocation.objects.filter(
            progress_invoice=_ref)
        current_cch_projects = [item['project_ident'] for item in new_allocs]
        project_dsp = current_app_projects.exclude(
            project_ident__in=current_cch_projects)
        # Detect missing projects and delete them
        project_dsp.delete()
        if _ref.unappliedprog_amt != cch_open_amount:
            _ref.on_change_open_amount(cch_open_amount)
    _ref.auto_allocated()


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
