from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from .models import SavedResult
from .forms import ProfileForm

import json


@login_required
def profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Profile updated successfully."))
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)

    return render(request, "accounts/profile.html", {"form": form})


@login_required
def saved_results(request):
    results = SavedResult.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "accounts/saved_results.html", {"results": results})


@login_required
def delete_saved_result(request, pk):
    result = get_object_or_404(SavedResult, pk=pk, user=request.user)
    if request.method == "POST":
        result.delete()
        messages.success(request, _("Result deleted."))

    return redirect("accounts:saved_results")


# ✅ FIXED SAVE VIEW
@require_POST
@login_required
def save_prediction(request):
    try:
        data = json.loads(request.body)

        # ✅ DEBUG (optional - remove later)
        print("📥 Incoming Save Data:", data)

        # ✅ VALIDATION (IMPORTANT)
        if not data.get("merit"):
            return JsonResponse({"saved": False, "error": "Missing merit"}, status=400)

        # ✅ CREATE OBJECT
        result = SavedResult.objects.create(
            user=request.user,
            category=str(data.get('category', '1')),
            merit_score=data.get('merit'),

            # ✅ FIELD NAME MATCH (VERY IMPORTANT)
            theory_marks=data.get('theory_obtained'),
            theory_total=data.get('theory_total', 300),
            gujcet_marks=data.get('gujcet_marks'),

            farming_bonus=data.get('farming', False),
            student_category=data.get('student_category', 'OPEN'),

            city=data.get('city', ''),
            district=data.get('district', '')
        )

        # ✅ DEBUG CONFIRMATION
        print("✅ Saved Result ID:", result.id)

        return JsonResponse({"saved": True})

    except Exception as e:
        import traceback
        traceback.print_exc()

        return JsonResponse({
            "saved": False,
            "error": str(e)
        }, status=400)