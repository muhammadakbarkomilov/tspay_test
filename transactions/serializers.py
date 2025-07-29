from rest_framework import serializers
from .models import Transaction
from accounts.models import Shop
from accounts.serializers import UserSerializer


class TransactionSerializer(serializers.ModelSerializer):
    payment_url = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = ['id', 'cheque_id', 'amount', 'payment_url','redirect_url', 'created_at', 'status']

    def get_payment_url(self, obj):
        return f"http://tspay.uz/pay/{obj.cheque_id}/"

    def validate_amount(self, value):
        if value < 500:
            raise serializers.ValidationError("Minimal summa 500 so‘m bo‘lishi kerak.")
        return value

class ShopSerializers(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop('owner', None)  # 👈 owner bo‘lsa ham olib tashlaydi
        return data

class ShopsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['id','shop_id', 'image', 'title', 'status', 'created_at','access_token']