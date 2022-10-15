from django.db import models

class Spend(models.Model):
    spend = models.CharField(max_length=200)
    spend_date = models.DateTimeField('transaction date')
    def __str__(self):
        return self.spend

class User(models.Model):
    user = models.CharField(max_length=200)
    spendingApp = models.CharField(max_length=200)
    def __str__(self):
        return self.user
