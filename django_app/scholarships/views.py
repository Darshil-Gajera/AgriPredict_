from django.shortcuts import render
from .models import Scholarship

def scholarship_list(request):
    # Optimization: Prefetch translations to improve performance
    scholarships = Scholarship.objects.filter(is_active=True).prefetch_related('translations')
    return render(request, "scholarships/list.html", {"scholarships": scholarships})