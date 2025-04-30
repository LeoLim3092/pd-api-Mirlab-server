from django.urls import include, path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from api.admin import admin_site  # ✅ use custom admin site

urlpatterns = [
    path('admin/', admin_site.urls),  # ✅ custom admin
    path('rest/', include('rest_framework.urls')),
    path('api/', include('api.urls')),
    path('api/token', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify', TokenVerifyView.as_view(), name='token_verify'),
]