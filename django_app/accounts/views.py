from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .forms import ProfileForm, SavedResultForm
from .models import SavedResult
import json
from django.core.mail import send_mail
from django.conf import settings

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


@require_POST
@login_required
def save_prediction(request):
    try:
        data = json.loads(request.body)
        print("📥 Incoming Save Data:", data)

        # ── Pull values supporting BOTH key conventions ──────────────────
        # JS in category1.html sends: theory, gujcet, farming
        # JS in merit_calculator.js sends: theory_obtained, gujcet_marks, farming_background
        merit         = data.get('merit')
        theory_marks  = data.get('theory')        or data.get('theory_obtained')
        theory_total  = data.get('theory_total',  300)
        gujcet_marks  = data.get('gujcet')        or data.get('gujcet_marks')
        farming       = data.get('farming')        or data.get('farming_background', False)
        category      = str(data.get('category', '1'))
        student_cat   = data.get('student_category', 'OPEN')
        city          = data.get('city', '')
        district      = data.get('district', '')

        # ── Validate required fields ─────────────────────────────────────
        if merit is None:
            return JsonResponse({"saved": False, "error": "Missing merit score"}, status=400)
        if theory_marks is None:
            return JsonResponse({"saved": False, "error": "Missing theory marks"}, status=400)
        if gujcet_marks is None:
            return JsonResponse({"saved": False, "error": "Missing GUJCET marks"}, status=400)

        result = SavedResult.objects.create(
            user             = request.user,
            category         = category,
            merit_score      = float(merit),
            theory_marks     = float(theory_marks),
            theory_total     = int(theory_total),
            gujcet_marks     = float(gujcet_marks),
            farming_bonus    = bool(farming),
            student_category = student_cat,
            city             = city,
            district         = district,
        )
        print("✅ Saved Result ID:", result.id, "for user:", request.user.email)
        return JsonResponse({"saved": True})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"saved": False, "error": str(e)}, status=400)


@login_required
def edit_saved_result(request, pk):
    result = get_object_or_404(SavedResult, pk=pk, user=request.user)

    if request.method == "POST":
        form = SavedResultForm(request.POST, instance=result)
        if form.is_valid():
            saved = form.save(commit=False)

            # ── Recalculate merit score with updated marks ────────────────
            try:
                from predict.predictors import AgriPredictor
                predictor    = AgriPredictor(saved.category)
                merit_result = predictor.calculate_merit(
                    float(saved.theory_marks),
                    float(saved.theory_total),
                    float(saved.gujcet_marks),
                    saved.farming_bonus,
                )
                saved.merit_score = merit_result['final_merit']
                print("✅ Recalculated merit:", saved.merit_score)
            except Exception as e:
                print("⚠️ Merit recalculation failed:", e)
                # Keep existing merit score if predictor fails

            saved.save()
            messages.success(request, _("Result updated successfully. Merit score recalculated."))
            return redirect("accounts:saved_results")
    else:
        form = SavedResultForm(instance=result)

    return render(request, "accounts/edit_saved_result.html", {
        "form":   form,
        "result": result,
    })
@login_required
def profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Profile updated successfully."))

            # ── Email notification ────────────────────────────────
            try:
                send_mail(
                    subject="[AgriPredict] Profile Updated",
                    message=f"Hi {request.user.email},\n\nYour profile was updated successfully.\n\nIf this wasn't you, please contact us immediately.\n\nAgriPredict Team",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[request.user.email],
                    fail_silently=True,
                )
            except Exception as e:
                print("Email error:", e)

            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "accounts/profile.html", {"form": form})
