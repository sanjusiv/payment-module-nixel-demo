import re
import qrcode
import base64
from io import BytesIO
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import (
    User, Payment, CardPayment, CashPayment,
    SubscriptionPlan, UserSubscription,
    GSTValidation, Invoice, EwayBill
)
from .serializers import (
    UserSerializer, PaymentSerializer, CardPaymentSerializer, CashPaymentSerializer,
    SubscriptionPlanSerializer, UserSubscriptionSerializer,
    GSTValidationSerializer, InvoiceSerializer, EwayBillSerializer
)


# ─────────────────────────────────────────
# BASE CLASS
# ─────────────────────────────────────────
class BaseView(APIView):
    def get_object(self, model, pk):
        try:
            return model.objects.get(pk=pk)
        except model.DoesNotExist:
            return None


# ─────────────────────────────────────────
# USER
# ─────────────────────────────────────────
class UserListView(BaseView):
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response({'success': True, 'data': serializer.data})

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────
# PAYMENT
# ─────────────────────────────────────────
class PaymentListView(BaseView):
    def get(self, request):
        payments = Payment.objects.all().order_by('-created_at')
        serializer = PaymentSerializer(payments, many=True)
        return Response({'success': True, 'count': payments.count(), 'data': serializer.data})

    def post(self, request):
        payment_type = request.data.get('payment_type')
        if payment_type == 'card':
            serializer = CardPaymentSerializer(data=request.data)
        elif payment_type == 'cash':
            serializer = CashPaymentSerializer(data=request.data)
        else:
            return Response({'success': False, 'message': 'payment_type must be card or cash'},
                            status=status.HTTP_400_BAD_REQUEST)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, 'message': 'Payment created', 'data': serializer.data},
                            status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        count, _ = Payment.objects.all().delete()
        return Response({'success': True, 'message': f'{count} payments deleted'})


