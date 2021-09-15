from django.forms.models import model_to_dict

from rest_framework.views import APIView
from rest_framework.generics import ListAPIView 
from rest_framework.response import Response

from .serializers import TransactionSerializer, BlockSerializer
from .models import Transaction, Block

class add_transaction(APIView):
    def post(self, request):
        transaction_srl = TransactionSerializer(
            data=request.data
        )
        if transaction_srl.is_valid():
            trx = transaction_srl.save()
            trx = model_to_dict(trx)
            return Response(data={'OK':True, 'message':'Transaction added successfully.', 'trx':trx}, status=200)
        return Response(data={'OK':False, 'message': transaction_srl.errors}, status=400)


class add_block(APIView):
    def post(self, request):
        block_srl = BlockSerializer(
            data=request.data
        )
        if block_srl.is_valid():
            block = block_srl.save()
            block = block.to_dict()
            return Response(data={'OK':True, 'message':'Block added successfully.', 'block':block}, status=200)
        return Response(data={'OK':False, 'message': block_srl.errors}, status=400)

class ListTransactions(APIView):
    def get(self, request):
        trxs = Transaction.objects.values()
        return Response({'trxs':trxs}, 200)
