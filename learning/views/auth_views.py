from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from ..forms import CustomUserCreationForm
from django.contrib.auth import logout

def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already taken. Please choose a different one.")
            else:
                user = form.save()  # Save the user to the database
                logout(request)  # Ensure the user is logged out immediately
                messages.success(request, "Account created successfully! Please log in to continue.")
                return redirect("learning:login")  # Redirect to login page

    else:
        form = CustomUserCreationForm()

    return render(request, "learning/register.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect(reverse('learning:login'))  # Ensure 'login' exists in urls.py