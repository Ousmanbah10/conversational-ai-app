from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Chat
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile


class ChatAppTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.chat_url = reverse("chat")
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")
        self.register_url = reverse("register")
        self.homepage_url = reverse("homepage")
        self.generatenotes_url = reverse("generatenotes")
        self.process_audio_url = reverse("process_audio")

    def test_login_view(self):
        response = self.client.post(
            self.login_url, {"username": "testuser", "password": "testpassword"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.homepage_url)

    def test_login_view_invalid(self):
        response = self.client.post(
            self.login_url, {"username": "wronguser", "password": "wrongpassword"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password")

    def test_chat_view_get(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(self.chat_url)
        self.assertEqual(response.status_code, 200)

    def test_chat_view_post(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.post(self.chat_url, {"message": "Hello, AI!"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.json())

    def test_register_view_get(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)

    def test_register_view_post(self):
        response = self.client.post(
            self.register_url,
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password1": "password123",
                "password2": "password123",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.homepage_url)

    def test_register_view_password_mismatch(self):
        response = self.client.post(
            self.register_url,
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password1": "password123",
                "password2": "password456",
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_logout_view(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.login_url)

    def test_generatenotes_view(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(self.generatenotes_url)
        self.assertEqual(response.status_code, 200)

    def test_homepage_view(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(self.homepage_url)
        self.assertEqual(response.status_code, 200)
