from itertools import chain

from django.db import models
from django.forms.models import model_to_dict
from django.db.models.base import Model

class Transaction(models.Model):
    sender = models.CharField(max_length=64)
    receiver = models.CharField(max_length=64)
    timestamp = models.DateTimeField()
    value = models.FloatField()

    def is_done(self):
        if len(self.block_transactions.all()) == 0:
            return False
        return True

class Block(models.Model):
    hash_block = models.CharField(max_length=256)
    prev_block = models.OneToOneField("Block", on_delete=models.PROTECT, null=True, blank=True)
    transactions = models.ManyToManyField("Transaction", related_name="block_transactions")
    timestamp = models.DateTimeField()
    difficulty = models.FloatField()
    nonce = models.IntegerField()    
    
    def to_dict(instance):
        opts = instance._meta
        data = {}
        for f in chain(opts.concrete_fields, opts.private_fields):
            data[f.name] = f.value_from_object(instance)
        for f in opts.many_to_many:
            data[f.name] = [model_to_dict(i) for i in f.value_from_object(instance)]
        return data
