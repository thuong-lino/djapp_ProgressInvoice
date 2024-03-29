from django.db import models
from django.db.models import Q
from django.forms.models import model_to_dict
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.utils.translation import gettext as _
# Create your models here.


class ModelWithMetaData(models.Model):
    created_at = models.DateTimeField(db_column='CreatedAt', auto_now_add=True)
    updated_at = models.DateTimeField(db_column='UpdatedAt', auto_now=True)

    class Meta:
        abstract = True


class Client(ModelWithMetaData):
    client_ident = models.CharField(db_column='ClientIdent', max_length=39)
    client_name = models.CharField(db_column='ClientSortName', max_length=255)
    client_full_id = models.CharField(_("Client ID"), max_length=50)

    def __str__(self) -> str:
        return f"{self.client_name} ({self.client_full_id})"

    def __iter__(self):
        return iter(self.prog_invs.all())

    class Meta:
        db_table = 'tblClient'
        ordering = ('client_name', )


class ProgressInvoice(ModelWithMetaData):
    invoice_ident = models.CharField(db_column='InvoiceIdent', max_length=39)
    invoice_number = models.CharField(db_column='InvoiceNumber', max_length=25)
    unbilled_wip = models.DecimalField(
        db_column='UnbilledWIP', max_digits=9, decimal_places=2, null=True)
    unappliedprog_amt = models.DecimalField(
        db_column='OpenAmount', max_digits=9, decimal_places=2)
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name='prog_invs')
    is_deactive = models.BooleanField(
        db_column='IsDeactivated', default=False)
    audit_partner = models.CharField(
        db_column='AuditPartner', max_length=255, null=True, default='')

    class Meta:
        db_table = 'tblProgressInvoice'

    @property
    def display_client_name(self):
        return f"{self.client.client_name} ({self.client.client_full_id})"

    @property
    def display_invoice_name(self):
        display = f"Invoice Number: [{self.invoice_number}]"
        # if self.is_all_allocated():
        #     display += f'Remaining: [{self.remaining_amount}]'
        return display

    @property
    def total_applied_value(self):
        s = 0
        for alloc in self:
            if alloc.is_alloc_active:
                s += alloc.allocated_amount
        return s

    @property
    def remaining_amount(self):
        return self.unappliedprog_amt - self.total_applied_value

    def is_all_allocated(self):
        if all([alloc.allocated_amount != 0 for alloc in self]):
            return True
        return False

    def on_change_open_amount(self, value):
        for alloc in self:
            alloc.reset()
        print('On Change Amount Evennt')
        self.unappliedprog_amt = value
        # self.save()

    def __str__(self) -> str:
        return f"InvoiceNumber: {self.invoice_number}, ClientName: {self.client.client_name}, OpenAmount: {self.unappliedprog_amt}, RemainingAmount: {self.remaining_amount}"

    def __iter__(self):
        return iter(self.allocs.all())

    def auto_allocated(self):
        allocs = self.allocs.exclude(project_ident=None)
        if allocs.count() == 1:
            alloc = allocs.first()
            if self.remaining_amount >= self.unappliedprog_amt:
                alloc.allocated_amount = self.unappliedprog_amt
                alloc.is_auto_applied_amount = True
                alloc.save()
        elif allocs.count() > 1:
            allocs = allocs.exclude(project_status='Complete')
            if allocs.count() == 1:
                alloc = allocs.first()
                if self.remaining_amount >= self.unappliedprog_amt:
                    alloc.allocated_amount = self.unappliedprog_amt
                    alloc.is_auto_applied_amount = True
                    alloc.save()

    def save(self, *args, **kwargs):
        if self.allocs.exclude(project_ident=None).count() == 0:
            print('Deactive Invoice:', self.invoice_number)
            self.is_deactive = True
        super().save(*args, **kwargs)
        # self.auto_allocated()


class ProgessInvoiceAllocation(ModelWithMetaData):
    progress_invoice = models.ForeignKey(
        ProgressInvoice,  on_delete=models.CASCADE, related_name='allocs')
    project_ident = models.CharField(
        db_column='ProjectIdent', max_length=39, null=True, blank=True)
    project_name = models.CharField(db_column='ProjectName', max_length=255)
    project_status = models.CharField(
        db_column='ProjectStatus', max_length=255, null=True, blank=True)
    allocated_amount = models.DecimalField(
        db_column='AppliedAmount', max_digits=9, decimal_places=2, default=0)
    is_alloc_active = models.BooleanField(db_column='IsActive', default=True)
    is_auto_applied_amount = models.BooleanField(
        db_column='IsAutoApplied', default=False)

    class Meta:
        db_table = 'tblProgressInvoiceAllocation'

    def save(self, *args, **kwargs) -> None:
        if self.allocated_amount == 0:
            self.is_alloc_active = True
        return super().save(*args, **kwargs)

    @property
    def display_project_name(self):
        if self.project_status is None or self.project_status == '':
            return self.project_name
        return f'{self.project_name} (Status: "{self.project_status}")'

    def to_table(self):
        parent = self.progress_invoice
        data = model_to_dict(self, exclude=['progress_invoice'])
        data.update(model_to_dict(parent, exclude=['id']))
        data['display_client_name'] = parent.display_client_name
        data['display_invoice_name'] = parent.display_invoice_name
        data['display_project_name'] = self.display_project_name
        data['audit_partner'] = parent.audit_partner
        data['remaining_amount'] = parent.remaining_amount if self.allocated_amount == 0 else ''
        return data

    def set_alloc_status(self, status):
        """active status"""
        self.is_alloc_active = status
        self.save()

    def reset(self):
        self.allocated_amount = 0
        self.is_alloc_active = True
        self.is_auto_applied_amount = False
        self.save()

    def allocate_amount(self, value):
        """raise ValidationError"""
        if type(value) is not Decimal:
            try:
                value = Decimal(value)
            except:
                value = self.allocated_amount
        if self.is_alloc_active:
            if self.progress_invoice.remaining_amount + self.allocated_amount >= value:
                print(
                    f'New Allocation from {self.allocated_amount} to {value}')
                self.allocated_amount = value
                self.is_auto_applied_amount = False
                self.save()
            else:
                if self.progress_invoice.remaining_amount + self.allocated_amount == Decimal('0.00'):
                    msg = f'Could not allocate amount {value}. No more available Unapplied Progress Amount'
                else:
                    msg = f'Could not allocate amount {value}. Please try amount less than {self.progress_invoice.remaining_amount + self.allocated_amount}'
                raise ValidationError(msg, 'allocate_error')

    def __str__(self) -> str:
        return f"<{self.project_name}: {self.allocated_amount}>"

    def __repr__(self) -> str:
        return f"<{self.project_name}({self.project_ident}): {self.allocated_amount}>"
