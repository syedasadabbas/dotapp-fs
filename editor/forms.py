from django import forms
from .models import Track, Dot, SubDot, Topic, Editor

class TrackForm(forms.ModelForm):
    class Meta:
        model = Track
        fields = ['title', 'description']

class DotForm(forms.ModelForm):
    class Meta:
        model = Dot
        fields = ['title', 'track']

class SubDotForm(forms.ModelForm):
    class Meta:
        model = SubDot
        fields = ['title', 'dot']  

class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['title', 'content', 'code', 'image', 'audio', 'subdot']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'tinymce'}),  # For TinyMCE
            'code': forms.Textarea(attrs={'class': 'monaco'})  # For Monaco Editor
        }

class ContentForm(forms.Form):
    title = forms.CharField(max_length=255)
    content = forms.CharField(widget=forms.Textarea)
    code = forms.CharField(widget=forms.Textarea)
    image = forms.ImageField(required=False)
    audio = forms.FileField(required=False)

class EditorForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Editor
        fields = ['username', 'email', 'password']