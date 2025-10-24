from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Candidate, Company
from django.contrib.auth import get_user_model

User = get_user_model()

class CandidateRegistrationForm(UserCreationForm):
    resume = forms.FileField(required=False)
    skills = forms.CharField(max_length=200, required=False)
    profile_image = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'resume', 'skills', 'profile_image']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Enter your username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email'}),
            'password1': forms.PasswordInput(attrs={'placeholder': 'Enter password'}),
            'password2': forms.PasswordInput(attrs={'placeholder': 'Confirm password'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap classes to form fields
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        self.fields['resume'].widget.attrs.update({'class': 'form-control'})
        self.fields['skills'].widget.attrs.update({'class': 'form-control'})
        self.fields['profile_image'].widget.attrs.update({'class': 'form-control'})

        for fieldname in ['username', 'password1', 'password2']:
            self.fields[fieldname].help_text = None

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_candidate = True  # Mark as candidate
        if commit:
            user.save()
            Candidate.objects.create(
                user=user,
                resume=self.cleaned_data.get('resume'),
                skills=self.cleaned_data.get('skills'),
            )
        return user



class CompanyRegistrationForm(UserCreationForm):
    company_name = forms.CharField(max_length=200)
    company_website = forms.URLField(required=False)
    profile_image = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'company_name', 'company_website', 'profile_image']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Enter your username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email'}),
        }
        help_texts = {
            'username': None,  # This removes the help text for the username field
            'password1':None,
            'password2':None
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap classes to form fields
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        self.fields['company_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['company_website'].widget.attrs.update({'class': 'form-control'})
        self.fields['profile_image'].widget.attrs.update({'class': 'form-control'})

        for fieldname in ['username', 'password1', 'password2']:
            self.fields[fieldname].help_text = None
            
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_company = True  # Mark as company
        if commit:
            user.save()
            Company.objects.create(
                user=user,
                company_name=self.cleaned_data.get('company_name'),
                company_website=self.cleaned_data.get('company_website'),
            )
        return user
