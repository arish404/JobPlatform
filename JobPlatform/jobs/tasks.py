# jobs/tasks.py
from celery import shared_task
from django.core.cache import cache
from .models import JobApplication, Candidate, Job
from .utils import parse_resume_and_calculate_score  # adjust if located elsewhere

@shared_task
def process_resume_score(application_id, resume_path, keywords):
    """
    Asynchronously calculate resume score and update the JobApplication record.
    """
    try:
        score = parse_resume_and_calculate_score(resume_path, keywords)
        app = JobApplication.objects.get(id=application_id)
        app.score = score
        app.save()

        # Clear related cache (optional)
        cache.delete(f"candidates_for_job_{app.job.id}")
        return f"Score {score} updated for {app.candidate.user.username}"
    except Exception as e:
        return f"Error processing application {application_id}: {e}"
