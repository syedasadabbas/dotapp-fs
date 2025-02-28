from datetime import datetime, timedelta
import random
from django.contrib import messages
from django.utils.timezone import now
from django.shortcuts import redirect, render
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.utils.dateparse import parse_duration
from django.core.mail import send_mail

from editor.models import OTP



def landing_page(request):
    return render(request, 'dot_app/index.html')

def google_login_callback(request):
    user = request.user
    if user.is_authenticated:
        # ✅ Bypass OTP for staff or admin users
        if user.is_staff or user.is_superuser:
            return redirect("dashboard")

        otp_instance, created = OTP.objects.get_or_create(user=user)

        if otp_instance.otp_confirmed:  # ✅ User has already completed 2FA
            return redirect("dashboard")  # Skip OTP verification

        # Generate a new OTP since user has not verified before
        otp = generate_otp()
        otp_instance.otp = otp
        otp_instance.save()
        send_otp_email(user, otp)

        return redirect("verify_otp")  # Redirect to OTP verification page

    return redirect("account_login")


def generate_otp():
    """Generate a 6-digit OTP."""
    return str(random.randint(100000, 999999))


def send_otp_email(email, otp):
    """Send OTP to user's email."""
    send_mail(
        "Your OTP Code",
        f"Your OTP code is {otp}. It will expire in 5 minutes.",
        "noreply@yourdomain.com",
        [email],
        fail_silently=False,
    )


def start_otp_verification(user, request):
    """
    Handles OTP initiation for a user.
    - Bypass OTP for staff and admin users.
    - Generates a new OTP if needed.
    - Sends OTP via email.
    - Stores the user ID in session to track verification.
    """
    if user.is_staff or user.is_superuser:
        return True  # ✅ Bypass OTP for staff/admin users

    otp_instance, created = OTP.objects.get_or_create(user=user)

    if otp_instance.otp_confirmed:  # ✅ User already verified
        return True  # No need to generate a new OTP

    # Generate and send OTP
    otp = generate_otp()
    otp_instance.otp = otp
    otp_instance.otp_confirmed = False  # Mark as unverified
    otp_instance.save()
    send_otp_email(user, otp)

    # Store user ID in session
    request.session["pending_otp_user"] = user.id
    return False  # OTP needs to be verified

def verify_otp(request):
    user_data = request.session.get("pending_user_data")
    stored_otp = request.session.get("pending_otp")
    otp_expires_at = request.session.get("otp_expires_at")

    if not user_data or not stored_otp:
        messages.error(request, "Session expired. Please register again.")
        return redirect("learning:register")

    if request.method == "POST":
        if "resend_otp" in request.POST:
            new_otp = generate_otp()
            request.session["pending_otp"] = new_otp
            request.session["otp_expires_at"] = (now() + timedelta(minutes=10)).isoformat()

            send_otp_email(user_data["email"], new_otp)  # Send new OTP
            messages.success(request, "A new OTP has been sent to your email.")
            return redirect("verify_otp")

        otp_input = request.POST.get("otp")

        # ✅ Convert `otp_expires_at` to datetime before comparison
        otp_expiry_time = datetime.fromisoformat(otp_expires_at)

        # ✅ Check OTP validity
        if otp_input != stored_otp:
            messages.error(request, "Invalid OTP. Please try again.")
            return render(request, "verify_otp.html")

        if now() > otp_expiry_time:
            messages.error(request, "OTP expired. Please request a new one.")
            return redirect("verify_otp")

        # ✅ Create and save the user now (only after OTP verification)
        user = User.objects.create_user(
            username=user_data["username"],
            email=user_data["email"],
            password=user_data["password"],
        )

        # ✅ Clear session data after successful verification
        del request.session["pending_user_data"]
        del request.session["pending_otp"]
        del request.session["otp_expires_at"]

        # ✅ Log in user
        login(request, user)
        messages.success(request, "Your account has been created successfully!")
        return redirect("learning:dashboard")

    return render(request, "verify_otp.html")