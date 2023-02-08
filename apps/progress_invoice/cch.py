from django.db import connections


def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def get_unapplied_process_invoices():
    connection = connections['CCH']
    data = []
    with connection.cursor() as cursor:
        query = """
SELECT 
	   I.InvoiceIdent as invoice_ident,
       InvoiceNumber as invoice_number,
	   C.clientident as client_ident,
       ClientIdSubId as client_full_id,
	   C.ClientSortName as client_name,
       BilledAmount as unappliedprog_amt,
       S.StaffName as [audit_partner]
FROM WIP W
JOIN Client C ON w.ClientIdent=C.ClientIdent
JOIN INVOICE I ON W.ProgressInvIntIdent=I.InvoiceIdent
LEFT JOIN (
	SELECT  STAFFName, ClientIdent, firmclientstaffassignmentname
   FROM clientcrs crs
   JOIN staff s ON crs.StaffIdent=s.StaffIdent
   AND crs.firmclientstaffassignmentname IN ('Audit partner', 'ITSC Partner')
) S ON C.ClientIdent= S.clientident
WHERE WIPTypeCode=3 -- code 3 is progress invoice
AND W.InvoiceIdent IS NULL --
AND BillingStatusCode<>1
and S.firmclientstaffassignmentname is not null
            """
        cursor.execute(query)
        data = dictfetchall(cursor)

        return data


def get_project_items(client_ident):
    connection = connections['CCH']
    query = f"""
    select InterimWorkingProjectIdent as project_ident
    , ProjectName as project_name
    , ProjectStatus as project_status
    from INTERIMWORKINGPROJECT where ClientIdent = '{client_ident}'  and ProjectName <> 'Internal Project' AND IsActiveFlag = 1
    """
    data = []
    with connection.cursor() as cursor:
        cursor.execute(query)
        data = dictfetchall(cursor)
    return data