class PaymentDetailView(BaseView):
    def get(self, request, pk):
        payment = self.get_object(Payment, pk)
        if not payment:
            return Response({'success': False, 'message': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'success': True, 'data': PaymentSerializer(payment).data})

    def put(self, request, pk):
        payment = self.get_object(Payment, pk)
        if not payment:
            return Response({'success': False, 'message': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = PaymentSerializer(payment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, 'message': 'Payment updated', 'data': serializer.data})
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        payment = self.get_object(Payment, pk)
        if not payment:
            return Response({'success': False, 'message': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)
        payment.delete()
        return Response({'success': True, 'message': f'Payment #{pk} deleted'})


class CardPaymentView(BaseView):
    def get(self, request):
        payments = CardPayment.objects.all().order_by('-created_at')
        return Response({'success': True, 'count': payments.count(),
                         'data': CardPaymentSerializer(payments, many=True).data})

    def post(self, request):
        data = request.data.copy()
        data['payment_type'] = 'card'
        serializer = CardPaymentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class CashPaymentView(BaseView):
    def get(self, request):
        payments = CashPayment.objects.all().order_by('-created_at')
        return Response({'success': True, 'count': payments.count(),
                         'data': CashPaymentSerializer(payments, many=True).data})

    def post(self, request):
        data = request.data.copy()
        data['payment_type'] = 'cash'
        serializer = CashPaymentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────
# SUBSCRIPTION PLANS
# ─────────────────────────────────────────
class SubscriptionPlanListView(BaseView):
    def get(self, request):
        plans = SubscriptionPlan.objects.filter(is_active=True)
        return Response({'success': True, 'data': SubscriptionPlanSerializer(plans, many=True).data})

    def post(self, request):
        serializer = SubscriptionPlanSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class SubscriptionPlanDetailView(BaseView):
    def get(self, request, pk):
        plan = self.get_object(SubscriptionPlan, pk)
        if not plan:
            return Response({'success': False, 'message': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'success': True, 'data': SubscriptionPlanSerializer(plan).data})

    def put(self, request, pk):
        plan = self.get_object(SubscriptionPlan, pk)
        if not plan:
            return Response({'success': False, 'message': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = SubscriptionPlanSerializer(plan, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, 'data': serializer.data})
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        plan = self.get_object(SubscriptionPlan, pk)
        if not plan:
            return Response({'success': False, 'message': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)
        plan.delete()
        return Response({'success': True, 'message': 'Plan deleted'})


class UserSubscriptionListView(BaseView):
    def get(self, request):
        subs = UserSubscription.objects.all().order_by('-created_at')
        return Response({'success': True, 'data': UserSubscriptionSerializer(subs, many=True).data})

    def post(self, request):
        serializer = UserSubscriptionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class UserSubscriptionDetailView(BaseView):
    def get(self, request, pk):
        sub = self.get_object(UserSubscription, pk)
        if not sub:
            return Response({'success': False, 'message': 'Subscription not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'success': True, 'data': UserSubscriptionSerializer(sub).data})

    def patch(self, request, pk):
        sub = self.get_object(UserSubscription, pk)
        if not sub:
            return Response({'success': False, 'message': 'Subscription not found'}, status=status.HTTP_404_NOT_FOUND)
        action = request.data.get('action')
        if action == 'cancel':
            sub.status = 'cancelled'
        elif action == 'pause':
            sub.status = 'paused'
        elif action == 'activate':
            sub.status = 'active'
        sub.save()
        return Response({'success': True, 'message': f'Subscription {action}d',
                         'data': UserSubscriptionSerializer(sub).data})


# ─────────────────────────────────────────
# GST VALIDATION
# ─────────────────────────────────────────
def validate_gst_format(gst):
    pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
    return bool(re.match(pattern, gst))


class GSTValidationView(BaseView):
    def post(self, request):
        gst_number = request.data.get('gst_number', '').strip().upper()

        if not gst_number:
            return Response({'success': False, 'message': 'GST number is required'},
                            status=status.HTTP_400_BAD_REQUEST)

        is_valid_format = validate_gst_format(gst_number)

        if not is_valid_format:
            return Response({
                'success': False,
                'is_valid': False,
                'gst_number': gst_number,
                'message': 'Invalid GST number format. Must be 15 characters (e.g. 27AAPFU0939F1ZV)'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Extract info from GST number
        state_codes = {
            '01': 'Jammu & Kashmir', '02': 'Himachal Pradesh', '03': 'Punjab',
            '04': 'Chandigarh', '05': 'Uttarakhand', '06': 'Haryana',
            '07': 'Delhi', '08': 'Rajasthan', '09': 'Uttar Pradesh',
            '10': 'Bihar', '11': 'Sikkim', '12': 'Arunachal Pradesh',
            '13': 'Nagaland', '14': 'Manipur', '15': 'Mizoram',
            '16': 'Tripura', '17': 'Meghalaya', '18': 'Assam',
            '19': 'West Bengal', '20': 'Jharkhand', '21': 'Odisha',
            '22': 'Chattisgarh', '23': 'Madhya Pradesh', '24': 'Gujarat',
            '27': 'Maharashtra', '28': 'Andhra Pradesh', '29': 'Karnataka',
            '30': 'Goa', '31': 'Lakshadweep', '32': 'Kerala',
            '33': 'Tamil Nadu', '34': 'Puducherry', '36': 'Telangana',
            '37': 'Andhra Pradesh (New)',
        }

        state_code = gst_number[:2]
        pan_number = gst_number[2:12]
        state_name = state_codes.get(state_code, 'Unknown State')

        validation = GSTValidation.objects.create(
            gst_number=gst_number,
            state=state_name,
            status='Active',
            is_valid=True,
            raw_response={
                'state_code': state_code,
                'pan': pan_number,
                'state': state_name,
            }
        )

        return Response({
            'success': True,
            'is_valid': True,
            'gst_number': gst_number,
            'pan_number': pan_number,
            'state': state_name,
            'state_code': state_code,
            'status': 'Active',
            'message': 'GST number is valid'
        })

    def get(self, request):
        validations = GSTValidation.objects.all().order_by('-validated_at')
        return Response({'success': True, 'data': GSTValidationSerializer(validations, many=True).data})


# ─────────────────────────────────────────
# INVOICE
# ─────────────────────────────────────────
def generate_qr_code(data):
    qr = qrcode.make(data)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode()


class InvoiceListView(BaseView):
    def get(self, request):
        invoices = Invoice.objects.all().order_by('-created_at')
        return Response({'success': True, 'count': invoices.count(),
                         'data': InvoiceSerializer(invoices, many=True).data})

    def post(self, request):
        serializer = InvoiceSerializer(data=request.data)
        if serializer.is_valid():
            invoice = serializer.save()
            # Generate QR code with invoice details
            qr_data = f"Invoice: {invoice.invoice_number} | Amount: {invoice.total_amount} {invoice.currency} | User: {invoice.user.name}"
            invoice.qr_code = generate_qr_code(qr_data)
            invoice.save()
            return Response({
                'success': True,
                'message': 'Invoice created',
                'data': InvoiceSerializer(invoice).data
            }, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class InvoiceDetailView(BaseView):
    def get(self, request, pk):
        invoice = self.get_object(Invoice, pk)
        if not invoice:
            return Response({'success': False, 'message': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'success': True, 'data': InvoiceSerializer(invoice).data})

    def delete(self, request, pk):
        invoice = self.get_object(Invoice, pk)
        if not invoice:
            return Response({'success': False, 'message': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)
        invoice.delete()
        return Response({'success': True, 'message': f'Invoice deleted'})


class InvoiceVerifyView(BaseView):
    def get(self, request, invoice_number):
        try:
            invoice = Invoice.objects.get(invoice_number=invoice_number)
            return Response({
                'success': True,
                'is_genuine': True,
                'invoice_number': invoice.invoice_number,
                'user': invoice.user.name,
                'amount': str(invoice.total_amount),
                'currency': invoice.currency,
                'status': invoice.status,
                'created_at': invoice.created_at,
                'message': 'Invoice is genuine and verified'
            })
        except Invoice.DoesNotExist:
            return Response({
                'success': False,
                'is_genuine': False,
                'invoice_number': invoice_number,
                'message': 'Invoice not found — may be fake or invalid'
            }, status=status.HTTP_404_NOT_FOUND)


# ─────────────────────────────────────────
# E-WAY BILL
# ─────────────────────────────────────────
class EwayBillListView(BaseView):
    def get(self, request):
        bills = EwayBill.objects.all().order_by('-created_at')
        return Response({'success': True, 'data': EwayBillSerializer(bills, many=True).data})

    def post(self, request):
        serializer = EwayBillSerializer(data=request.data)
        if serializer.is_valid():
            bill = serializer.save()
            return Response({
                'success': True,
                'message': 'E-way bill generated',
                'eway_bill_number': bill.eway_bill_number,
                'data': EwayBillSerializer(bill).data
            }, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class EwayBillDetailView(BaseView):
    def get(self, request, pk):
        bill = self.get_object(EwayBill, pk)
        if not bill:
            return Response({'success': False, 'message': 'E-way bill not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'success': True, 'data': EwayBillSerializer(bill).data})

    def patch(self, request, pk):
        bill = self.get_object(EwayBill, pk)
        if not bill:
            return Response({'success': False, 'message': 'E-way bill not found'}, status=status.HTTP_404_NOT_FOUND)
        bill.status = 'cancelled'
        bill.save()
        return Response({'success': True, 'message': 'E-way bill cancelled'})