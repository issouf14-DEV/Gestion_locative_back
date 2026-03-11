from django.urls import path
from .views import DashboardStatsView, LocataireDashboardView

urlpatterns = [
    path('admin/', DashboardStatsView.as_view(), name='dashboard-admin'),
    path('locataire/', LocataireDashboardView.as_view(), name='dashboard-locataire'),
]
