import uuid
from django.db import models
from django.utils import timezone

from accounts.models import CustomUser, Shop


class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    cheque_id = models.UUIDField(default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="transactions")
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    amount = models.IntegerField(default=0)
    comment = models.TextField(blank=True, null=True)
    redirect_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    payed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.email} - {self.amount} UZS - {self.status}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['shop']),
            models.Index(fields=['status']),
        ]

    @classmethod
    def filter_transactions(cls, shop_id=None, start_date=None, end_date=None, status=None):
        """
        Filter transactions by:
        - shop_id: Filter by specific shop
        - start_date: Filter transactions after this date
        - end_date: Filter transactions before this date
        - status: Filter by transaction status
        """
        queryset = cls.objects.all()

        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)

        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)

        if end_date:
            # Include the entire end_date day
            end_date = end_date + timezone.timedelta(days=1)
            queryset = queryset.filter(created_at__lt=end_date)

        if status:
            queryset = queryset.filter(status=status)

        return queryset