from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Candidate, Company, Job,JobApplication

admin.site.register(User, UserAdmin)
admin.site.register(Candidate)
admin.site.register(Company)
admin.site.register(Job)
admin.site.register(JobApplication)