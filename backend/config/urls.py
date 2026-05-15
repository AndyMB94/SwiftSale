"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI

from apps.authentication.api import router as auth_router
from apps.users.api import router as users_router
from apps.products.api import router as products_router
from core.health import router as health_router

api = NinjaAPI(
    title='SwiftSale API',
    version='1.0.0',
    description='Modern Retail Management Platform',
)

api.add_router('/auth', auth_router)
api.add_router('/users', users_router)
api.add_router('/products', products_router)
api.add_router('/health', health_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', api.urls),
]
