from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.utils.timezone import now
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from dot_app.views import generate_otp, send_otp_email, start_otp_verification
from ..forms import CustomUserCreationForm
from django.contrib.auth import logout

def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password1"]
            is_staff = form.cleaned_data.get("is_staff", False)  # Check if registering as staff/admin

            # ✅ Check if username already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already taken. Please choose a different one.")
                return render(request, "learning/register.html", {"form": form})

            # ✅ Allow superusers & staff to register directly
            if is_staff:
                user = User.objects.create_superuser(username=username, email=email, password=password)
                login(request, user)
                messages.success(request, "Admin account created successfully! You are now logged in.")
                return redirect("learning:dashboard")

            # ✅ Store user data temporarily in session instead of saving in DB
            request.session["pending_user_data"] = {
                "username": username,
                "email": email,
                "password": password,
            }

            # ✅ Generate OTP and send it to user
            new_otp = generate_otp()
            request.session["pending_otp"] = new_otp  
            request.session["otp_expires_at"] = (now() + timedelta(minutes=10)).isoformat()

            send_otp_email(email, new_otp)  # Send OTP

            messages.success(request, "An OTP has been sent to your email. Please verify to complete registration.")
            return redirect("verify_otp")  # Redirect to OTP verification page

    else:
        form = CustomUserCreationForm()

    return render(request, "learning/register.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect(reverse('learning:login'))  # Ensure 'login' exists in urls.py