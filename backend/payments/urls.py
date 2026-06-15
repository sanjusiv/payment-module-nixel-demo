from django.urls import path
from .views import (
    UserListView,

    # superadmin views
    SuperadminPlanListView,
    SuperadminPlanDetailView,

    # public facing
    PublicPlanListView,

    # checkout steps
    RegistrationView,
    CheckoutView,
    PaymentInitiateView,
    PaymentConfirmView,
    WebhookView,

    # payment endpoints
    PaymentListView,
    PaymentDetailView,

    # gst
    GSTValidationView,

    # invoices
    InvoiceListView,
    InvoiceDetailView,
    InvoiceVerifyView,

    # eway bill
    EwayBillListView,
    EwayBillDetailView,

    # renewals
    RenewalCheckView,
)

urlpatterns = [

    # users
    path('users/', UserListView.as_view()),

    # superadmin only - need to pass X-Superadmin-Token header
    path('admin/plans/', SuperadminPlanListView.as_view()),
    path('admin/plans/<int:pk>/', SuperadminPlanDetailView.as_view()),

    # public plans page - pass country as query param eg ?country=India
    path('plans/', PublicPlanListView.as_view()),

    # checkout flow
    # step 1 - register the customer first
    path('checkout/register/', RegistrationView.as_view()),
    # step 2 - customer selects plan
    path('checkout/', CheckoutView.as_view()),
    # step 3 - create payment session with gateway
    path('payment/initiate/', PaymentInitiateView.as_view()),
    # step 4 - confirm after gateway processes
    path('payment/confirm/', PaymentConfirmView.as_view()),
    # webhook - gateway sends events here
    path('webhooks/payment/', WebhookView.as_view()),

    # payments
    path('payments/', PaymentListView.as_view()),
    path('payments/<int:pk>/', PaymentDetailView.as_view()),

    # gst validation
    path('gst/validate/', GSTValidationView.as_view()),

    # invoices - verify endpoint checks if invoice is real or fake
    path('invoices/', InvoiceListView.as_view()),
    path('invoices/<int:pk>/', InvoiceDetailView.as_view()),
    path('invoices/verify/<str:invoice_number>/', InvoiceVerifyView.as_view()),

    # eway bills - filter by country using ?country=India or ?country=Australia
    path('ewaybills/', EwayBillListView.as_view()),
    path('ewaybills/<int:pk>/', EwayBillDetailView.as_view()),

    # check subscriptions expiring soon and send reminders
    path('subscriptions/renewal-check/', RenewalCheckView.as_view()),

]