from django.urls import path
from .views import (
    UserListView,

    # Superadmin
    SuperadminPlanListView,
    SuperadminPlanDetailView,

    # Public
    PublicPlanListView,

    # Checkout flow
    RegistrationView,
    CheckoutView,
    PaymentInitiateView,
    PaymentConfirmView,
    WebhookView,

    # Payments CRUD
    PaymentListView,
    PaymentDetailView,

    # GST
    GSTValidationView,

    # Invoice
    InvoiceListView,
    InvoiceDetailView,
    InvoiceVerifyView,

    # Eway
    EwayBillListView,
    EwayBillDetailView,

    # Renewals
    RenewalCheckView,
)

urlpatterns = [

    # ── Users ──────────────────────────────────────────────
    path('users/',                                   UserListView.as_view()),

    # ── Superadmin — Plan Management ───────────────────────
    # Header required: X-Superadmin-Token: nixel-superadmin-2024
    path('admin/plans/',                             SuperadminPlanListView.as_view()),
    path('admin/plans/<int:pk>/',                    SuperadminPlanDetailView.as_view()),

    # ── Public — Plans for customers ───────────────────────
    # ?country=India or ?country=Australia
    path('plans/',                                   PublicPlanListView.as_view()),

    # ── Checkout Flow ──────────────────────────────────────
    # Step 1: Register
    path('checkout/register/',                       RegistrationView.as_view()),
    # Step 2: Select plan + get checkout details
    path('checkout/',                                CheckoutView.as_view()),
    # Step 3: Initiate payment with gateway
    path('payment/initiate/',                        PaymentInitiateView.as_view()),
    # Step 4: Confirm payment after gateway
    path('payment/confirm/',                         PaymentConfirmView.as_view()),
    # Gateway webhook
    path('webhooks/payment/',                        WebhookView.as_view()),

    # ── Payments CRUD ──────────────────────────────────────
    path('payments/',                                PaymentListView.as_view()),
    path('payments/<int:pk>/',                       PaymentDetailView.as_view()),

    # ── GST Validation ─────────────────────────────────────
    path('gst/validate/',                            GSTValidationView.as_view()),

    # ── Invoices ───────────────────────────────────────────
    path('invoices/',                                InvoiceListView.as_view()),
    path('invoices/<int:pk>/',                       InvoiceDetailView.as_view()),
    path('invoices/verify/<str:invoice_number>/',    InvoiceVerifyView.as_view()),

    # ── E-way Bills ────────────────────────────────────────
    # ?country=India or ?country=Australia
    path('ewaybills/',                               EwayBillListView.as_view()),
    path('ewaybills/<int:pk>/',                      EwayBillDetailView.as_view()),

    # ── Renewal Notifications ──────────────────────────────
    path('subscriptions/renewal-check/',             RenewalCheckView.as_view()),

]
