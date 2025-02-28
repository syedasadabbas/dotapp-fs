from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from ..models import SubscriptionPlan, UserSubscription, FreeTrialUsage, LearnerProfile, Progress
from editor.models import Dot, SubDot

import stripe
from django.conf import settings
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView


def check_subscription_access(user, subdot):
    try:
        subscription = UserSubscription.objects.get(user=user, is_active=True)
        if subscription.is_valid():
            return True, None
    except UserSubscription.DoesNotExist:
        pass

    try:
        trial_usage, created = FreeTrialUsage.objects.get_or_create(
            user=user,
            dot=subdot.dot
        )
        if trial_usage.has_free_trial_access():
            if subdot not in trial_usage.subdots_accessed.all():
                trial_usage.subdots_accessed.add(subdot)
            return True, None
        return False, "You have reached your free trial limit for this Dot. Please subscribe to continue learning."
    except Exception as e:
        return False, str(e)

@login_required
def subscription_view(request):
    plans = SubscriptionPlan.objects.filter(is_active=True)
    
    try:
        current_subscription = UserSubscription.objects.get(
            user=request.user,
            is_active=True
        )
    except UserSubscription.DoesNotExist:
        current_subscription = None

    context = {
        'plans': plans,
        'current_subscription': current_subscription
    }
    return render(request, 'learning/subscription_plans.html', context)

@login_required
def payment_view(request):
    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
            end_date = timezone.now() + timezone.timedelta(days=plan.duration_days)
            
            subscription, created = UserSubscription.objects.update_or_create(
                user=request.user,
                defaults={
                    'plan': plan,
                    'end_date': end_date,
                    'is_active': True,
                    'payment_status': 'completed'
                }
            )
            
            # Grant access to all tracks, dots, subdots, and topics
            user_profile = LearnerProfile.objects.get(user=request.user)
            dots = Dot.objects.all()
            subdots = SubDot.objects.all()
            
            # Grant access to all subdots for the user
            for subdot in subdots:
                Progress.objects.update_or_create(
                    learner=user_profile,
                    subdot=subdot,
                    defaults={'completed': False}
                )
            
            messages.success(request, f"Successfully subscribed to {plan.name} plan!")
            return redirect('dashboard/')
            
        except SubscriptionPlan.DoesNotExist:
            messages.error(request, "Invalid subscription plan selected.")
            return redirect('subscription_view')
    
    plan_id = request.GET.get('plan_id')
    try:
        plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
    except SubscriptionPlan.DoesNotExist:
        messages.error(request, "Invalid subscription plan selected.")
        return redirect('subscription_view')
        
    context = {
        'plan': plan
    }
    return render(request, 'learning/payment.html', context)


stripe.api_key = settings.STRIPE_SECRET_KEY

class CreateStripeCheckoutSessionView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "You need to be logged in to subscribe.")
            return redirect("login")

        plan_id = request.POST.get("plan_id")
        plan = SubscriptionPlan.objects.filter(id=plan_id, is_active=True).first()

        if not plan:
            messages.error(request, "Invalid subscription plan.")
            return redirect("error_page")

        # Prevent re-purchase of the same plan
        subscription = UserSubscription.objects.filter(user=request.user, is_active=True).first()
        if subscription and subscription.plan == plan:
            messages.error(request, "You are already subscribed to this plan.")
            return redirect("learning:dashboard")

        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "unit_amount": int(plan.price * 100),
                            "product_data": {
                                "name": plan.name,
                                "description": plan.description,
                            },
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url=settings.PAYMENT_SUCCESS_URL,
                cancel_url=settings.PAYMENT_CANCEL_URL,
            )

            # Save Subscription with `pending` status before payment
            UserSubscription.objects.update_or_create(
                user=request.user,
                defaults={
                    "plan": plan,
                    "start_date": timezone.now(),
                    "end_date": timezone.now() + timedelta(days=plan.duration_days),
                    "is_active": True,
                    "payment_status": "pending",  # Will update on success
                },
            )

            return redirect(checkout_session.url)

        except Exception as e:
            print(f"Stripe error: {e}")
            return redirect("error_page")

class SuccessView(TemplateView):
    template_name = "success.html"

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")

        # Find user's subscription and mark it as completed
        subscription = UserSubscription.objects.filter(user=request.user, payment_status="pending").first()
        if subscription:
            subscription.payment_status = "completed"
            subscription.is_active = True
            subscription.save()

        return super().get(request, *args, **kwargs)

class CancelView(TemplateView):
    template_name = "cancel.html"