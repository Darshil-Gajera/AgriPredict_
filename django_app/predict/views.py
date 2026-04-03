from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.translation import gettext_lazy as _
import json

from .merit import MeritInput, calculate_merit, get_admission_probability
from colleges.models import College, CutoffMerit, Course
from accounts.models import SavedResult


def _get_colleges_with_probability(merit_score, category, student_category):
    """Return college queryset annotated with admission probability."""
    colleges = College.objects.filter(
        category=category, is_active=True
    ).prefetch_related("courses__cutoffs", "university")

    results = []
    for college in colleges:
        for course in college.courses.all():
            # Get latest cutoff for this student category
            cutoff = (
                course.cutoffs.filter(
                    student_category=student_category,
                    year__gte=2023,
                )
                .order_by("-year", "-round_no")
                .first()
            )
            prob = get_admission_probability(merit_score, cutoff.last_merit) if cutoff else "unknown"
            results.append({
                "college_id": college.id,
                "college_name": college.safe_translation_getter("name", any_language=True),
                "college_code": college.code,
                "university": college.safe_translation_getter("short_name", any_language=True) if hasattr(college, "university") else "",
                "city": college.safe_translation_getter("city", any_language=True),
                "district": college.safe_translation_getter("district", any_language=True),
                "course_id": course.id,
                "course_name": course.safe_translation_getter("name", any_language=True),
                "last_cutoff": cutoff.last_merit if cutoff else None,
                "cutoff_year": cutoff.year if cutoff else None,
                "probability": prob,
            })
    return results


def category_view(request, category):
    """Render the merit calculator page for a given category."""
    category = str(category)
    if category not in ("1", "2", "3"):
        category = "1"
    return render(request, f"predict/category{category}.html", {"category": category})


@require_POST
def calculate_view(request):
    """AJAX endpoint: receive form data, return merit + college list."""
    try:
        data = json.loads(request.body)
        inp = MeritInput(
            category=str(data["category"]),
            theory_obtained=float(data["theory_obtained"]),
            theory_total=int(data["theory_total"]),
            gujcet_marks=float(data["gujcet_marks"]),
            student_category=data["student_category"].upper(),
            farming_background=bool(data.get("farming_background", False)),
            subject_group=data.get("subject_group", ""),
        )
    except (KeyError, ValueError, TypeError) as e:
        return JsonResponse({"error": str(e)}, status=400)

    result = calculate_merit(inp)
    colleges = _get_colleges_with_probability(
        result.final_merit, inp.category, inp.student_category
    )

    return JsonResponse({
        "merit": result.final_merit,
        "raw_merit": result.raw_merit,
        "theory_component": result.theory_component,
        "gujcet_component": result.gujcet_component,
        "farming_bonus_applied": result.farming_bonus_applied,
        "colleges": colleges,
    })


@login_required
@require_POST
def save_result_view(request):
    """Save a merit result for the logged-in user."""
    try:
        data = json.loads(request.body)
        SavedResult.objects.create(
            user=request.user,
            category=data["category"],
            theory_marks=data["theory_obtained"],
            theory_total=data["theory_total"],
            gujcet_marks=data["gujcet_marks"],
            student_category=data["student_category"],
            merit_score=data["merit"],
            farming_bonus=data.get("farming_background", False),
            subject_group=data.get("subject_group", ""),
            city=data.get("city", ""),
            district=data.get("district", ""),
            label=data.get("label", ""),
        )
    except (KeyError, ValueError) as e:
        return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"saved": True})
