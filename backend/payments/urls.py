from django.urls import path
from .views import (
    PaymentListView,
    PaymentDetailView,
    CardPaymentView,
    CashPaymentView,
    UserListView,
)

urlpatterns = [

    # ── Users ──────────────────────────────
    path('users/',                  UserListView.as_view()),

    # ── Payments (all types) ───────────────
    path('payments/',               PaymentListView.as_view()),   # GET all, POST, DELETE all
    path('payments/<int:pk>/',      PaymentDetailView.as_view()), # GET by id, PUT, DELETE by id

    # ── Card Payments ──────────────────────
    path('payments/card/',          CardPaymentView.as_view()),   # GET all cards, POST card

    # ── Cash Payments ──────────────────────
    path('payments/cash/',          CashPaymentView.as_view()),   # GET all cash, POST cash

]