"""
URL configuration for software_cup project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from myapp.test_view import index
from django.conf import settings  
from django.conf.urls.static import static  
from django.urls import path, include 
from myapp.views import *
urlpatterns = [
    path('admin/', admin.site.urls),
    path('gengrate_all/', index),
    path('sta/report', static_report),
    path('sta/basicinfo', static_basicinfo),
    path('sta/permissioninfo', static_permissioninfo),
    path('sta/urlinfo', static_urlinfo),
    path('sta/picinfo', static_picinfo),
    path('sta/apk', static_apk),
    path('sta/pics', static_pics),
    path('sta/urls', static_urls),
    path('list/black', list_black),
    path('list/white', list_white),
    path('task/doing', task_doing),
    path('task/apk', task_apk),
    path('task/link', task_link),
    path('task/done', task_done),
    path('task/del', task_del),
    path('chat/chat', chat_chat),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

