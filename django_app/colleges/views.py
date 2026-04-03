from django.shortcuts import render, get_object_or_404
from django.utils import translation
from .models import College, University

def college_list(request):
    """
    Displays the grouped list of universities and their colleges.
    Optimized to prevent N+1 queries and translation crashes.
    """
    user_lang = translation.get_language()
    
    # 1. Prefetch translations for both University and College to avoid crashes
    # 2. Prefetch colleges linked to each university
    universities = University.objects.prefetch_related(
        'translations', 
        'colleges__translations'
    ).all()

    return render(request, "colleges/list.html", {
        "universities": universities,
        "current_lang": user_lang
    })

def college_detail(request, code):
    """
    Fetches details for a single college.
    Uses .prefetch_related('courses__translations') to ensure course names 
    don't crash the page if a translation is missing.
    """
    # Fetch college with its translations
    college = get_object_or_404(College.objects.prefetch_related('translations'), code=code)
    
    # Prefetch courses, their translations, and their cutoffs
    courses = college.courses.prefetch_related(
        'translations', 
        'cutoffs'
    ).all()
    
    return render(request, "colleges/detail.html", {
        "college": college, 
        "courses": courses
    })