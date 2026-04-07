from rest_framework import serializers
from .models import User, Payment, CardPayment, CashPayment


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'phone', 'country', 'created_at']


class PaymentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )

    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'user_id', 'amount', 'currency',
            'payment_type', 'status', 'description',
            'is_international', 'created_at', 'updated_at'
        ]


class CardPaymentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )

    class Meta:
        model = CardPayment
        fields = [
            'id', 'user', 'user_id', 'amount', 'currency',
            'payment_type', 'status', 'description', 'is_international',
            'card_last_four', 'card_brand', 'card_holder_name',
            'billing_address', 'customer_country', 'customer_postal_code',
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'card_last_four': {'required': False},
            'card_brand': {'required': False},
            'card_holder_name': {'required': False},
            'billing_address': {'required': False},
            'customer_country': {'required': False},
            'customer_postal_code': {'required': False},
        }

    def validate_card_last_four(self, value):
        if value and (not value.isdigit() or len(value) != 4):
            raise serializers.ValidationError("card_last_four must be exactly 4 digits.")
        return value


class CashPaymentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )

    class Meta:
        model = CashPayment
        fields = [
            'id', 'user', 'user_id', 'amount', 'currency',
            'payment_type', 'status', 'description', 'is_international',
            'received_by', 'receipt_number', 'location',
            'created_at', 'updated_at'
        ]