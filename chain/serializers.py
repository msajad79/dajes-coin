from rest_framework import serializers

from . import models as models_chain

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models_chain.Transaction
        fields = ('sender', 'receiver', 'value', 'timestamp')


class BlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = models_chain.Block
        fields = ('hash_block', 'prev_block', 'transactions', 'timestamp', 'difficulty', 'nonce')

    def validate_transactions(self, trxs):
        for trx in trxs:
            if trx.is_done():
                raise serializers.ValidationError("Transactions block is invalid.")
        return trxs