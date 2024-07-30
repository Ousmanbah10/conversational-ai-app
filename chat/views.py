from openai import OpenAI
from django.utils.safestring import mark_safe
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from django.contrib import auth
from django.contrib.auth.models import User
from .models import Chat
from django.utils import timezone
import re
import tempfile
from datetime import datetime
from django.http import JsonResponse
import io
from django.conf import settings

from dotenv import load_dotenv
import openai

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def transcribe_audio(audio_file):
    """Transcribes the given audio file using OpenAI's whisper-1 model."""
    transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)

    return transcript.text


def ask_openai(transcribed_text):
    """Sends the transcribed text to OpenAI and receives a structured HTML response."""
    prompt = f"""
    Analyze the following transcribed audio content and provide a response in HTML format:

    "{transcribed_text}"

    Structure your HTML response as follows:

    <div class="transcription">
        <h2>Transcription</h2>
        <p>[Insert the original transcription here]</p>
    </div>

    <div class="analysis-content">
        <h2>Analysis</h2>
        <h3>Summary</h3>
        [Summary content]
        <h3>Key Points</h3>
        [List of key points]
        <h3>Critical Analysis</h3>
        [Critical analysis content]
        <h3>Practical Applications</h3>
        [Practical applications content]
        <h3>Thought-Provoking Questions</h3>
        [List of questions]
    </div>

    Use appropriate HTML tags: <p> for paragraphs, <ul> and <li> for unordered lists, <ol> and <li> for ordered lists.
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that provides analysis in valid HTML format.",
            },
            {"role": "user", "content": prompt},
        ],
    )

    return response.choices[0].message.content.strip()


def ask_openai_chat(message):
    prompt = f"""
    Provide a response to the following message in HTML format:

    User message: "{message}"

    Structure your HTML response as follows:

    <div class="ai-response">
        <h3>AI Response</h3>
        [Your response here, using appropriate HTML tags]
    </div>

    Use appropriate HTML tags: <p> for paragraphs, <ul> and <li> for unordered lists, <ol> and <li> for ordered lists, <strong> for emphasis, etc.
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that provides responses in valid HTML format.",
            },
            {"role": "user", "content": prompt},
        ],
    )

    answer = response.choices[0].message.content.strip()
    return answer


def login(request):
    """Handles user login. Authenticates and logs in the user if credentials are valid."""
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = auth.authenticate(request, username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect("homepage")
        else:
            error_message = "Invalid username or password"
            return render(request, "login.html", {"error_message": error_message})
    else:
        return render(request, "login.html")


@login_required
def chat(request):
    """Renders the chat page and handles user messages."""
    chats = Chat.objects.filter(user=request.user)

    if request.method == "POST":
        message = request.POST.get("message")
        response = ask_openai_chat(message)

        chat = Chat(
            user=request.user, message=message, response=response, time=timezone.now()
        )
        chat.save()
        return JsonResponse({"message": message, "response": mark_safe(response)})
    return render(request, "chat.html", {"chats": chats})


def register(request):
    """Handles user registration. Creates a new user account if the provided details are valid."""
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password1 = request.POST["password1"]
        password2 = request.POST["password2"]
        if password1 == password2:
            try:
                user = User.objects.create_user(username, email, password1)
                user.save()
                auth.login(request, user)
                return redirect("homepage")
            except:
                error_message = "Error creating your account"
                return render(
                    request, "regsiter.html", {"error_message": error_message}
                )
        else:
            error_message = "Password dont match."
            return render(request, "register.html", {"error_message": error_message})

    return render(request, "register.html")


def logout(request):
    """Logs out the current user."""
    auth.logout(request)

    return redirect("login")


@login_required
def generatenotes(request):
    """Renders the page for generating notes."""
    return render(request, "generatenotes.html")


@login_required
def homepage(request):
    """Renders the homepage."""
    return render(request, "homepage.html")


SUPPORTED_FORMATS = [
    "flac",
    "m4a",
    "mp3",
    "mp4",
    "mpeg",
    "mpga",
    "oga",
    "ogg",
    "wav",
    "webm",
]


def process_audio(request):
    """Processes the uploaded audio file, transcribes it, and returns the transcription in HTML format."""
    if request.method == "POST":
        audio_file = request.FILES.get("audioFile")
        if audio_file:
            with tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False
            ) as temp_audio_file:
                for chunk in audio_file.chunks():
                    temp_audio_file.write(chunk)

            try:
                with open(temp_audio_file.name, "rb") as audio_data:
                    transcribed_audio = transcribe_audio(audio_data)

                html_content = ask_openai(transcribed_audio)

                return JsonResponse({"success": True, "html_content": html_content})
            finally:
                os.unlink(temp_audio_file.name)
        else:
            return JsonResponse({"success": False, "error": "No file received"})
    return JsonResponse({"success": False, "error": "Invalid request method"})
