import random
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


def send_otp_email(user, otp):
    """Send OTP to user's email."""
    send_mail(
        "Your OTP Code",
        f"Your OTP code is {otp}. It will expire in 5 minutes.",
        "noreply@yourdomain.com",
        [user.email],
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
    """
    Verify OTP input by the user.
    If valid, mark OTP as confirmed and log in the user.
    """
    user_id = request.session.get("pending_otp_user")
    
    if not user_id:
        return redirect("login")  # Redirect if no user is in session

    user = User.objects.filter(id=user_id).first()
    if not user:
        return redirect("login")

    # ✅ Bypass OTP for staff or admin users
    if user.is_staff or user.is_superuser:
        login(request, user)
        del request.session["pending_otp_user"]  # Clean up session
        return redirect("learning:dashboard")

    if request.method == "POST":
        otp_input = request.POST.get("otp")
        otp_instance = OTP.objects.filter(user=user).first()

        if otp_instance and otp_instance.otp == otp_input:
            otp_instance.otp_confirmed = True  # ✅ Mark 2FA as completed
            otp_instance.save()

            # Log in the user since OTP is confirmed
            login(request, user)
            del request.session["pending_otp_user"]  # Clean up session
            
            return redirect("learning:dashboard")  # Redirect to dashboard

        return render(request, "verify_otp.html", {"error": "Invalid OTP or expired."})

    return render(request, "verify_otp.html")
