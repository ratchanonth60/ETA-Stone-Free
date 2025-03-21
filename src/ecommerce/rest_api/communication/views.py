from rest_framework import viewsets

from ecommerce.apps.communication.models import (
    CommunicationEventType,
    Email,
    Notification,
)

from .serializers import (
    CommunicationEventTypeSerializer,
    EmailSerializer,
    NotificationSerializer,
)


class CommunicationEventTypeViewSet(viewsets.ModelViewSet):
    queryset = CommunicationEventType.objects.all()
    serializer_class = CommunicationEventTypeSerializer


class EmailViewSet(viewsets.ModelViewSet):
    queryset = Email.objects.all()
    serializer_class = EmailSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
