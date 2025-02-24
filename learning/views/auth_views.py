from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already taken. Please choose a different one.')
            else:
                user = form.save()
                login(request, user)
                messages.success(request, 'Account created successfully! Welcome to the learning platform.')
                return redirect('dashboard')
    else:
        form = CustomUserCreationForm()

    return render(request, 'learning/register.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')