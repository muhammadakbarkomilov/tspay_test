import drf_yasg
import transactions
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import RedirectView
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework_simplejwt.views import TokenRefreshView
from accounts.views import RegisterView, MyTokenObtainPairView, UserListView, UserDetailView, verify_sms_code
from uuid import UUID

from blog import views
from blog.views import blog_list, blog_detail, increment_click, increment_view
from core import settings
from core.settings import DEBUG
from payment.views import ClickWebhookAPIView
from terms.views import policy_view
from transactions.views import *

from accounts.views import register_view, login_view, logout_view, dashboard
from notification.views import *


from django.contrib import admin

schema_view = get_schema_view(
   openapi.Info(
      title="TsPay API",
      default_version='v1',
      description="To‘lov tizimi uchun Swagger hujjatlari",
      terms_of_service="https://tspay.uz/terms/",
      contact=openapi.Contact(email="support@tspay.uz"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)


urlpatterns = [
    # Admin and Home
    path('admin/', admin.site.urls),
    path('', home, name='home'),

    # Auth (API)
    path('api/auth/register/', RegisterView.as_view(), name='register'),
    path('api/auth/login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Auth (Web)
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    # User/Profile
    path('dashboard/', dashboard, name='dashboard'),
    path('profile/', profile_view, name='profile'),
    path('profile/change-password/', change_password, name='change_password'),
    path('profile/disconnect-telegram/', disconnect_telegram, name='disconnect_telegram'),

    # Shops
    path('shops/', shops, name='shops'),
    path('shops/add/', add_shop, name='add_shop'),
    path('shops/<uuid:shop_id>/edit/', edit_shop, name='edit_shop'),
    path('shops/<uuid:shop_id>/delete/', delete_shop, name='delete_shop'),
    path('api/shops/create/', ShopCreateView.as_view(), name='shop-create'),
    path('api/shops/<uuid:pk>/', ShopDetailView.as_view(), name='shop-detail'),
    path('api/dash/shops/', ShopListView.as_view(), name='shop-list'),
    path('api/shops/access-token/', ShopAccessTokenView.as_view(), name='shops-access-token'),

    # Transactions
    path('transactions/', transactions, name='transactions'),
    path('api/transactions/create/', TransactionCreateView.as_view(), name='transaction-create'),
    path('api/transactions/<int:pk>/', TransactionDetailView.as_view(), name='transaction-detail'),
    path('transaction/<uuid:uuid>/cancel', cancel_transaction, name='cancel_transaction'),
    path('api/chart-data/', chart_data, name='transactions_chart_api'),
    path('pay/<uuid:cheque_id>/', payment_page, name='payment_page'),
    path('checkout/<uuid:uuid>/', checkout_detail, name='checkout_detail'),

    # Notifications
    path('notifications/list/', notification_list, name='notification-list'),
    path('notifications/mark_read/<int:notification_id>/', mark_as_read, name='mark-as-read'),
    path('notifications/mark_all_read/', mark_all_read, name='mark-all-read'),

    # Blog
    path('blog/', blog_list, name='blog_list'),
    path('blog/<slug:slug>/', blog_detail, name='blog_detail'),
    path('blog/post/<int:post_id>/view/', increment_view, name='increment_view'),
    path('blog/post/<int:post_id>/click/', increment_click, name='increment_click'),

    # CKEditor
    path('ckeditor/', include('ckeditor_uploader.urls')),

    # Legal
    path('terms/', policy_view, {'policy_type': 'terms'}, name='terms'),
    path('privacy/', policy_view, {'policy_type': 'privacy'}, name='privacy'),

    # Telegram Support
    path('support/', RedirectView.as_view(url='https://t.me/tspaysupport'), name='support'),

    # Misc
    path('verify-code/', verify_sms_code, name='verify_sms_code'),

    # Swagger Docs
    re_path(r'^docs(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('docs/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    path("payment/click/update/", ClickWebhookAPIView.as_view()),
]


# Static and media files in debug mode
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)