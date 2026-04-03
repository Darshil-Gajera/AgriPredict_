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
    path("accounts/", include("allauth.urls")),
    path("accounts/", include("accounts.urls")),
    path("predict/", include("predict.urls")),
    path("colleges/", include("colleges.urls")),
    path("notifications/", include("notifications.urls")),
    path("scholarships/", include("scholarships.urls")),
    path("", include("core.urls")),
    prefix_default_language=False,
)

# DRF API endpoints (not i18n prefixed)
urlpatterns += [
    path("api/predict/", include("predict.api_urls")),
    path("api/colleges/", include("colleges.api_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
