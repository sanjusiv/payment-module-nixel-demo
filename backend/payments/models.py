from django.db import models
import uuid


# ─────────────────────────────────────────
# USER
# ─────────────────────────────────────────
class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='India')
    gst_number = models.CharField(max_length=15, blank=True, null=True)
    is_active = models.BooleanField(default=False)  # becomes True after business setup
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.name} ({self.email})"


# ─────────────────────────────────────────
# SUBSCRIPTION PLANS (Superadmin manages)
# ─────────────────────────────────────────
class SubscriptionPlan(models.Model):
    PLAN_NAMES = [
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
    ]
    BILLING_CYCLES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    STATUS = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('hidden', 'Hidden'),
    ]

    name = models.CharField(max_length=20, choices=PLAN_NAMES)
    billing_cycle = models.CharField(max_length=10, choices=BILLING_CYCLES)
    status = models.CharField(max_length=15, choices=STATUS, default='draft')

    # Pricing per country
    price_inr = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_aud = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Features
    max_users = models.IntegerField(default=1)
    max_products = models.IntegerField(default=100)
    gst_validation = models.BooleanField(default=False)
    eway_bill = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    custom_branding = models.BooleanField(default=False)
    multi_location = models.BooleanField(default=False)

    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscription_plans'
        unique_together = ('name', 'billing_cycle')

    def get_price_for_country(self, country):
        """Returns correct price based on country"""
        mapping = {
            'India': self.price_inr,
            'Australia': self.price_aud,
        }
        return mapping.get(country, self.price_usd)

    def __str__(self):
        return f"{self.name} - {self.billing_cycle} - {self.status}"


# ─────────────────────────────────────────
# PAYMENT GATEWAY REFERENCE
# Records every transaction with the gateway
# ─────────────────────────────────────────
class PaymentGatewayTransaction(models.Model):
    GATEWAY_CHOICES = [
        ('razorpay', 'Razorpay'),
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
    ]
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('processing', 'Processing'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
        ('refunded', 'Refunded'),
    ]

    # Gateway reference IDs
    gateway_name = models.CharField(max_length=20, choices=GATEWAY_CHOICES, default='razorpay')
    gateway_order_id = models.CharField(max_length=100, unique=True, blank=True)
    gateway_payment_id = models.CharField(max_length=100, blank=True)
    gateway_signature = models.CharField(max_length=255, blank=True)

    # Our internal reference
    internal_reference = models.CharField(max_length=50, unique=True, blank=True)

    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='INR')
    country = models.CharField(max_length=100, default='India')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')

    # What this payment is for
    plan = models.ForeignKey('SubscriptionPlan', on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True)

    # Webhook data received from gateway
    webhook_event = models.CharField(max_length=100, blank=True)
    webhook_payload = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payment_gateway_transactions'

    def save(self, *args, **kwargs):
        if not self.internal_reference:
            self.internal_reference = f"PAY-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.internal_reference} - {self.gateway_name} - {self.status}"


# ─────────────────────────────────────────
# PAYMENT (internal record)
# ─────────────────────────────────────────
class Payment(models.Model):
    PAYMENT_TYPE_CHOICES = [
        ('card', 'Card'),
        ('cash', 'Cash'),
        ('upi', 'UPI'),
        ('netbanking', 'Net Banking'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    gateway_transaction = models.OneToOneField(
        PaymentGatewayTransaction, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='payment'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='INR')
    country = models.CharField(max_length=100, default='India')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.TextField(blank=True)
    is_international = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'

    def __str__(self):
        return f"Payment #{self.id} - {self.user.name} - {self.amount} {self.currency}"


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
# USER SUBSCRIPTION
# ─────────────────────────────────────────
class UserSubscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('paused', 'Paused'),
        ('pending', 'Pending'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    payment = models.OneToOneField(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    country = models.CharField(max_length=100, default='India')  # country where sub was made
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='INR')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=True)
    renewal_reminder_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_subscriptions'

    def __str__(self):
        return f"{self.user.name} - {self.plan.name} - {self.status}"


# ─────────────────────────────────────────
# INVOICE (linked to payment)
# ─────────────────────────────────────────
class Invoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]

    invoice_number = models.CharField(max_length=50, unique=True, blank=True)
    revised_invoice_number = models.CharField(max_length=50, blank=True)  # RINV- prefix for edits
    qr_code = models.TextField(blank=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices')
    payment = models.OneToOneField(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    subscription = models.ForeignKey(UserSubscription, on_delete=models.SET_NULL, null=True, blank=True)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18.00)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='INR')

    seller_gst = models.CharField(max_length=15, blank=True)
    buyer_gst = models.CharField(max_length=15, blank=True)
    buyer_email = models.EmailField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    due_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'invoices'

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f"INV-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.user.name} - {self.total_amount}"


# ─────────────────────────────────────────
# GST VALIDATION
# ─────────────────────────────────────────
class GSTValidation(models.Model):
    gst_number = models.CharField(max_length=15)
    company_name = models.CharField(max_length=200, blank=True)
    state = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=50, blank=True)
    is_valid = models.BooleanField(default=False)
    raw_response = models.JSONField(null=True, blank=True)
    validated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'gst_validations'

    def __str__(self):
        return f"{self.gst_number} - {'Valid' if self.is_valid else 'Invalid'}"


# ─────────────────────────────────────────
# E-WAY BILL (India + Australia)
# ─────────────────────────────────────────
class EwayBill(models.Model):
    COUNTRY_CHOICES = [
        ('India', 'India'),
        ('Australia', 'Australia'),
    ]
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
    country = models.CharField(max_length=20, choices=COUNTRY_CHOICES, default='India')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='eway_bills')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='eway_bills')

    from_place = models.CharField(max_length=200)
    from_state = models.CharField(max_length=100)
    from_pincode = models.CharField(max_length=10)
    to_place = models.CharField(max_length=200)
    to_state = models.CharField(max_length=100)
    to_pincode = models.CharField(max_length=10)

    goods_description = models.TextField()
    hsn_code = models.CharField(max_length=20, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, default='NOS')
    taxable_value = models.DecimalField(max_digits=10, decimal_places=2)

    transport_mode = models.CharField(max_length=10, choices=TRANSPORT_MODE_CHOICES, default='road')
    vehicle_number = models.CharField(max_length=20, blank=True)
    transporter_name = models.CharField(max_length=200, blank=True)

    seller_gst = models.CharField(max_length=15, blank=True)
    buyer_gst = models.CharField(max_length=15, blank=True)

    # Australia equivalent fields
    abn_number = models.CharField(max_length=20, blank=True)  # ABN for Australia
    consignment_note = models.CharField(max_length=50, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='generated')
    valid_upto = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'eway_bills'

    def save(self, *args, **kwargs):
        if not self.eway_bill_number:
            prefix = "EWB-IN" if self.country == 'India' else "EWB-AU"
            self.eway_bill_number = f"{prefix}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.eway_bill_number} - {self.from_place} to {self.to_place}"
