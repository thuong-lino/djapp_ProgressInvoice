from django.http import JsonResponse, HttpResponseBadRequest, QueryDict, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Case, When, F, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.views.decorators.csrf import csrf_exempt
import pdb

from functools import reduce

from ..models import ProgessInvoiceAllocation, ProgressInvoice, Client

from ..utils import refresh_all
from decimal import Decimal


@csrf_exempt
def refresh_db_view(request):
    if request.method == 'POST':
        refresh_all()
        return JsonResponse({}, status=200)
    return HttpResponseNotAllowed


def get_allocations(request):
    _per_page = request.GET.get('length', 25)
    _start_index = request.GET.get('start')
    _search_value = request.GET.get('search[value]', None)

    allocated = ProgessInvoiceAllocation.objects.filter(progress_invoice__client__id=OuterRef('id')).values(
        'progress_invoice__client__id').annotate(sum_unapplied_amt=Sum('allocated_amount')).values('sum_unapplied_amt')
    unapplied = ProgressInvoice.objects.filter(client__id=OuterRef('id')).values(
        'client__id').annotate(sum_umallocated_amt=Sum('unappliedprog_amt')).values('sum_umallocated_amt')
    clients = Client.objects.annotate(unapplied_amt=Subquery(unapplied), allocated_amt=Subquery(
        allocated)).annotate(unallocated=F('unapplied_amt') - F('allocated_amt')).order_by('-unallocated')

    #clients = Client.objects.raw(query)
    if _search_value:
        searchable_fields = ['client_name',

                             ]
        queries = [Q(**{f'{f}__icontains': _search_value})
                   for f in searchable_fields]
        r = reduce(lambda a, b: a | b, queries)
        clients = clients.filter(r)
    progress_invoices = []
    for c in clients:
        progress_invoices += c
    data = []

    for invoice in progress_invoices:
        data += [alloc.to_table() for alloc in invoice]
    paginator = Paginator(data, per_page=_per_page)
    page_index = int(_start_index) // int(_per_page)
    data_in_page = paginator.get_page(
        page_index).object_list

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
