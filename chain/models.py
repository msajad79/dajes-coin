from itertools import chain

from django.db import models
from django.forms.models import model_to_dict

from . import validators_block as block_val
from . import validators_trx as trx_val

class Transaction(models.Model):
    sender = models.CharField(max_length=64, validators=[trx_val.validate_sender])
    receiver = models.CharField(max_length=64, validators=[trx_val.validate_receiver])
    timestamp = models.DateTimeField()
    value = models.FloatField()

    def is_done(self):
        if len(self.block_transactions.all()) == 0:
            return False
        return True

class Block(models.Model):
    hash_block = models.CharField(max_length=256, validators=[block_val.validate_hash_block])
    prev_block = models.OneToOneField(
        "Block",
        on_delete=models.PROTECT,
        validators=[block_val.validate_prev_block],
        null=True,
        blank=True
    )
    transactions = models.ManyToManyField("Transaction", related_name="block_transactions")
    timestamp = models.DateTimeField(validators=[block_val.validate_timestamp])
    difficulty = models.PositiveIntegerField(validators=[block_val.validate_difficulty])
    nonce = models.IntegerField()

    def to_dict(instance):
        opts = instance._meta
        data = {}
        for f in chain(opts.concrete_fields, opts.private_fields):
            data[f.name] = f.value_from_object(instance)
        for f in opts.many_to_many:
            data[f.name] = [model_to_dict(i) for i in f.value_from_object(instance)]
        return data
    
    @staticmethod
    def get_difficulty():
        blocks = Block.objects.all().order_by('-id')[:5]
        avg = blocks.aggregate(models.Avg('difficulty'))
        avg = avg['difficulty__avg']
        if avg is None:
            return 1
        diff_time = (blocks[len(blocks)-1].timestamp - blocks[0].timestamp).total_seconds()
        try:
            avg = int(avg * ((60*len(blocks))/diff_time))
        except ZeroDivisionError:
            avg = int(avg)
        if avg == 0:
            return 1
        return avg
