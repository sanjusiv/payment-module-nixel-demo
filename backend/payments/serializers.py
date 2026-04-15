from rest_framework import serializers
from .models import (
    User, Payment, CardPayment, CashPayment,
    SubscriptionPlan, UserSubscription,
    GSTValidation, Invoice, EwayBill
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'phone', 'country', 'gst_number', 'created_at']


# ─────────────────────────────────────────
# SUBSCRIPTION
# ─────────────────────────────────────────
class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'


class UserSubscriptionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )
    plan = SubscriptionPlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(
        queryset=SubscriptionPlan.objects.all(), source='plan', write_only=True
    )

    class Meta:
        model = UserSubscription
        fields = ['id', 'user', 'user_id', 'plan', 'plan_id', 'status',
                  'start_date', 'end_date', 'auto_renew', 'created_at']


# ─────────────────────────────────────────
# PAYMENT
# ─────────────────────────────────────────
class PaymentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )

    class Meta:
        model = Payment
        fields = ['id', 'user', 'user_id', 'amount', 'currency',
                  'payment_type', 'status', 'description',
                  'is_international', 'created_at', 'updated_at']


class CardPaymentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )

    class Meta:
        model = CardPayment
        fields = ['id', 'user', 'user_id', 'amount', 'currency',
                  'payment_type', 'status', 'description', 'is_international',
                  'card_last_four', 'card_brand', 'card_holder_name',
                  'billing_address', 'customer_country', 'customer_postal_code',
                  'created_at', 'updated_at']
        extra_kwargs = {
            'card_last_four': {'required': False},
            'card_brand': {'required': False},
            'card_holder_name': {'required': False},
            'billing_address': {'required': False},
            'customer_country': {'required': False},
            'customer_postal_code': {'required': False},
        }


class CashPaymentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )

    class Meta:
        model = CashPayment
        fields = ['id', 'user', 'user_id', 'amount', 'currency',
                  'payment_type', 'status', 'description', 'is_international',
                  'received_by', 'receipt_number', 'location',
                  'created_at', 'updated_at']
        extra_kwargs = {
            'received_by': {'required': False},
            'receipt_number': {'required': False},
            'location': {'required': False},
        }


# ─────────────────────────────────────────
# GST
# ─────────────────────────────────────────
class GSTValidationSerializer(serializers.ModelSerializer):
    class Meta:
        model = GSTValidation
        fields = '__all__'
        read_only_fields = ['company_name', 'legal_name', 'state',
                            'status', 'is_valid', 'raw_response', 'validated_at']


# ─────────────────────────────────────────
# INVOICE
# ─────────────────────────────────────────
class InvoiceSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )

    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ['invoice_number', 'qr_code', 'tax_amount',
                            'total_amount', 'created_at', 'updated_at']

    def create(self, validated_data):
        subtotal = validated_data.get('subtotal', 0)
        tax_rate = validated_data.get('tax_rate', 18)
        tax_amount = (subtotal * tax_rate) / 100
        total_amount = subtotal + tax_amount
        validated_data['tax_amount'] = tax_amount
        validated_data['total_amount'] = total_amount
        return super().create(validated_data)


# ─────────────────────────────────────────
# E-WAY BILL
# ─────────────────────────────────────────
class EwayBillSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )

    class Meta:
        model = EwayBill
        fields = '__all__'
        read_only_fields = ['eway_bill_number', 'created_at']

    def validate_taxable_value(self, value):
        if value < 50000:
            raise serializers.ValidationError(
                "E-way bill is only required for goods worth more than ₹50,000."
            )
        return value