from django.urls import path
from rest_framework import views

from . import views as views_chain

urlpatterns = [
    path('add_transaction/', views_chain.add_transaction.as_view(), name='add_transaction'),
    path('add_block/', views_chain.add_block.as_view(), name='add_block'),
    path('list_transactions/', views_chain.ListTransactions.as_view(), name='list_transactions'),
]

