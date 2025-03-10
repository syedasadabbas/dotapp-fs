from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import LearnerProfile, Note, InstructorQuestion

#
# 1) USER REGISTRATION
#
class CustomUserCreationForm(UserCreationForm):
    """
    Registration form. You can rename it to UserRegisterForm if you prefer.
    """
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        # The default fields are: username, password1, password2
        # We'll add 'email' explicitly
        fields = UserCreationForm.Meta.fields + ('email',)


#
# 2) USER UPDATE FORM
#
class UserUpdateForm(forms.ModelForm):
    """
    Updates User model fields (username, email, first_name, last_name).
    Merges your snippet's logic with any existing validations you need.
    """
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)
    username = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # You can customize help_texts or widgets here
        self.fields['username'].help_text = 'Letters, digits and @/./+/-/_ only.'
        self.fields['email'].help_text = 'Enter a valid email address.'

    def clean(self):
        cleaned_data = super().clean()
        # If username wasn’t provided, fallback to the old username
        if not cleaned_data.get('username'):
            cleaned_data['username'] = self.instance.username
        return cleaned_data


#
# 3) PROFILE UPDATE FORM
#
class ProfileUpdateForm(forms.ModelForm):
    """
    Updates the LearnerProfile fields (bio, profile_picture, learning_style, etc.).
    Combines fields from your snippet + any existing ones.
    """
    bio = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False,
        help_text='Tell us about yourself'
    )

    class Meta:
        model = LearnerProfile
        fields = [
            'bio',
            'profile_picture',
            'learning_style',
            'email_notifications',
            'progress_reminders',
            'public_profile',    # If you want to include these fields
            'show_progress'      # from your snippet
        ]
        help_texts = {
            'profile_picture': 'Upload your profile picture',
            'learning_style': 'Choose your preferred way of learning',
            'email_notifications': 'Receive updates about your courses via email',
            'progress_reminders': 'Get reminders about your learning progress',
            'public_profile': 'Allow other users to see your profile',
            'show_progress': 'Show your learning progress to other users'
        }


#
# 4) NOTE FORM
#
class NoteForm(forms.ModelForm):
    """
    For creating/updating notes. 
    Your snippet uses a CharField with a Textarea; 
    here we combine it into Meta for clarity.
    """
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'form-control',
            'placeholder': 'Write your note here...',
            'style': 'color: white; background: rgba(17, 34, 64, 0.7); '
                     'border: 1px solid rgba(100, 255, 218, 0.1);'
        }),
        required=True
    )

    class Meta:
        model = Note
        fields = ['content']


#
# 5) INSTRUCTOR QUESTION FORM (If Needed)
#
class InstructorQuestionForm(forms.ModelForm):
    """
    If you have a model for instructor questions, you can keep it here.
    """
    class Meta:
        model = InstructorQuestion
        fields = ['question']
        widgets = {
            'question': forms.Textarea(attrs={'rows': 4}),
        }
