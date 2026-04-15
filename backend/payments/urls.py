from django.urls import path
from .views import (
    UserListView,
    PaymentListView, PaymentDetailView, CardPaymentView, CashPaymentView,
    SubscriptionPlanListView, SubscriptionPlanDetailView,
    UserSubscriptionListView, UserSubscriptionDetailView,
    GSTValidationView,
    InvoiceListView, InvoiceDetailView, InvoiceVerifyView,
    EwayBillListView, EwayBillDetailView,
)

urlpatterns = [

    # ── Users ──────────────────────────────────────────
    path('users/',                              UserListView.as_view()),

    # ── Payments ───────────────────────────────────────
    path('payments/',                           PaymentListView.as_view()),
    path('payments/<int:pk>/',                  PaymentDetailView.as_view()),
    path('payments/card/',                      CardPaymentView.as_view()),
    path('payments/cash/',                      CashPaymentView.as_view()),

    # ── Subscription Plans ─────────────────────────────
    path('plans/',                              SubscriptionPlanListView.as_view()),
    path('plans/<int:pk>/',                     SubscriptionPlanDetailView.as_view()),

    # ── User Subscriptions ─────────────────────────────
    path('subscriptions/',                      UserSubscriptionListView.as_view()),
    path('subscriptions/<int:pk>/',             UserSubscriptionDetailView.as_view()),

    # ── GST Validation ─────────────────────────────────
    path('gst/validate/',                       GSTValidationView.as_view()),
    path('gst/history/',                        GSTValidationView.as_view()),

    # ── Invoices ───────────────────────────────────────
    path('invoices/',                           InvoiceListView.as_view()),
    path('invoices/<int:pk>/',                  InvoiceDetailView.as_view()),
    path('invoices/verify/<str:invoice_number>/', InvoiceVerifyView.as_view()),

    # ── E-way Bills ────────────────────────────────────
    path('ewaybills/',                          EwayBillListView.as_view()),
    path('ewaybills/<int:pk>/',                 EwayBillDetailView.as_view()),

]