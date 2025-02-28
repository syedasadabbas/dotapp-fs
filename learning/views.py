from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import login, authenticate, update_session_auth_hash, logout
from django.contrib import messages
from django.utils import timezone
from django import forms
from .forms import InstructorQuestionForm
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from learning.models import LearnerProfile, Progress, Note, NewNote, Bookmark, Assessment, AssessmentQuestion, AssessmentResult
from editor.models import Track, Dot, SubDot, Topic

class UserUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)
    username = forms.CharField(required=False)  

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = 'Letters, digits and @/./+/-/_ only.'
        self.fields['email'].help_text = 'Enter a valid email address.'
        
    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('username'):
            cleaned_data['username'] = self.instance.username
        return cleaned_data

class ProfileUpdateForm(forms.ModelForm):
    bio = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False,
        help_text='Tell us about yourself'
    )

    class Meta:
        model = LearnerProfile
        fields = ['bio', 'profile_picture', 'learning_style', 'email_notifications', 
                 'progress_reminders', 'public_profile', 'show_progress']
        help_texts = {
            'profile_picture': 'Upload your profile picture',
            'learning_style': 'Choose your preferred way of learning',
            'email_notifications': 'Receive updates about your courses via email',
            'progress_reminders': 'Get reminders about your learning progress',
            'public_profile': 'Allow other users to see your profile',
            'show_progress': 'Show your learning progress to other users'
        }

class NoteForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'form-control',
            'placeholder': 'Write your note here...',
            'style': 'color: white; background: rgba(17, 34, 64, 0.7); border: 1px solid rgba(100, 255, 218, 0.1);'
        }),
        required=True
    )

    class Meta:
        model = Note
        fields = ['content']

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            #  Check if the username already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already taken. Please choose a different one.')
            else:
                user = form.save()
                login(request, user)  # Log the user in after successful registration
                messages.success(request, 'Account created successfully! Welcome to the learning platform.')
                return redirect('dashboard')
    else:
        form = CustomUserCreationForm()

    return render(request, 'learning/register.html', {'form': form})

@login_required
def dashboard(request):
    learner, created = LearnerProfile.objects.get_or_create(user=request.user)
    tracks = Track.objects.all()

    # Get the learner's progress for each track
    track_progress = {}
    for track in tracks:
        dots = track.dots.all()
        total_subdots = sum(dot.subdots.count() for dot in dots)
        completed_subdots = Progress.objects.filter(
            learner=learner,
            subdot__dot__track=track,
            completed=True
        ).count()
        
        if total_subdots > 0:
            progress_percentage = (completed_subdots / total_subdots) * 100
        else:
            progress_percentage = 0
            
        track_progress[track.id] = {
            'track': track,
            'total': total_subdots,
            'completed': completed_subdots,
            'percentage': round(progress_percentage, 1),
            'is_completed': progress_percentage == 100
        }
    
    # Get recent notes
    recent_notes = Note.objects.filter(learner=learner).order_by('-created_at')[:5]
    
    # Get recently viewed content
    recent_activities = Progress.objects.filter(
        learner=learner
    ).order_by('-last_accessed')[:5]
    
    # Get completed dots
    completed_dots = Progress.objects.filter(
        learner=learner,
        completed=True
    ).select_related('subdot__dot').order_by('-completed_at')[:5]
    
    # Get bookmarked subdots
    bookmarked_subdots = SubDot.objects.filter(bookmark__learner=learner)
    
    user_results = AssessmentResult.objects.filter(
        learner=learner
    ).order_by('-completed_at')

    context = {
        'tracks': tracks,
        'track_progress': track_progress,
        'recent_notes': recent_notes,
        'bookmarked_subdots': bookmarked_subdots,
        'recent_activities': recent_activities,
        'completed_dots': completed_dots,
        'user_results': user_results,
    }
    return render(request, 'learning/dashboard.html', context)

