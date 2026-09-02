from rest_framework import serializers


class CardAdviceRequestSerializer(serializers.Serializer):
    owned_cards = serializers.ListField(
        child=serializers.CharField(max_length=100, allow_blank=False),
        allow_empty=True,
        max_length=20,
    )
    goals = serializers.CharField(max_length=500, required=False, allow_blank=True)
