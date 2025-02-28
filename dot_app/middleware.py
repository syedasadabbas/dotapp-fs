from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from django.urls import reverse

from editor.models import OTP


class OTPMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            # ✅ Allow access to `verify_otp` and `google_login_callback` without further OTP checks
            allowed_paths = [reverse("verify_otp"), reverse("google_login_callback")]
            if request.path in allowed_paths:
                return None  # Ensure OTP check is skipped

            otp_instance = OTP.objects.filter(user=request.user).first()

            if otp_instance and not otp_instance.otp_confirmed:
                return redirect("verify_otp")  # ✅ Force 2FA if not confirmed

        return None