@login_required
def profile(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.learnerprofile)
        
        if 'update_profile' in request.POST:
            if user_form.is_valid() and profile_form.is_valid():
                user = user_form.save(commit=False)
                profile = profile_form.save(commit=False)
                
                if user_form.cleaned_data.get('first_name'):
                    user.first_name = user_form.cleaned_data['first_name']
                if user_form.cleaned_data.get('last_name'):
                    user.last_name = user_form.cleaned_data['last_name']
                if user_form.cleaned_data.get('email'):
                    user.email = user_form.cleaned_data['email']
                user.save()
                
                if profile_form.cleaned_data.get('bio'):
                    profile.bio = profile_form.cleaned_data['bio']
                if profile_form.cleaned_data.get('learning_style'):
                    profile.learning_style = profile_form.cleaned_data['learning_style']
                
                if 'profile_picture' in request.FILES:
                    profile.profile_picture = request.FILES['profile_picture']
                    
                profile.email_notifications = profile_form.cleaned_data.get('email_notifications', profile.email_notifications)
                profile.progress_reminders = profile_form.cleaned_data.get('progress_reminders', profile.progress_reminders)
                profile.public_profile = profile_form.cleaned_data.get('public_profile', profile.public_profile)
                profile.show_progress = profile_form.cleaned_data.get('show_progress', profile.show_progress)
                
                profile.save()
                
                messages.success(request, 'Your profile has been updated successfully!')
                return redirect('profile')
            else:
                for field, errors in user_form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field.title()}: {error}')
                for field, errors in profile_form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field.title()}: {error}')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.learnerprofile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    
    return render(request, 'learning/profile.html', context)

@login_required
def track_list(request):
    tracks = Track.objects.all()
    learner = request.user.learnerprofile
    dot_progress = {}
    
    for track in tracks:
        for dot in track.dots.all():
            dot_progress[dot.id] = calculate_dot_progress(learner, dot)
    
    return render(request, 'learning/track_list.html', {
        'tracks': tracks,
        'dot_progress': dot_progress,
    })

@login_required
def track_detail(request, track_id):
    track = get_object_or_404(Track, id=track_id)
    dots = track.dot_set.all().order_by('order')
    learner = request.user.learnerprofile

    dot_progress = {}
    total_time_spent = timezone.timedelta()

    for dot in dots:
        progress = calculate_dot_progress(learner, dot)
        dot_progress[dot.id] = progress
        if progress and progress.get('time_spent'):
            total_time_spent += progress.time_spent

    total_dots = dots.count()
    completed_dots = sum(1 for p in dot_progress.values() if p and p['percentage'] == 100)
    track_stats = {
        'total_dots': total_dots,
        'completed_dots': completed_dots,
        'completion_percentage': (completed_dots / total_dots * 100) if total_dots > 0 else 0
    }

    context = {
        'track': track,
        'dots': dots,
        'dot_progress': dot_progress,
        'total_time_spent': total_time_spent,
        'track_stats': track_stats,
    }
    return render(request, 'learning/track_detail.html', context)

@login_required
def track(request):
    user_tracks = Track.objects.filter(learner=request.user).order_by('-created_at')
    
    tracks_with_progress = []
    for track in user_tracks:
        dots = track.dots.all()
        total_dots = dots.count()
        completed_dots = dots.filter(completed=True).count()
        progress = (completed_dots / total_dots * 100) if total_dots > 0 else 0
        
        description = track.description if track.description else "No description provided."
        tracks_with_progress.append({
            'track': track,
            'total_dots': total_dots,
            'completed_dots': completed_dots,
            'progress': progress,
            'description': description
        })
    
    return render(request, 'learning/track.html', {
        'tracks_with_progress': tracks_with_progress
    })

def format_timedelta(td):
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"

@login_required
def dot_detail(request, track_id, dot_id):
    track = get_object_or_404(Track, id=track_id)
    dot = get_object_or_404(Dot, track=track, id=dot_id)
    learner = request.user.learnerprofile
    
    subdots = dot.subdots.all().order_by('order')
    
    progress = calculate_dot_progress(learner, dot)
    
    context = {
        'track': track,
        'dot': dot,
        'subdots': subdots,
        'progress': progress,
    }
    
    return render(request, 'learning/dot_detail.html', context)

@login_required
def subdot_detail(request, subdot_id):
    subdot = get_object_or_404(SubDot, id=subdot_id)
    learner = request.user.learnerprofile
    
    progress, created = Progress.objects.get_or_create(learner=learner, subdot=subdot)
    
    # Get next subdot if it exists
    next_subdot = SubDot.objects.filter(
        dot=subdot.dot,
        id__gt=subdot.id
    ).order_by('id').first()
    
    # "Previous" SubDot: same dot, lower id
    previous_subdot = SubDot.objects.filter(
        dot=subdot.dot,
        id__lt=subdot.id
    ).order_by('-id').first()

    # Calculate dot progress
    dot_progress = calculate_dot_progress(learner, subdot.dot)
    
    # Check if all subdots are completed
    if dot_progress == 100:
        # Mark the dot as completed
        dot_progress, created = DotProgress.objects.get_or_create(learner=learner, dot=subdot.dot)
        dot_progress.completed = True
        dot_progress.save()

    notes = Note.objects.filter(
        learner=learner,
        subdot=subdot
    ).order_by('-updated_at')
    
    is_bookmarked = Bookmark.objects.filter(learner=learner, subdot=subdot).exists()
    
    track = subdot.dot.track
    
    topics = subdot.topics.all()

    topic_audio = []
    topic_timestamps = None
    if topics.exists():
        for topic in topics:
            if topic.audio:
                topic_audio = topic.audio.url  # Get the audio file URL
                topic_timestamps = topic.timestamps  # Get timestamps (stored in JSONField)
                break  

    context = {
        'subdot': subdot,
        'track': track,
        'progress': progress,
        'is_bookmarked': is_bookmarked,
        'next_subdot': next_subdot,
        'previous_subdot': previous_subdot,
        'dot_progress': dot_progress,
        'notes': notes,
        'topics': topics,
        'topic_audio': topic_audio,  # Pass the audio URL to the frontend
        'topic_timestamps': topic_timestamps
    }
    
    return render(request, 'learning/subdot_detail.html', context)

