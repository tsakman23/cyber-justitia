"""
URL configuration for justitia project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from justitia.feeds import LatestPostsFeed

urlpatterns = [
    path("admin/", admin.site.urls),
    path("forum/", include("forum.urls")),
    path("", include("users.urls")),
    path("chatbot/", include("chatbot.urls")),
    path("hitcount/", include("hitcount.urls", namespace="hitcount")),
    path("latest/feed/", LatestPostsFeed()),
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}),
]

# Custom error handlers
handler400 = "users.views.handler400"
handler403 = "users.views.handler403"
handler404 = "users.views.handler404"
handler500 = "users.views.handler500"
handler503 = "users.views.handler503"
