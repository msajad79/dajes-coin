from django.db import models
from django.db.models.base import Model

class Transaction(models.Model):
    sender = models.CharField(max_length=64)
    receiver = models.CharField(max_length=64)
    timestamp = models.DateTimeField()
    value = models.FloatField()

class Block(models.Model):
    hash_block = models.CharField(max_length=256)
    prev_block = models.ForeignKey("Block", on_delete=models.PROTECT, unique=True)
    transactions = models.ManyToManyField("Transaction", related_name="block_transactions", unique=True)
    timestamp = models.DateTimeField()
    difficulty = models.FloatField()
    nonce = models.IntegerField()    
