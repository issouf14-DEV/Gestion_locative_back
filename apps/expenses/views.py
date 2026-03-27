from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Depense
from .serializers import DepenseSerializer
from apps.core.permissions import IsAdminUser
from apps.core.mixins import CustomResponseMixin


class DepenseViewSet(CustomResponseMixin, viewsets.ModelViewSet):
    queryset = Depense.objects.all()
    serializer_class = DepenseSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
