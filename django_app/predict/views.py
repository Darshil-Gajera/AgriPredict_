import json
import traceback
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .predictors import AgriPredictor


def category_view(request, category):
    """Render category-specific calculator page"""
    return render(request, f"predict/category{category}.html", {
        "category": category
    })


@require_POST
def calculate_view(request):
    """Handles merit calculation and college recommendations"""
    try:
        data = json.loads(request.body)

        theory_ob      = float(data.get('theory_obtained') or 0)
        theory_total   = float(data.get('theory_total') or 300)
        gujcet         = float(data.get('gujcet_marks') or 0)
        category       = str(data.get('category') or '1')
        student_cat    = str(data.get('student_category') or 'OPEN').strip().upper()
        farming        = bool(data.get('farming_background'))

        predictor = AgriPredictor(category)

        merit_results = predictor.calculate_merit(
            theory_ob, theory_total, gujcet, farming
        )

        colleges = predictor.get_recommendations(
            merit_results['final_merit'],
            student_cat
        )

        print("========== DEBUG ==========")
        print("Input:", data)
        print("Merit results:", merit_results)
        print("Colleges count:", len(colleges))
        if colleges:
            print("First college keys:", list(colleges[0].keys()))
            print("First college:", colleges[0])
        print("===========================")

        # Guarantee colleges is never empty
        if not colleges:
            colleges = [{
                "name": "No colleges found",
                "course": "-",
                "location": "",
                "cutoff": 0,
                "probability": 0,
                "chance_label": "Low",
                "round_prediction": "Try lower preferences"
            }]

        # Build response with explicit, guaranteed key names
        response_data = {
            "merit":       float(merit_results.get('final_merit', 0)),
            "theory_comp": float(merit_results.get('theory_comp', 0)),
            "gujcet_comp": float(merit_results.get('gujcet_comp', 0)),
            "bonus_comp":  float(merit_results.get('bonus_comp', 0)),
            "colleges": [
                {
                    "name":             str(c.get("name", "") or "Unknown"),
                    "course":           str(c.get("course", "") or "Unknown"),
                    "location":         str(c.get("location", "") or ""),
                    "cutoff":           float(c.get("cutoff", 0) or 0),
                    "probability":      float(c.get("probability", 0) or 0),
                    "chance_label":     str(c.get("chance_label", "Low") or "Low"),
                    "round_prediction": str(c.get("round_prediction", "—") or "—"),
                }
                for c in colleges
            ]
        }

        print("RESPONSE KEYS:", list(response_data.keys()))
        print("COLLEGE[0] KEYS:", list(response_data['colleges'][0].keys()) if response_data['colleges'] else "empty")

        return JsonResponse(response_data)

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({
            "error": "Something went wrong",
            "details": str(e)
        }, status=400)


@require_POST
def save_result_view(request):
    """Save user result (placeholder for future DB logic)"""
    try:
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Login required"}, status=401)
        return JsonResponse({"saved": True})
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=400)