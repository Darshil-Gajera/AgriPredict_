from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
]

urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),

    # ✅ Auth (allauth)
    path("accounts/", include("allauth.urls")),

    # ✅ Your custom user app (NO conflict now)
    path("user/", include("accounts.urls")),

    # Other apps
    path("predict/", include("predict.urls")),
    path("colleges/", include("colleges.urls")),
    path("notifications/", include("notifications.urls")),
    path("scholarships/", include("scholarships.urls")),
    path("", include("core.urls")),

    prefix_default_language=False,
)

# ✅ API routes (CLEAN SEPARATION)
urlpatterns += [
    path("api/predict/", include("predict.api_urls")),
    path("api/colleges/", include("colleges.api_urls")),
    path("api/chat/", include("core.chat_urls")),

    # 🔥 FIXED: use separate API urls file (NOT accounts.urls)
    path("api/accounts/", include("accounts.api_urls")),
]

# Media files (dev)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)