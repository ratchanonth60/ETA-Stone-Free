from rest_framework import serializers

from ecommerce.apps.communication.models import (
    CommunicationEventType,
    Email,
    Notification,
)


class CommunicationEventTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunicationEventType
        fields = "__all__"


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Email
        fields = "__all__"
