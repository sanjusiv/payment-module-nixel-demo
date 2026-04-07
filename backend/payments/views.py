from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Payment, CardPayment, CashPayment, User
from .serializers import (
    PaymentSerializer, CardPaymentSerializer,
    CashPaymentSerializer, UserSerializer
)


# ─────────────────────────────────────────
# PARENT CLASS — base logic shared by all
# ─────────────────────────────────────────
class BasePaymentView(APIView):
    """
    Parent class. Holds shared helpers.
    Child classes inherit from this.
    """
    def get_object(self, model, pk):
        try:
            return model.objects.get(pk=pk)
        except model.DoesNotExist:
            return None


# ─────────────────────────────────────────
# PAYMENT — GET all, POST, DELETE all
# ─────────────────────────────────────────
class PaymentListView(BasePaymentView):
    """
    GET  /payments      → list all payments
    POST /payments      → create a payment
    DELETE /payments    → delete all payments
    """

    def get(self, request):
        payments = Payment.objects.all().order_by('-created_at')
        serializer = PaymentSerializer(payments, many=True)
        return Response({
            'success': True,
            'count': payments.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        payment_type = request.data.get('payment_type')

        if payment_type == 'card':
            serializer = CardPaymentSerializer(data=request.data)
        elif payment_type == 'cash':
            serializer = CashPaymentSerializer(data=request.data)
        else:
            return Response({
                'success': False,
                'message': 'payment_type must be card or cash'
            }, status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Payment created successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        count, _ = Payment.objects.all().delete()
        return Response({
            'success': True,
            'message': f'{count} payments deleted'
        }, status=status.HTTP_200_OK)


# ─────────────────────────────────────────
# PAYMENT — GET by id, PUT, DELETE by id
# ─────────────────────────────────────────
class PaymentDetailView(BasePaymentView):
    """
    GET    /payments/:id  → get single payment
    PUT    /payments/:id  → replace entire payment
    DELETE /payments/:id  → delete by id
    """

    def get(self, request, pk):
        payment = self.get_object(Payment, pk)
        if not payment:
            return Response({
                'success': False,
                'message': 'Payment not found'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = PaymentSerializer(payment)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def put(self, request, pk):
        payment = self.get_object(Payment, pk)
        if not payment:
            return Response({
                'success': False,
                'message': 'Payment not found'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = PaymentSerializer(payment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Payment updated successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        payment = self.get_object(Payment, pk)
        if not payment:
            return Response({
                'success': False,
                'message': 'Payment not found'
            }, status=status.HTTP_404_NOT_FOUND)

        payment.delete()
        return Response({
            'success': True,
            'message': f'Payment #{pk} deleted'
        }, status=status.HTTP_200_OK)


# ─────────────────────────────────────────
# CARD PAYMENT — inherits BasePaymentView
# ─────────────────────────────────────────
class CardPaymentView(BasePaymentView):
    """
    GET  /payments/card      → all card payments
    POST /payments/card      → create card payment
    """

    def get(self, request):
        payments = CardPayment.objects.all().order_by('-created_at')
        serializer = CardPaymentSerializer(payments, many=True)
        return Response({
            'success': True,
            'count': payments.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data.copy()
        data['payment_type'] = 'card'
        serializer = CardPaymentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Card payment created',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────
# CASH PAYMENT — inherits BasePaymentView
# ─────────────────────────────────────────
class CashPaymentView(BasePaymentView):
    """
    GET  /payments/cash      → all cash payments
    POST /payments/cash      → create cash payment
    """

    def get(self, request):
        payments = CashPayment.objects.all().order_by('-created_at')
        serializer = CashPaymentSerializer(payments, many=True)
        return Response({
            'success': True,
            'count': payments.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data.copy()
        data['payment_type'] = 'cash'
        serializer = CashPaymentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Cash payment created',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────
# USER
# ─────────────────────────────────────────
class UserListView(BasePaymentView):
    """
    GET  /users    → list all users
    POST /users    → create user
    """

    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response({'success': True, 'data': serializer.data})

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)