@login_required
def add_note(request, subdot_id):
    subdot = get_object_or_404(SubDot, id=subdot_id)
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            print(f"Adding note for user {request.user.username} to subdot {subdot_id}")  # Debug message
            note = form.save(commit=False)
            note.learner = request.user.learnerprofile
            note.subdot = subdot
            note.save()
            print(f"Note saved successfully with id {note.id}")  # Debug message
            messages.success(request, 'Note added successfully!')
        else:
            print(f"Form errors: {form.errors}")  # Debug message
            messages.error(request, 'Please check your input and try again.')
    return redirect('subdot_detail', subdot_id=subdot_id)

@require_http_methods(["POST"])
def create_note(request):
    try:
        print("Received create_note request")  # Debug message
        data = json.loads(request.body)
        content = data.get('content')
        subdot_id = data.get('subdot_id')
        
        print(f"Creating note for user {request.user.username}, subdot {subdot_id}")  # Debug message
        
        if not content or not subdot_id:
            print("Missing content or subdot_id")  # Debug message
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields'
            }, status=400)
        
        subdot = get_object_or_404(SubDot, id=subdot_id)
        note = Note.objects.create(
            learner=request.user.learnerprofile,
            subdot=subdot,
            content=content
        )
        
        print(f"Note created successfully with id {note.id}")  # Debug message
        
        return JsonResponse({
            'success': True,
            'note': {
                'id': note.id,
                'content': note.content,
                'subdot': {
                    'id': subdot.id,
                    'title': subdot.title
                },
                'updated_at': note.updated_at.strftime("%b %d, %Y %H:%M")
            }
        })
    except json.JSONDecodeError:
        print("Invalid JSON data")  # Debug message
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        print(f"Error creating note: {str(e)}")  # Debug message
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["PUT"])
def update_note(request, note_id):
    try:
        data = json.loads(request.body)
        content = data.get('content')
        
        if not content:
            return JsonResponse({
                'success': False,
                'error': 'Content is required'
            }, status=400)
        
        note = Note.objects.get(id=note_id, learner=request.user.learnerprofile)
        note.content = content
        note.updated_at = timezone.now()
        note.save()
        
        return JsonResponse({
            'success': True,
            'note': {
                'id': note.id,
                'content': note.content,
                'subdot': {
                    'id': note.subdot.id,
                    'title': note.subdot.title
                },
                'updated_at': note.updated_at.strftime("%b %d, %Y %H:%M")
            }
        })
    except Note.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Note not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["DELETE"])
def delete_note(request, note_id):
    try:
        note = Note.objects.get(id=note_id, learner=request.user.learnerprofile)
        note.delete()
        return JsonResponse({
            'success': True
        })
    except Note.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Note not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
def get_note(request, note_id):
    try:
        note = Note.objects.get(id=note_id, learner=request.user.learnerprofile)
        return JsonResponse({
            'success': True,
            'note': {
                'id': note.id,
                'content': note.content,
                'subdot': {
                    'id': note.subdot.id,
                    'title': note.subdot.title
                },
                'updated_at': note.updated_at.strftime("%b %d, %Y %H:%M")
            }
        })
    except Note.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Note not found'
        }, status=404)

