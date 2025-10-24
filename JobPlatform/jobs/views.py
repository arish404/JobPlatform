from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse,FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate,logout
from django.contrib import messages
from .models import Job, JobApplication, Candidate,Company
from .forms import CandidateRegistrationForm, CompanyRegistrationForm
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponseForbidden,HttpResponse
from .utils import parse_resume_and_calculate_score 
from django.core.cache import cache
from .tasks import process_resume_score

def home(req):
    return render(req,'jobs/home.html')

@login_required
def job_list(request):
    cache_key = "job_list"
    jobs = cache.get(cache_key)

    if not jobs:
        jobs = Job.objects.all()
        cache.set(cache_key, jobs, 300)  # Cache for 5 minutes (300s)

    applied_jobs = []
    if request.user.is_authenticated and request.user.is_candidate:
        try:
            candidate = request.user.candidate_profile
            applied_jobs = candidate.applied_jobs.all()
        except Candidate.DoesNotExist:
            applied_jobs = []

    for job in jobs:
        job.keywords_list = job.keywords.split(",")
        job.applied = job in applied_jobs

    return render(request, 'jobs/job_list.html', {'jobs': jobs})

@login_required
def job_detail(request, job_id):
    cache_key = f"job_detail_{job_id}"
    job = cache.get(cache_key)

    if not job:
        job = get_object_or_404(Job, id=job_id)
        cache.set(cache_key, job, 600)

    if not request.user.is_authenticated or not request.user.is_candidate:
        return HttpResponseForbidden("You must be logged in as a candidate to apply for jobs.")
    
    try:
        candidate = request.user.candidate_profile
    except Candidate.DoesNotExist:
        return HttpResponseForbidden("Candidate profile not found.")
    
    already_applied = JobApplication.objects.filter(candidate=candidate, job=job).exists()

    return render(request, 'jobs/job_detail.html', {
        'job': job,
        'candidate': candidate,
        'already_applied': already_applied,
        "keywords_list": job.keywords.split(",") if job.keywords else []
    })

