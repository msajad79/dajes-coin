from django.db import models

class NeighborNode(models.Model):
    ip = models.CharField(max_length=128)
    port = models.IntegerField(null=True, blank=True)


