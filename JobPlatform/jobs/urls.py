from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('',views.home, name='home'),
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/<int:job_id>/', views.job_detail, name='job_detail'), 
    path('post_job/', views.post_job, name='post_job'),  
    path('posted_job/', views.posted_jobs, name='posted_job'),  
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout_view, name='logout'),
    path('job/<int:job_id>/candidates/', views.view_candidates, name='view_candidates'),
    path('job/<int:job_id>/apply/', views.apply_to_job, name='apply_to_job'),
    path('login/candidate/', views.candidate_login, name='candidate_login'),
    path('login/company/', views.company_login, name='company_login'),
    path('register/candidate/', views.candidate_register, name='candidate_register'),
    path('register/company/', views.company_register, name='company_register'),
    path('select-role/', views.select_role, name='select_role'),
    path('view-resume/<int:candidate_id>/', views.view_resume, name='view_resume'),
    path('job/<int:job_id>/applications/', views.job_applications, name='job_applications'),
]
