from django.db import models
import uuid


# ─────────────────────────────────────────
# USER
# ─────────────────────────────────────────
class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    gst_number = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.name


# ─────────────────────────────────────────
# SUBSCRIPTION PLANS
# ─────────────────────────────────────────
class SubscriptionPlan(models.Model):
    PLAN_CHOICES = [
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
    ]

    BILLING_CYCLE_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    name = models.CharField(max_length=20, choices=PLAN_CHOICES, unique=False)
    billing_cycle = models.CharField(max_length=10, choices=BILLING_CYCLE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)

    # Features per plan
    max_users = models.IntegerField(default=1)
    max_invoices = models.IntegerField(default=10)
    gst_validation = models.BooleanField(default=False)
    eway_bill = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    custom_branding = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'subscription_plans'
        unique_together = ('name', 'billing_cycle')

    def __str__(self):
        return f"{self.name} - {self.billing_cycle} - {self.price}"


class UserSubscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('paused', 'Paused'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_subscriptions'

    def __str__(self):
        return f"{self.user.name} - {self.plan.name} - {self.status}"


# ─────────────────────────────────────────
# PAYMENT
# ─────────────────────────────────────────
class Payment(models.Model):
    PAYMENT_TYPE_CHOICES = [
        ('card', 'Card'),
        ('cash', 'Cash'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='INR')
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.TextField(blank=True)
    is_international = models.BooleanField(default=False)
    subscription = models.ForeignKey(UserSubscription, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'

    def __str__(self):
        return f"Payment #{self.id} - {self.user.name} - {self.amount}"


class CardPayment(Payment):
    card_last_four = models.CharField(max_length=4, blank=True)
    card_brand = models.CharField(max_length=50, blank=True)
    card_holder_name = models.CharField(max_length=100, blank=True)
    billing_address = models.TextField(blank=True)
    customer_country = models.CharField(max_length=100, blank=True)
    customer_postal_code = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = 'card_payments'


class CashPayment(Payment):
    received_by = models.CharField(max_length=100, blank=True)
    receipt_number = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'cash_payments'


# ─────────────────────────────────────────
# GST VALIDATION
# ─────────────────────────────────────────
class GSTValidation(models.Model):
    gst_number = models.CharField(max_length=15)
    company_name = models.CharField(max_length=200, blank=True)
    legal_name = models.CharField(max_length=200, blank=True)
    state = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=50, blank=True)
    is_valid = models.BooleanField(default=False)
    raw_response = models.JSONField(null=True, blank=True)
    validated_at = models.DateTimeField(auto_now_add=True)
    validated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'gst_validations'

    def __str__(self):
        return f"{self.gst_number} - {self.company_name} - {'Valid' if self.is_valid else 'Invalid'}"


# ─────────────────────────────────────────
# INVOICE
# ─────────────────────────────────────────
class Invoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]

    invoice_number = models.CharField(max_length=50, unique=True)
    qr_code = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices')
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    subscription = models.ForeignKey(UserSubscription, on_delete=models.SET_NULL, null=True, blank=True)

    # Invoice details
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18.00)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='INR')

    # GST details
    seller_gst = models.CharField(max_length=15, blank=True)
    buyer_gst = models.CharField(max_length=15, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    due_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'invoices'

    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.user.name} - {self.total_amount}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f"INV-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


# ─────────────────────────────────────────
# E-WAY BILL
# ─────────────────────────────────────────
class EwayBill(models.Model):
    STATUS_CHOICES = [
        ('generated', 'Generated'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]

    TRANSPORT_MODE_CHOICES = [
        ('road', 'Road'),
        ('rail', 'Rail'),
        ('air', 'Air'),
        ('ship', 'Ship'),
    ]

    eway_bill_number = models.CharField(max_length=50, unique=True, blank=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='eway_bills')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='eway_bills')

    # From - To
    from_place = models.CharField(max_length=200)
    from_state = models.CharField(max_length=100)
    from_pincode = models.CharField(max_length=10)
    to_place = models.CharField(max_length=200)
    to_state = models.CharField(max_length=100)
    to_pincode = models.CharField(max_length=10)

    # Goods details
    goods_description = models.TextField()
    hsn_code = models.CharField(max_length=20, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, default='NOS')
    taxable_value = models.DecimalField(max_digits=10, decimal_places=2)

    # Transport details
    transport_mode = models.CharField(max_length=10, choices=TRANSPORT_MODE_CHOICES, default='road')
    vehicle_number = models.CharField(max_length=20, blank=True)
    transporter_name = models.CharField(max_length=200, blank=True)
    transporter_id = models.CharField(max_length=50, blank=True)

    # GST
    seller_gst = models.CharField(max_length=15, blank=True)
    buyer_gst = models.CharField(max_length=15, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='generated')
    valid_upto = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'eway_bills'

    def __str__(self):
        return f"E-way Bill #{self.eway_bill_number} - {self.from_place} to {self.to_place}"

    def save(self, *args, **kwargs):
        if not self.eway_bill_number:
            self.eway_bill_number = f"EWB-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)