@login_required
def post_job(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        keywords = request.POST.get('keywords')

        job = Job.objects.create(
            title=title,
            description=description,
            keywords=keywords,
            company_name=request.user.company_profile.company_name
        )
        cache.delete("job_list")
        cache.delete(f"posted_jobs_{request.user.company_profile.company_name}")
        return JsonResponse({'message': 'Job posted successfully', 'job': job.title})
    return render(request, 'jobs/post_job.html')

@login_required
def posted_jobs(request):
    # Ensure the logged-in user is a company
    if not request.user.is_company:
        return render(request, 'error.html', {'message': 'Access Denied'})

    company_name = request.user.company_profile.company_name
    cache_key = f"posted_jobs_{company_name}"

    jobs = cache.get(cache_key)
    if not jobs:
        jobs = Job.objects.filter(company_name=company_name).order_by('-posted_at')
        cache.set(cache_key, jobs, 600)

    return render(request, 'jobs/posted_jobs.html', {'jobs': jobs})

def candidate_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_company:  # Ensure user is a candidate
                login(request, user)
                return redirect('job_list')
            else:
                messages.error(request, "You are not registered as a candidate.")
        else:
            messages.error(request, "Invalid credentials.")
    else:
        form = AuthenticationForm()
    return render(request, 'jobs/login.html', {'form': form})

def company_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_company:  # Ensure user is a company
                login(request, user)
                return redirect('job_list')
            else:
                messages.error(request, "You are not registered as a company.")
        else:
            messages.error(request, "Invalid credentials.")
    else:
        form = AuthenticationForm()
    return render(request, 'jobs/login.html', {'form': form})

def candidate_register(request):
    if request.method == 'POST':
        form = CandidateRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_company = False  # Ensure user is a candidate
            user.save()

            Candidate.objects.create(
                user=user,
                resume=form.cleaned_data.get('resume'),
                skills=form.cleaned_data.get('skills'),
                profile_image=form.cleaned_data.get('profile_image')
            )

            login(request, user)
            return redirect('job_list')
    else:
        form = CandidateRegistrationForm()
    return render(request, 'jobs/register_candidate.html', {'form': form})

def company_register(request):
    if request.method == 'POST':
        form = CompanyRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_company = True  # Ensure user is a company
            user.save()

            Company.objects.create(
                user=user,
                company_name=form.cleaned_data.get('company_name'),
                company_website=form.cleaned_data.get('company_website'),
                profile_image=form.cleaned_data.get('profile_image')
            )

            login(request, user)
            return redirect('job_list')
    else:
        form = CompanyRegistrationForm()
    return render(request, 'jobs/register_company.html', {'form': form})

def select_role(request):
    return render(request, 'jobs/role_selection.html')

@login_required
def apply_to_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    # Ensure user is a candidate
    if not request.user.is_candidate:
        return HttpResponseForbidden("You must be logged in as a candidate to apply for jobs.")
    
    try:
        candidate = request.user.candidate_profile
    except Candidate.DoesNotExist:
        messages.error(request, "Candidate profile not found.")
        return redirect('job_detail', job_id=job_id)

    if request.method == 'POST':
        resume_file = None

        # Handle resume selection
        if 'use_existing' in request.POST:
            if not candidate.resume:
                messages.error(request, "No existing resume found. Please upload a resume.")
                return redirect('job_detail', job_id=job_id)
            resume_file = candidate.resume
        elif 'upload_new' in request.POST and 'resume' in request.FILES:
            resume_file = request.FILES['resume']

        if resume_file:
            # Create or update job application entry
            job_application, created = JobApplication.objects.get_or_create(
                candidate=candidate, job=job,
                defaults={'resume': resume_file}
            )
            if not created:
                job_application.resume = resume_file
                job_application.save()

            # Trigger async Celery task
            process_resume_score.delay(
                job_application.id, 
                job_application.resume.path, 
                job.keywords.split(",")
            )

            messages.success(
                request, 
                f"Applied for {job.title}. Resume scoring will be processed shortly in the background."
            )
        else:
            messages.error(request, "Something went wrong. Please try again.")

        cache.delete(f"candidates_for_job_{job_id}")
        return redirect('job_list')

    return redirect('job_detail', job_id=job_id)

@login_required
def view_candidates(request, job_id):
    cache_key = f"candidates_for_job_{job_id}"
    applications = cache.get(cache_key)

    if not applications:
        applications = JobApplication.objects.filter(job_id=job_id).order_by('-score')
        cache.set(cache_key, applications, 600)

    job = get_object_or_404(Job, id=job_id)
    return render(request, 'jobs/candidates_list.html', {'job': job, 'applications': applications})

@login_required
def profile(request):
    user = request.user  # Current logged-in user

    # Check if the user is a candidate
    if hasattr(user, 'candidate_profile'):
        candidate = user.candidate_profile  # Access the related Candidate object
    else:
        candidate = None

    if request.method == 'POST' and 'resume' in request.FILES:
        if candidate:  # Update resume only if the user is a candidate
            candidate.resume = request.FILES['resume']
            candidate.save()
            messages.success(request, "Resume updated successfully!")
        else:
            messages.error(request, "Only candidates can update resumes.")
        return redirect('profile')  # Redirect to the profile page

    return render(request, 'jobs/profile_page.html', {'user': user, 'candidate': candidate})

@login_required
def view_resume(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)
    if candidate.resume:
        response = FileResponse(candidate.resume.open(), content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename=%s' % candidate.resume.name
        return response
    else:
        return HttpResponse("Resume not found", status=404)

@login_required
def job_applications(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    # Only allow the employer who created the job (or admin) to view
    if not hasattr(request.user, "company_profile") and not request.user.is_superuser:
        return HttpResponseForbidden("Access denied: Only the employer can view job applications.")

    employer = request.user.company_profile
    if job.company_name != str(employer) and not request.user.is_superuser:
        return HttpResponseForbidden("Access denied: You are not the owner of this job posting.")

    applications = JobApplication.objects.filter(job=job).order_by('-score')
    return render(request, 'jobs/job_applications.html', {
        'job': job,
        'applications': applications
    })


def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect('/')  # Redirect to home page