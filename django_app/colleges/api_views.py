from rest_framework.views import APIView
from rest_framework.response import Response
from .models import College, CutoffMerit


class CollegeListAPIView(APIView):
    def get(self, request):
        category = request.query_params.get("category")
        qs = College.objects.filter(is_active=True)
        if category:
            qs = qs.filter(category=category)
        data = [
            {
                "id": c.id,
                "code": c.code,
                "name": c.safe_translation_getter("name", any_language=True),
                "city": c.safe_translation_getter("city", any_language=True),
                "district": c.safe_translation_getter("district", any_language=True),
                "university": c.university.safe_translation_getter("short_name", any_language=True),
                "category": c.category,
            }
            for c in qs.select_related("university")
        ]
        return Response(data)


class CutoffAPIView(APIView):
    def get(self, request):
        college_code = request.query_params.get("college_code")
        student_category = request.query_params.get("student_category", "OPEN")
        year = request.query_params.get("year")
        qs = CutoffMerit.objects.filter(student_category=student_category)
        if college_code:
            qs = qs.filter(course__college__code=college_code)
        if year:
            qs = qs.filter(year=year)
        data = [
            {
                "course": c.course.safe_translation_getter("name", any_language=True),
                "college_code": c.course.college.code,
                "year": c.year,
                "round": c.round_no,
                "student_category": c.student_category,
                "last_merit": c.last_merit,
            }
            for c in qs.select_related("course__college")[:200]
        ]
        return Response(data)
