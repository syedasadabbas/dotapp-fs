from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from learning.forms import UserUpdateForm, ProfileUpdateForm

@login_required
def profile(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.learnerprofile)

        if 'update_profile' in request.POST:
            if user_form.is_valid() and profile_form.is_valid():
                user = user_form.save(commit=False)
                profile = profile_form.save(commit=False)

                # Update user fields
                if user_form.cleaned_data.get('first_name'):
                    user.first_name = user_form.cleaned_data['first_name']
                if user_form.cleaned_data.get('last_name'):
                    user.last_name = user_form.cleaned_data['last_name']
                if user_form.cleaned_data.get('email'):
                    user.email = user_form.cleaned_data['email']
                user.save()

                # Update profile fields
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
                # Handle form errors
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
