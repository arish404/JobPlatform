from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver

# Custom User model
class User(AbstractUser):
    is_candidate = models.BooleanField(default=False)
    is_company = models.BooleanField(default=False)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    class Meta:
        db_table = "jobs_user"

# Candidate model
class Candidate(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="candidate_profile")
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    skills = models.CharField(max_length=200, null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)

    def __str__(self):
        return self.user.username

# Company model
class Company(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="company_profile")
    company_name = models.CharField(max_length=200)
    company_website = models.URLField(null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)

    def __str__(self):
        return self.company_name

# Job model
class Job(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    keywords = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200)
    posted_at = models.DateTimeField(auto_now_add=True)
    candidates = models.ManyToManyField(Candidate, through='JobApplication', related_name='applied_jobs')

    def __str__(self):
        return self.title

# JobApplication model
class JobApplication(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    score = models.FloatField(default=0.0)  # Resume score
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.candidate.user.username} -> {self.job.title}"