@require_http_methods(["GET"])
def get_all_notes(request):
    try:
        notes = Note.objects.filter(learner=request.user.learnerprofile).order_by('-updated_at')
        return JsonResponse({
            'success': True,
            'notes': [{
                'id': note.id,
                'content': note.content,
                'subdot': {
                    'id': note.subdot.id,
                    'title': note.subdot.title
                },
                'updated_at': note.updated_at.strftime("%b %d, %Y %H:%M")
            } for note in notes]
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["POST"])
def mark_completed(request, subdot_id):
    subdot = get_object_or_404(SubDot, id=subdot_id)
    learner = request.user.learnerprofile
    
    # Get or create progress
    progress, created = Progress.objects.get_or_create(learner=learner, subdot=subdot)
    
    # Toggle completion status
    progress.completed = not progress.completed
    if progress.completed:
        progress.completed_at = timezone.now()
    progress.save()
    
    # Calculate dot progress after marking subdot as complete
    dot_progress = calculate_dot_progress(learner, subdot.dot)
    
    # If all subdots are completed, mark the dot as completed
    if dot_progress == 100:
        dot_progress_obj, created = DotProgress.objects.get_or_create(learner=learner, dot=subdot.dot)
        dot_progress_obj.completed = True
        dot_progress_obj.completed_at = timezone.now()
        dot_progress_obj.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'completed': progress.completed,
            'dot_progress': dot_progress
        })
    
    return redirect('subdot_detail', subdot_id=subdot_id)

@login_required
@require_http_methods(["POST"])
def toggle_bookmark(request, subdot_id):
    try:
        learner = request.user.learnerprofile
        subdot = get_object_or_404(SubDot, id=subdot_id)
        
        bookmark, created = Bookmark.objects.get_or_create(learner=learner, subdot=subdot)
        
        if not created:
            bookmark.delete()
            message = 'Bookmark removed successfully!'
            is_bookmarked = False
        else:
            message = 'Bookmark added successfully!'
            is_bookmarked = True
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': message,
                'is_bookmarked': is_bookmarked
            })
        else:
            messages.success(request, message)
            return redirect('subdot_detail', subdot_id=subdot_id)
            
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
        else:
            messages.error(request, f'Error: {str(e)}')
            return redirect('subdot_detail', subdot_id=subdot_id)

@login_required
def ask_instructor(request, subdot_id):
    if request.method == 'POST':
        form = InstructorQuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.learner = request.user.learnerprofile
            question.subdot_id = subdot_id
            question.save()
            messages.success(request, 'Question submitted to instructor!')
    return redirect('subdot_detail', subdot_id=subdot_id)

@login_required
def progress_view(request):
    learner = request.user.learnerprofile
    tracks = Track.objects.all()
    
    total_subdots = SubDot.objects.count()
    completed_subdots = Progress.objects.filter(
        learner=learner,
        completed=True
    ).count()
    
    overall_progress = (completed_subdots / total_subdots * 100) if total_subdots > 0 else 0
    
    tracks_progress = []
    for track in tracks:
        total_track_subdots = SubDot.objects.filter(dot__track=track).count()
        completed_track_subdots = Progress.objects.filter(
            learner=learner,
            subdot__dot__track=track,
            completed=True
        ).count()
        
        track_progress = (completed_track_subdots / total_track_subdots * 100) if total_track_subdots > 0 else 0
            
        tracks_progress.append({
            'title': track.title,
            'progress': track_progress,
            'completed_dots': completed_track_subdots,
            'total_dots': total_track_subdots
        })
    
    recent_achievements = Progress.objects.filter(
        learner=learner,
        completed=True
    ).order_by('-completed_at')[:5].select_related('subdot', 'subdot__dot')
    
    achievements_data = []
    for achievement in recent_achievements:
        achievements_data.append({
            'title': achievement.subdot.title,
            'description': f"Completed from {achievement.subdot.dot.title}",
            'date': achievement.completed_at
        })
    
    context = {
        'overall_progress': overall_progress,
        'completed_dots': completed_subdots,
        'total_dots': total_subdots,
        'tracks': tracks_progress,
        'recent_achievements': achievements_data
    }
    
    return render(request, 'learning/progress.html', context)

def calculate_dot_progress(learner, dot):
    """Calculate the progress percentage for a dot based on completed subdots"""
    total_subdots = dot.subdots.count()
    if total_subdots == 0:
        return 0
    
    completed_subdots = Progress.objects.filter(
        learner=learner,
        subdot__dot=dot,
        completed=True
    ).count()
    
    return int((completed_subdots / total_subdots) * 100)

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
from .models import DotProgress, Note
from django.utils import timezone

