from django import forms
from .models import Track, Dot, SubDot, Topic, Editor
import json

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
        fields = ['title', 'content', 'code', 'image', 'audio', 'subdot', 'timestamps', 'order']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'tinymce', 'rows': 10}),
            'code': forms.Textarea(attrs={'class': 'monaco', 'rows': 10}),
            'timestamps': forms.HiddenInput(),
        }
        
    def clean_timestamps(self):
        timestamps = self.cleaned_data.get('timestamps')
        if timestamps and isinstance(timestamps, str):
            try:
                return json.loads(timestamps)
            except json.JSONDecodeError:
                return None
        return timestamps

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