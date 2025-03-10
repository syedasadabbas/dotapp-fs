from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from ..models import SubscriptionPlan, UserSubscription, FreeTrialUsage, LearnerProfile, Progress
from editor.models import Dot, SubDot


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
            return redirect('dashboard')
            
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