@require_http_methods(["POST"])
def create_note(request):
    try:
        print("Received create_note request")  # Debug message
        data = json.loads(request.body)
        content = data.get('content')
        subdot_id = data.get('subdot_id')
        
        print(f"Creating note for user {request.user.username}, subdot {subdot_id}")  # Debug message
        
        if not content or not subdot_id:
            print("Missing content or subdot_id")  # Debug message
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields'
            }, status=400)
        
        subdot = get_object_or_404(SubDot, id=subdot_id)
        note = Note.objects.create(
            learner=request.user.learnerprofile,
            subdot=subdot,
            content=content
        )
        
        print(f"Note created successfully with id {note.id}")  # Debug message
        
        return JsonResponse({
            'success': True,
            'note': {
                'id': note.id,
                'content': note.content,
                'subdot': {
                    'id': subdot.id,
                    'title': subdot.title
                },
                'updated_at': note.updated_at.strftime("%b %d, %Y %H:%M")
            }
        })
    except json.JSONDecodeError:
        print("Invalid JSON data")  # Debug message
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        print(f"Error creating note: {str(e)}")  # Debug message
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["PUT"])
def update_note(request, note_id):
    try:
        data = json.loads(request.body)
        content = data.get('content')
        
        if not content:
            return JsonResponse({
                'success': False,
                'error': 'Content is required'
            }, status=400)
        
        note = Note.objects.get(id=note_id, learner=request.user.learnerprofile)
        note.content = content
        note.updated_at = timezone.now()
        note.save()
        
        return JsonResponse({
            'success': True,
            'note': {
                'id': note.id,
                'content': note.content,
                'subdot': {
                    'id': note.subdot.id,
                    'title': note.subdot.title
                },
                'updated_at': note.updated_at.strftime("%b %d, %Y %H:%M")
            }
        })
    except Note.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Note not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["DELETE"])
def delete_note(request, note_id):
    try:
        note = Note.objects.get(id=note_id, learner=request.user.learnerprofile)
        note.delete()
        return JsonResponse({
            'success': True
        })
    except Note.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Note not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
def get_note(request, note_id):
    try:
        note = Note.objects.get(id=note_id, learner=request.user.learnerprofile)
        return JsonResponse({
            'success': True,
            'note': {
                'id': note.id,
                'content': note.content,
                'subdot': {
                    'id': note.subdot.id,
                    'title': note.subdot.title
                },
                'updated_at': note.updated_at.strftime("%b %d, %Y %H:%M")
            }
        })
    except Note.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Note not found'
        }, status=404)

@require_http_methods(["GET"])
def get_all_notes(request):
    try:
        notes = Note.objects.filter(learner=request.user.learnerprofile).order_by('-updated_at')
        return JsonResponse({
            'success': True,
            'notes': [{
                'id': note.id,
                'content': note.content,
                'subdot': {
                    'id': note.subdot.id,
                    'title': note.subdot.title
                },
                'updated_at': note.updated_at.strftime("%b %d, %Y %H:%M")
            } for note in notes]
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["POST"])
def update_progress(request, subdot_id):
    try:
        data = json.loads(request.body)
        time_spent = data.get('time_spent')
        
        if time_spent is not None:
            learner = request.user.learnerprofile
            subdot = get_object_or_404(SubDot, id=subdot_id)
            progress = Progress.objects.get_or_create(learner=learner, subdot=subdot)[0]
            
            # Convert seconds to timedelta
            time_spent_delta = timezone.timedelta(seconds=int(time_spent))
            
            # If there's existing time_spent, add to it
            if progress.time_spent:
                progress.time_spent += time_spent_delta
            else:
                progress.time_spent = time_spent_delta
            
            progress.save()
            
            return JsonResponse({
                'success': True,
                'time_spent': str(progress.time_spent)
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def generate_assessment(request, subdot_id):
    subdot = get_object_or_404(Subdot, id=subdot_id)
    content_items = list(subdot.contents.all())

    # Shuffle and select questions
    random.shuffle(content_items)
    number_of_questions = min(len(content_items), 10)
    selected_items = content_items[:number_of_questions]

    if request.method == "POST":
        learner = request.user
        assessment = Assessment.objects.create(learner=learner, subdot=subdot)
        score = 0

        for item in selected_items:
            selected_answer = request.POST.get(f"question_{item.id}", "")
            is_correct = selected_answer == item.correct_answer
            if is_correct:
                score += 1

            AssessmentQuestion.objects.create(
                assessment=assessment,
                question_text=item.question,
                selected_answer=selected_answer,
                correct_answer=item.correct_answer,
                is_correct=is_correct
            )

        # Save final score
        result = AssessmentResult.objects.create(
            learner=learner,
            subdot=subdot,
            score=score,
            total_marks=10
        )

        return redirect("assessment_result", result_id=result.id)

    return render(request, "learning/assessment.html", {
        "subdot": subdot,
        "questions": selected_items
    })

def assessment_result(request, result_id):
    result = get_object_or_404(AssessmentResult, id=result_id)
    return render(request, "learning/assessment_result.html", {"result": result})