from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.login, name="login"),
    path("login", views.login, name="login"),
    path("register", views.register, name="register"),
    path("logout", views.logout, name="logout"),
    path("homepage", views.homepage, name="homepage"),
    path("generatenotes", views.generatenotes, name="generatenotes"),
    path("process_audio", views.process_audio, name="process_audio"),
    path("chat", views.chat, name="chat"),
]
