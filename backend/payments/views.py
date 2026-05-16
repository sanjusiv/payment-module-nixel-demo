import re
import qrcode
import base64
import hmac
import hashlib
from io import BytesIO
from datetime import timedelta
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import (
    User, Payment, CardPayment, CashPayment,
    SubscriptionPlan, UserSubscription,
    PaymentGatewayTransaction,
    GSTValidation, Invoice, EwayBill
)
from .serializers import (
    UserSerializer, PaymentSerializer, CardPaymentSerializer, CashPaymentSerializer,
    SubscriptionPlanSerializer, UserSubscriptionSerializer,
    PaymentGatewayTransactionSerializer,
    GSTValidationSerializer, InvoiceSerializer, EwayBillSerializer
)


# ─────────────────────────────────────────
# BASE
# ─────────────────────────────────────────
class BaseView(APIView):
    def get_object(self, model, pk):
        try:
            return model.objects.get(pk=pk)
        except model.DoesNotExist:
            return None

    def superadmin_only(self, request):
        """Check if request is from superadmin"""
        token = request.headers.get('X-Superadmin-Token', '')
        return token == 'nixel-superadmin-2024'


# ─────────────────────────────────────────
# USER
# ─────────────────────────────────────────
class UserListView(BaseView):
    def get(self, request):
        users = User.objects.all()
        return Response({'success': True, 'data': UserSerializer(users, many=True).data})

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────
# SUPERADMIN — PLAN MANAGEMENT
# ─────────────────────────────────────────
class SuperadminPlanListView(BaseView):
    """
    Superadmin only. Full plan management.
    GET  — list all plans (all statuses)
    POST — create a new plan
    """

    def get(self, request):
        if not self.superadmin_only(request):
            return Response({'success': False, 'message': 'Superadmin access only'},
                            status=status.HTTP_403_FORBIDDEN)
        plans = SubscriptionPlan.objects.all().order_by('name', 'billing_cycle')
        return Response({'success': True, 'data': SubscriptionPlanSerializer(plans, many=True).data})

    def post(self, request):
        if not self.superadmin_only(request):
            return Response({'success': False, 'message': 'Superadmin access only'},
                            status=status.HTTP_403_FORBIDDEN)
        serializer = SubscriptionPlanSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, 'message': 'Plan created', 'data': serializer.data},
                            status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class SuperadminPlanDetailView(BaseView):
    """
    GET    — view plan
    PUT    — edit plan
    DELETE — delete plan
    PATCH  — publish / hide plan
    """

    def get(self, request, pk):
        if not self.superadmin_only(request):
            return Response({'success': False, 'message': 'Superadmin access only'},
                            status=status.HTTP_403_FORBIDDEN)
        plan = self.get_object(SubscriptionPlan, pk)
        if not plan:
            return Response({'success': False, 'message': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'success': True, 'data': SubscriptionPlanSerializer(plan).data})

    def put(self, request, pk):
        if not self.superadmin_only(request):
            return Response({'success': False, 'message': 'Superadmin access only'},
                            status=status.HTTP_403_FORBIDDEN)
        plan = self.get_object(SubscriptionPlan, pk)
        if not plan:
            return Response({'success': False, 'message': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = SubscriptionPlanSerializer(plan, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, 'message': 'Plan updated', 'data': serializer.data})
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        """Publish or hide a plan"""
        if not self.superadmin_only(request):
            return Response({'success': False, 'message': 'Superadmin access only'},
                            status=status.HTTP_403_FORBIDDEN)
        plan = self.get_object(SubscriptionPlan, pk)
        if not plan:
            return Response({'success': False, 'message': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action')
        if action == 'publish':
            plan.status = 'published'
            msg = 'Plan published — now visible to customers'
        elif action == 'hide':
            plan.status = 'hidden'
            msg = 'Plan hidden from customers'
        elif action == 'draft':
            plan.status = 'draft'
            msg = 'Plan moved to draft'
        else:
            return Response({'success': False, 'message': 'action must be publish, hide or draft'},
                            status=status.HTTP_400_BAD_REQUEST)
        plan.save()
        return Response({'success': True, 'message': msg, 'data': SubscriptionPlanSerializer(plan).data})

    def delete(self, request, pk):
        if not self.superadmin_only(request):
            return Response({'success': False, 'message': 'Superadmin access only'},
                            status=status.HTTP_403_FORBIDDEN)
        plan = self.get_object(SubscriptionPlan, pk)
        if not plan:
            return Response({'success': False, 'message': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)
        plan.delete()
        return Response({'success': True, 'message': 'Plan deleted'})


# ─────────────────────────────────────────
# PUBLIC — Plans visible to customers
# ─────────────────────────────────────────
class PublicPlanListView(BaseView):
    """No auth required. Returns only published plans."""

    def get(self, request):
        country = request.query_params.get('country', 'India')
        plans = SubscriptionPlan.objects.filter(status='published')
        data = []
        for plan in plans:
            plan_data = SubscriptionPlanSerializer(plan).data
            plan_data['price'] = str(plan.get_price_for_country(country))
            plan_data['currency'] = 'INR' if country == 'India' else 'AUD' if country == 'Australia' else 'USD'
            data.append(plan_data)
        return Response({'success': True, 'country': country, 'data': data})


# ─────────────────────────────────────────
# CHECKOUT FLOW
# Step 1: Register → Step 2: Checkout → Step 3: Pay
# ─────────────────────────────────────────
class RegistrationView(BaseView):
    """
    Step 1 — Customer registers (no auth)
    POST /checkout/register/
    """

    def post(self, request):
        name = request.data.get('name')
        email = request.data.get('email')
        phone = request.data.get('phone', '')
        country = request.data.get('country', 'India')
        gst_number = request.data.get('gst_number', '')

        if not name or not email:
            return Response({'success': False, 'message': 'Name and email are required'},
                            status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({'success': False, 'message': 'Email already registered'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create(
            name=name, email=email, phone=phone,
            country=country, gst_number=gst_number,
            is_active=False  # not active until payment done
        )

        return Response({
            'success': True,
            'message': 'Registration successful. Proceed to checkout.',
            'user_id': user.id,
            'data': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class CheckoutView(BaseView):
    """
    Step 2 — Customer selects plan, gets payment details
    POST /checkout/
    """

    def post(self, request):
        user_id = request.data.get('user_id')
        plan_id = request.data.get('plan_id')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'success': False, 'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, status='published')
        except SubscriptionPlan.DoesNotExist:
            return Response({'success': False, 'message': 'Plan not found or not available'},
                            status=status.HTTP_404_NOT_FOUND)

        # Get price for user's country
        price = plan.get_price_for_country(user.country)
        currency = 'INR' if user.country == 'India' else 'AUD' if user.country == 'Australia' else 'USD'

        # Create gateway transaction record
        gateway_txn = PaymentGatewayTransaction.objects.create(
            gateway_name='razorpay',
            amount=price,
            currency=currency,
            country=user.country,
            plan=plan,
            user=user,
            status='created'
        )

        return Response({
            'success': True,
            'message': 'Checkout ready. Proceed to payment.',
            'checkout': {
                'user': UserSerializer(user).data,
                'plan': SubscriptionPlanSerializer(plan).data,
                'amount': str(price),
                'currency': currency,
                'country': user.country,
                'internal_reference': gateway_txn.internal_reference,
                'gateway_transaction_id': gateway_txn.id,
            }
        })


class PaymentInitiateView(BaseView):
    """
    Step 3 — Create payment intent with gateway
    POST /payment/initiate/
    In production: this calls Razorpay/Stripe API and returns their order_id
    """

    def post(self, request):
        gateway_txn_id = request.data.get('gateway_transaction_id')
        payment_type = request.data.get('payment_type', 'card')

        try:
            gateway_txn = PaymentGatewayTransaction.objects.get(id=gateway_txn_id)
        except PaymentGatewayTransaction.DoesNotExist:
            return Response({'success': False, 'message': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

        # Simulate gateway order creation
        # In production replace this with:
        # import razorpay
        # client = razorpay.Client(auth=("YOUR_KEY", "YOUR_SECRET"))
        # order = client.order.create({'amount': int(gateway_txn.amount * 100), 'currency': gateway_txn.currency})
        # gateway_txn.gateway_order_id = order['id']

        gateway_txn.gateway_order_id = f"order_{gateway_txn.internal_reference}"
        gateway_txn.status = 'processing'
        gateway_txn.save()

        return Response({
            'success': True,
            'message': 'Payment initiated. Complete payment on gateway.',
            'payment_intent': {
                'internal_reference': gateway_txn.internal_reference,
                'gateway_order_id': gateway_txn.gateway_order_id,
                'amount': str(gateway_txn.amount),
                'currency': gateway_txn.currency,
                'gateway': gateway_txn.gateway_name,
                'instructions': 'Pass gateway_order_id to payment gateway SDK on frontend'
            }
        })


class PaymentConfirmView(BaseView):
    """
    Step 4 — Confirm payment after gateway processes it
    POST /payment/confirm/
    """

    def post(self, request):
        internal_reference = request.data.get('internal_reference')
        gateway_payment_id = request.data.get('gateway_payment_id', '')
        gateway_signature = request.data.get('gateway_signature', '')

        try:
            gateway_txn = PaymentGatewayTransaction.objects.get(internal_reference=internal_reference)
        except PaymentGatewayTransaction.DoesNotExist:
            return Response({'success': False, 'message': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

        # In production — verify signature from Razorpay:
        # msg = f"{gateway_txn.gateway_order_id}|{gateway_payment_id}"
        # generated = hmac.new(SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()
        # if generated != gateway_signature: return 400

        gateway_txn.gateway_payment_id = gateway_payment_id
        gateway_txn.gateway_signature = gateway_signature
        gateway_txn.status = 'paid'
        gateway_txn.save()

        # Create internal payment record
        payment = Payment.objects.create(
            user=gateway_txn.user,
            gateway_transaction=gateway_txn,
            amount=gateway_txn.amount,
            currency=gateway_txn.currency,
            country=gateway_txn.country,
            payment_type='card',
            status='completed',
            description=f"Subscription payment for {gateway_txn.plan.name} plan"
        )

        # Activate subscription
        end_date = timezone.now() + timedelta(days=365 if gateway_txn.plan.billing_cycle == 'yearly' else 30)
        subscription = UserSubscription.objects.create(
            user=gateway_txn.user,
            plan=gateway_txn.plan,
            payment=payment,
            status='active',
            country=gateway_txn.country,
            amount_paid=gateway_txn.amount,
            currency=gateway_txn.currency,
            end_date=end_date
        )

        # Generate invoice automatically
        tax_rate = 18.00 if gateway_txn.country == 'India' else 10.00  # GST India vs GST Australia
        tax_amount = (gateway_txn.amount * tax_rate) / 100
        total = gateway_txn.amount + tax_amount

        invoice = Invoice.objects.create(
            user=gateway_txn.user,
            payment=payment,
            subscription=subscription,
            subtotal=gateway_txn.amount,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            total_amount=total,
            currency=gateway_txn.currency,
            buyer_email=gateway_txn.user.email,
            buyer_gst=gateway_txn.user.gst_number or '',
            status='sent'
        )

        # Generate QR code for invoice
        qr_data = f"Invoice:{invoice.invoice_number}|Amount:{total}|User:{gateway_txn.user.email}"
        qr = qrcode.make(qr_data)
        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        invoice.qr_code = base64.b64encode(buffer.getvalue()).decode()
        invoice.save()

        # Mark user registration complete (but business not active yet)
        gateway_txn.user.is_active = False  # stays False until business setup done
        gateway_txn.user.save()

        return Response({
            'success': True,
            'message': 'Payment confirmed. Registration complete. Business setup pending.',
            'data': {
                'payment_id': payment.id,
                'internal_reference': gateway_txn.internal_reference,
                'gateway_payment_id': gateway_payment_id,
                'subscription': {
                    'id': subscription.id,
                    'plan': gateway_txn.plan.name,
                    'status': subscription.status,
                    'valid_until': subscription.end_date,
                },
                'invoice': {
                    'invoice_number': invoice.invoice_number,
                    'total': str(total),
                    'currency': gateway_txn.currency,
                },
                'next_step': 'Business account setup required before going live'
            }
        })


class WebhookView(BaseView):
    """
    Receives webhook events from payment gateway
    POST /webhooks/payment/
    Gateway fires this automatically when payment status changes
    """

    def post(self, request):
        event = request.data.get('event', '')
        payload = request.data

        # Find the transaction
        gateway_order_id = request.data.get('payload', {}).get('payment', {}).get('entity', {}).get('order_id', '')

        try:
            gateway_txn = PaymentGatewayTransaction.objects.get(gateway_order_id=gateway_order_id)
        except PaymentGatewayTransaction.DoesNotExist:
            return Response({'success': False, 'message': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

        gateway_txn.webhook_event = event
        gateway_txn.webhook_payload = payload

        if event == 'payment.captured':
            gateway_txn.status = 'paid'
        elif event == 'payment.failed':
            gateway_txn.status = 'failed'
        elif event == 'refund.created':
            gateway_txn.status = 'refunded'

        gateway_txn.save()

        return Response({'success': True, 'message': f'Webhook {event} processed'})


# ─────────────────────────────────────────
# PAYMENT — full CRUD
# ─────────────────────────────────────────
class PaymentListView(BaseView):
    def get(self, request):
        payments = Payment.objects.all().order_by('-created_at')
        return Response({'success': True, 'count': payments.count(),
                         'data': PaymentSerializer(payments, many=True).data})

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
            return Response({'success': True, 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        count, _ = Payment.objects.all().delete()
        return Response({'success': True, 'message': f'{count} payments deleted'})


class PaymentDetailView(BaseView):
    def get(self, request, pk):
        payment = self.get_object(Payment, pk)
        if not payment:
            return Response({'success': False, 'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'success': True, 'data': PaymentSerializer(payment).data})

    def put(self, request, pk):
        payment = self.get_object(Payment, pk)
        if not payment:
            return Response({'success': False, 'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = PaymentSerializer(payment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, 'data': serializer.data})
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        payment = self.get_object(Payment, pk)
        if not payment:
            return Response({'success': False, 'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        payment.delete()
        return Response({'success': True, 'message': f'Payment #{pk} deleted'})


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
            return Response({'success': False, 'message': 'GST number required'}, status=status.HTTP_400_BAD_REQUEST)

        is_valid = validate_gst_format(gst_number)
        if not is_valid:
            return Response({'success': False, 'is_valid': False,
                             'message': 'Invalid GST format. Expected: 27AAPFU0939F1ZV'},
                            status=status.HTTP_400_BAD_REQUEST)

        state_codes = {
            '01': 'Jammu & Kashmir', '07': 'Delhi', '09': 'Uttar Pradesh',
            '19': 'West Bengal', '27': 'Maharashtra', '29': 'Karnataka',
            '32': 'Kerala', '33': 'Tamil Nadu', '36': 'Telangana',
        }
        state_code = gst_number[:2]
        pan_number = gst_number[2:12]
        state = state_codes.get(state_code, 'Unknown State')

        GSTValidation.objects.create(
            gst_number=gst_number, state=state, status='Active',
            is_valid=True, raw_response={'state_code': state_code, 'pan': pan_number}
        )

        return Response({
            'success': True, 'is_valid': True,
            'gst_number': gst_number, 'pan_number': pan_number,
            'state': state, 'state_code': state_code,
            'status': 'Active', 'message': 'GST number is valid'
        })


# ─────────────────────────────────────────
# INVOICE
# ─────────────────────────────────────────
class InvoiceListView(BaseView):
    def get(self, request):
        invoices = Invoice.objects.all().order_by('-created_at')
        return Response({'success': True, 'count': invoices.count(),
                         'data': InvoiceSerializer(invoices, many=True).data})

    def post(self, request):
        serializer = InvoiceSerializer(data=request.data)
        if serializer.is_valid():
            invoice = serializer.save()
            qr_data = f"Invoice:{invoice.invoice_number}|Amount:{invoice.total_amount}|User:{invoice.user.name}"
            qr = qrcode.make(qr_data)
            buffer = BytesIO()
            qr.save(buffer, format='PNG')
            invoice.qr_code = base64.b64encode(buffer.getvalue()).decode()
            invoice.save()
            return Response({'success': True, 'data': InvoiceSerializer(invoice).data},
                            status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class InvoiceDetailView(BaseView):
    def get(self, request, pk):
        invoice = self.get_object(Invoice, pk)
        if not invoice:
            return Response({'success': False, 'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'success': True, 'data': InvoiceSerializer(invoice).data})

    def put(self, request, pk):
        """Edit invoice — creates RINV- revised number"""
        invoice = self.get_object(Invoice, pk)
        if not invoice:
            return Response({'success': False, 'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        import uuid
        invoice.revised_invoice_number = f"RINV-{uuid.uuid4().hex[:8].upper()}"
        serializer = InvoiceSerializer(invoice, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, 'revised_number': invoice.revised_invoice_number,
                             'data': serializer.data})
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        invoice = self.get_object(Invoice, pk)
        if not invoice:
            return Response({'success': False, 'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        invoice.delete()
        return Response({'success': True, 'message': 'Invoice permanently deleted'})


class InvoiceVerifyView(BaseView):
    def get(self, request, invoice_number):
        try:
            invoice = Invoice.objects.get(
                models.Q(invoice_number=invoice_number) | models.Q(revised_invoice_number=invoice_number)
            )
            return Response({
                'success': True, 'is_genuine': True,
                'invoice_number': invoice.invoice_number,
                'revised_number': invoice.revised_invoice_number,
                'user': invoice.user.name, 'amount': str(invoice.total_amount),
                'status': invoice.status, 'created_at': invoice.created_at,
                'message': 'Invoice is genuine and verified'
            })
        except Invoice.DoesNotExist:
            return Response({'success': False, 'is_genuine': False,
                             'message': 'Invoice not found — may be fake or invalid'},
                            status=status.HTTP_404_NOT_FOUND)


# ─────────────────────────────────────────
# E-WAY BILL (India + Australia)
# ─────────────────────────────────────────
class EwayBillListView(BaseView):
    def get(self, request):
        country = request.query_params.get('country', None)
        bills = EwayBill.objects.all().order_by('-created_at')
        if country:
            bills = bills.filter(country=country)
        return Response({'success': True, 'data': EwayBillSerializer(bills, many=True).data})

    def post(self, request):
        serializer = EwayBillSerializer(data=request.data)
        if serializer.is_valid():
            bill = serializer.save()
            return Response({
                'success': True, 'message': 'E-way bill generated',
                'eway_bill_number': bill.eway_bill_number,
                'data': EwayBillSerializer(bill).data
            }, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class EwayBillDetailView(BaseView):
    def get(self, request, pk):
        bill = self.get_object(EwayBill, pk)
        if not bill:
            return Response({'success': False, 'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'success': True, 'data': EwayBillSerializer(bill).data})

    def patch(self, request, pk):
        bill = self.get_object(EwayBill, pk)
        if not bill:
            return Response({'success': False, 'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        bill.status = 'cancelled'
        bill.save()
        return Response({'success': True, 'message': 'E-way bill cancelled'})


# ─────────────────────────────────────────
# RENEWAL NOTIFICATIONS
# ─────────────────────────────────────────
class RenewalCheckView(BaseView):
    """
    Checks subscriptions expiring in next 7 days
    In production: run this as a scheduled cron job daily
    GET /subscriptions/renewal-check/
    """

    def get(self, request):
        if not self.superadmin_only(request):
            return Response({'success': False, 'message': 'Superadmin access only'},
                            status=status.HTTP_403_FORBIDDEN)

        seven_days = timezone.now() + timedelta(days=7)
        expiring = UserSubscription.objects.filter(
            status='active',
            end_date__lte=seven_days,
            renewal_reminder_sent=False
        )

        notified = []
        for sub in expiring:
            # In production: send email/SMS/WhatsApp here
            sub.renewal_reminder_sent = True
            sub.save()
            notified.append({
                'user': sub.user.name,
                'email': sub.user.email,
                'plan': sub.plan.name,
                'expires': sub.end_date,
            })

        return Response({
            'success': True,
            'message': f'{len(notified)} renewal reminders sent',
            'notified': notified
        })
