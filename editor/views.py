from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, authenticate, get_user_model, logout
from django.contrib import messages
from django.utils.timezone import now
from dot_app.views import generate_otp, send_otp_email, start_otp_verification
from .models import Track, Dot, SubDot, Topic, SubscriptionPlan, PaymentMethod, Subscription, Earnings
from django import forms
from django.core.files.storage import FileSystemStorage
from django.core.exceptions import ValidationError
from .forms import TrackForm, DotForm, SubDotForm, TopicForm, ContentForm
import logging
import json
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.decorators import login_required


@login_required
def toggle_subscription(request, dot_id):
    # Get the Dot by ID or return 404 if not found
    dot = get_object_or_404(Dot, id=dot_id)
    editor = request.user  # Get the logged-in Editor

    # Check if the Editor is already subscribed
    if dot in editor.subscribed_dots.all():
        # If subscribed, remove subscription
        editor.subscribed_dots.remove(dot)
        messages.success(request, f"You have unsubscribed from {dot.title}.")
    else:
        # If not subscribed, add subscription
        editor.subscribed_dots.add(dot)
        messages.success(request, f"You have subscribed to {dot.title}.")

    # Redirect back to the Dots page
    return redirect('view_Dots', track_id=dot.track.id)

# Configure logging
logger = logging.getLogger(__name__)

# Editor Dashboard
@login_required(login_url='editor_login')
def editor_dashboard(request):
    if request.method == 'POST':
        form = TrackForm(request.POST)
        if form.is_valid():
            #track.created_by = request.user
            track = form.save()
            return redirect('editor_dashboard')
    else:
        form = TrackForm()
    
    #tracks = Track.objects.filter(created_by=request.user)
    tracks = Track.objects.all()
    return render(request, 'editor/dashboard.html', {'tracks': tracks, 'form': form})

# View Dots

def editor_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("editor_dashboard")  # Redirect after login
    return render(request, "editor/login.html")  # Render login template

def view_Dots(request, track_id):
    track = Track.objects.get(id=track_id)
    
    if request.method == 'POST':
        form = DotForm(request.POST)
        if form.is_valid():
            # Create editor's dot
            dot = form.save(commit=False)
            dot.track = track
            dot.created_by = request.user
            dot.save()
            return redirect('view_Dots', track_id=track_id)
    else:
        form = DotForm()
    
    #dots = Dot.objects.filter(track=track, created_by=request.user)
    dots = Dot.objects.filter(track=track)
    return render(request, 'editor/Dots.html', {'track': track, 'Dots': dots, 'form': form})

# View Subdots

def view_subdots(request, Dot_id):
    dot_instance = Dot.objects.get(id=Dot_id)
    #subdots = SubDot.objects.filter(dot=dot_instance, created_by=request.user)
    subdots = SubDot.objects.filter(dot=dot_instance)  
    return render(request, 'editor/subdots.html', {'Dot': dot_instance, 'subdots': subdots})

# View Topics

def view_topics(request, subdot_id):
    subdot = SubDot.objects.get(id=subdot_id)
    #topics = Topic.objects.filter(subdot=subdot, created_by=request.user)
    topics = Topic.objects.filter(subdot=subdot)
    return render(request, 'editor/topics.html', {'subdot': subdot, 'topics': topics})

# View Topic Details

def view_topic(request, topic_id):
    topic = Topic.objects.get(id=topic_id)
    context = {
        'topic': topic,
        'timestamps': json.dumps(topic.timestamps) if topic.timestamps else '[]'
    }
    return render(request, 'editor/topic_detail.html', context)

# Subscription View
def subscribe_editor(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        User = get_user_model()

        if User.objects.filter(username=username).exists():
            messages.error(request, "You are already registered. Please log in.")
            return render(request, "editor/subscribe.html")

        if request.user.is_staff or request.user.is_superuser:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            messages.success(request, "Registration successful! You are now logged in.")
            return redirect("subscription_view")

        request.session["pending_user_data"] = {
            "username": username,
            "email": email,
            "password": password,
        }

        new_otp = generate_otp()
        request.session["pending_otp"] = new_otp
        request.session["otp_expires_at"] = (now() + timedelta(minutes=10)).isoformat()

        send_otp_email(email, new_otp)

        messages.success(request, "An OTP has been sent to your email. Please verify to complete registration.")
        return redirect("verify_otp")

    return render(request, "editor/subscribe.html")

# Login View

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('editor_dashboard')  # Redirect to Dashboard instead of content addition
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'editor/login.html')

@login_required
def content_addition(request):
    if request.method == 'POST':
        # Capture Form Data
        title = request.POST.get('title')
        content = request.POST.get('content')
        code = request.POST.get('code')
        dot_id = request.POST.get('dot')
        subdot_id = request.POST.get('subdot')

        # Get Dot and SubDot
        dot = Dot.objects.get(id=dot_id) if dot_id else None
        subdot = SubDot.objects.get(id=subdot_id) if subdot_id else None
        
        # Handle Image and Audio Uploads
        image = request.FILES.get('image')
        audio = request.FILES.get('audio')

        # Create New Topic
        new_topic = Topic(
            title=title,
            content=content,
            code=code,
            subdot=subdot,
            created_by=request.user
        )

        # Add Image and Audio if uploaded
        if image:
            new_topic.image = image
        if audio:
            new_topic.audio = audio

        new_topic.save()
        messages.success(request, 'Content added successfully!')
        return redirect('content_addition')
    
    # GET Request: Display Form
    dots = Dot.objects.all()
    subdots = SubDot.objects.all()
    return render(request, 'editor/content_addition.html', {'Dots': dots, 'subdots': subdots})

