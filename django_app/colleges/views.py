from django.shortcuts import render, get_object_or_404
from .models import College, University


def college_list(request):
    universities = University.objects.prefetch_related("colleges").all()
    return render(request, "colleges/list.html", {"universities": universities})


def college_detail(request, code):
    college = get_object_or_404(College, code=code)
    courses = college.courses.prefetch_related("cutoffs").all()
    return render(request, "colleges/detail.html", {"college": college, "courses": courses})
