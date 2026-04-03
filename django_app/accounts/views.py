from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _

from .models import SavedResult
from .forms import ProfileForm


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
    results = SavedResult.objects.filter(user=request.user)
    return render(request, "accounts/saved_results.html", {"results": results})


@login_required
def delete_saved_result(request, pk):
    result = get_object_or_404(SavedResult, pk=pk, user=request.user)
    if request.method == "POST":
        result.delete()
        messages.success(request, _("Result deleted."))
    return redirect("accounts:saved_results")