# Registration View

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        User = get_user_model()

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists. Please choose another.')
            return render(request, 'editor/register.html')

        User.objects.create_user(username=username, email=email, password=password)
        messages.success(request, 'Registration successful! You can now subscribe.')
        return redirect('subscription_view')
    return render(request, 'editor/register.html')

# Content Upload Form

class ContentForm(forms.Form):
    title = forms.CharField(max_length=255)
    content = forms.CharField(widget=forms.Textarea)
    code = forms.CharField(widget=forms.Textarea)
    image = forms.ImageField(required=False)
    audio = forms.FileField(required=False)

# Content Upload View

def upload_content(request):
    if request.method == 'POST':
        form = ContentForm(request.POST, request.FILES)
        if form.is_valid():
            title = form.cleaned_data['title']
            content = form.cleaned_data['content']
            code = form.cleaned_data['code']
            image = form.cleaned_data['image']
            audio = form.cleaned_data['audio']
            fs = FileSystemStorage()
            if image:
                try:
                    fs.save(image.name, image)
                except ValidationError:
                    form.add_error('image', 'Invalid image file.')
            if audio:
                try:
                    fs.save(audio.name, audio)
                except ValidationError:
                    form.add_error('audio', 'Invalid audio file.')
            new_topic = Topic(title=title, content=content, code=code)
            new_topic.save()
            return redirect('editor_dashboard')
    else:
        form = ContentForm()
    return render(request, 'editor/upload_content.html', {'form': form})

# Add Topic View
def add_topic(request, subdot_id):
    subdot = SubDot.objects.get(id=subdot_id)
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            content = request.POST.get('content')
            code = request.POST.get('code')
            timestamps = request.POST.get('timestamps')  # Get timestamps JSON string

            # Create new topic
            topic = Topic(
                subdot=subdot,
                title=title,
                content=content,
                code=code if code else None,
                timestamps=json.loads(timestamps) if timestamps else None,  # Parse JSON timestamps
                created_by=request.user
            )

            # Handle image upload
            if 'image' in request.FILES:
                image = request.FILES['image']
                if image:
                    topic.image = image

            # Handle audio upload
            if 'audio' in request.FILES:
                audio = request.FILES['audio']
                if audio:
                    topic.audio = audio

            topic.save()
            messages.success(request, 'Topic added successfully!')
            return redirect('view_topics', subdot_id=subdot_id)

        except json.JSONDecodeError:
            messages.error(request, 'Invalid timestamps format')
            return render(request, 'editor/add_topic.html', {'subdot': subdot})
        except Exception as e:
            messages.error(request, f'Error adding topic: {str(e)}')
            return render(request, 'editor/add_topic.html', {'subdot': subdot})

    return render(request, 'editor/add_topic.html', {'subdot': subdot})

# Add Subdot View

def add_subdot(request, Dot_id):
    dot_instance = Dot.objects.get(id=Dot_id)
    if request.method == 'POST':
        title = request.POST.get('title')
        subdot = SubDot(dot=dot_instance, title=title, created_by=request.user)
        subdot.save()
        messages.success(request, 'Subdot added successfully!')
        return redirect('view_subdots', Dot_id=dot_instance.id)
    return render(request, 'editor/add_subdot.html', {'Dot': dot_instance})
# View for displaying subscription options

def subscription_view(request):
    plans = SubscriptionPlan.objects.all()
    payment_methods = PaymentMethod.objects.all()
    return render(request, 'editor/subscription.html', {'plans': plans, 'payment_methods': payment_methods, 'plan_id': plans[0].id if plans else None})

# View for processing payments

def payment_view(request):
    if request.method == 'POST':
        payment_method_name = request.POST.get('payment_method')
        plan_id = request.POST.get('plan_id')
        logger.debug(f'Selected plan ID: {plan_id}')

        registration_successful = True  # Placeholder for actual payment logic

        if registration_successful:
            try:
                payment_method = PaymentMethod.objects.get(method_name=payment_method_name)
            except PaymentMethod.DoesNotExist:
                messages.error(request, 'Selected payment method does not exist.')
                return redirect('payment_view')

            subscription_plan = SubscriptionPlan.objects.get(id=plan_id)
            end_date = timezone.now() + timedelta(days=30)
            Subscription.objects.create(editor=request.user, subscription_plan=subscription_plan, payment_method=payment_method, end_date=end_date)
            messages.success(request, 'Payment successful! You are now registered.')
            return redirect('editor_dashboard')
    return render(request, 'editor/payment.html')

# View for displaying earnings

def earnings_view(request):
    #earnings = Earnings.objects.filter(editor=request.user)
    earnings = Earnings.objects.all()
    return render(request, 'editor/earnings.html', {'earnings': earnings})

def logout_view(request):
    logout(request)
    return redirect('login_view')