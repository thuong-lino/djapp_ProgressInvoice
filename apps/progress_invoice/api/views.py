from django.http import JsonResponse, HttpResponseBadRequest, QueryDict, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Case, When, F
from django.views.decorators.csrf import csrf_exempt

from functools import reduce

from ..models import ProgessInvoiceAllocation, ProgressInvoice

from ..utils import refresh_all


@csrf_exempt
def refresh_db_view(request):
    if request.method == 'POST':
        refresh_all()
        return JsonResponse({}, status=200)
    return HttpResponseNotAllowed


def get_allocations(request):

    _per_page = request.GET.get('length', 25)
    _page_index = request.GET.get('start', 0)
    _search_value = request.GET.get('search[value]', None)
    progress_invoices = ProgressInvoice.objects.annotate(sum_applied=F('unappliedprog_amt') - Sum(Case(When(
        allocs__is_alloc_active=True, then=F('allocs__allocated_amount'))))).order_by('-sum_applied')

    allocs = ProgessInvoiceAllocation.objects.filter(
        progress_invoice__is_deactive=False)
    if _search_value:
        searchable_fields = ['progress_invoice__client_name',
                             'progress_invoice__client_full_id',
                             'progress_invoice__audit_partner']
        queries = [Q(**{f'allocs__{f}__icontains': _search_value})
                   for f in searchable_fields]
        r = reduce(lambda a, b: a | b, queries)
        progress_invoices = progress_invoices.filter(r)
    total = allocs.count()
    paginator = Paginator(allocs, per_page=_per_page)
    data_in_page = paginator.get_page(_page_index).object_list
    #data = [item.to_table() for item in data_in_page]
    data = []

    for invoice in progress_invoices:
        data += [alloc.to_table() for alloc in invoice]

    res = {
        'data': data,
        'recordsTotal': len(data),
        'recordsFiltered': len(data)
    }

    return JsonResponse(res)


def put_allocation(request, alloc_id):

    if request.method == 'PUT':
        alloc = get_object_or_404(ProgessInvoiceAllocation, pk=alloc_id)
        query_dict = QueryDict(request.body)
        alloc.allocate_amount(query_dict.get('allocated_amount'))

        return JsonResponse(alloc.to_table())
    return HttpResponseBadRequest
