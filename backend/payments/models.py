from django.db import models


class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.name


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
    currency = models.CharField(max_length=10, default='USD')
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPE_CHOICES)
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
    """Subclass of Payment for card-specific details"""
    card_last_four = models.CharField(max_length=4)
    card_brand = models.CharField(max_length=50)  # Visa, Mastercard etc
    card_holder_name = models.CharField(max_length=100)
    billing_address = models.TextField(blank=True)

    # International customer details
    customer_country = models.CharField(max_length=100, blank=True)
    customer_postal_code = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = 'card_payments'

    def __str__(self):
        return f"Card Payment #{self.id} - **** {self.card_last_four}"


class CashPayment(Payment):
    """Subclass of Payment for cash-specific details"""
    received_by = models.CharField(max_length=100)
    receipt_number = models.CharField(max_length=50, unique=True)
    location = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'cash_payments'

    def __str__(self):
        return f"Cash Payment #{self.id} - Receipt: {self.receipt_number}"