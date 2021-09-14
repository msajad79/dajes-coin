from rest_framework import serializers

from . import models as models_chain

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models_chain.Transaction
        fields = ('sender', 'receiver', 'value', 'timestamp')

    def validate_sender(self, value):
        if len(value) != 34:
            raise serializers.ValidationError('sender address is invalid.')
        return value
    
    def validate_receiver(self, value):
        if len(value) != 34:
            raise serializers.ValidationError('receiver address is invalid.')
        return value

class BlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = models_chain.Block
        fields = ('hash_block', 'prev_block', 'transactions', 'timestamp', 'difficulty', 'nonce')

    def validate_transactions(self, trxs):
        for trx in trxs:
            if trx.is_done():
                raise serializers.ValidationError(f"Transactions is not in mempool.")
        return trxs

    def validate_prev_block(self, value):
        blocks = models_chain.Block.objects.all().order_by('-id')
        if len(blocks) == 0:
            if not value is None:
                raise serializers.ValidationError("prev_block is invalid")
        else:
            if value is None or blocks[0].id != value:
                raise serializers.ValidationError("prev_block is invalid")
        return value
        

