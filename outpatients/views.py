from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from outpatients.forms import OutpatientForm
from outpatients.models import Outpatient


def top(request):
    outpatients = Outpatient.objects.all()
    context = {"outpatients": outpatients}
    return render(request, "outpatients/top.html", context)


@login_required
def outpatient_new(request):
    if request.method == "POST":
        form = OutpatientForm(request.POST)
        if form.is_valid():
            outpatient = form.save(commit=False)
            outpatient.created_by = request.user
            outpatient.save()
            return redirect(outpatient_detail, outpatient_id=outpatient.pk)
    else:
        form = OutpatientForm()
    return render(request, "outpatients/outpatient_new.html", {"form": form})


@login_required
def outpatient_edit(request, outpatient_id):
    outpatient = get_object_or_404(Outpatient, pk=outpatient_id)
    if outpatient.created_by_id != request.user.id:
        return HttpResponseForbidden("この発熱外来の編集は許可されていません。")

    if request.method == "POST":
        form = OutpatientForm(request.POST, instance=outpatient)
        if form.is_valid():
            form.save()
            return redirect("outpatient_detail", outpatient_id=outpatient_id)
    else:
        form = OutpatientForm(instance=outpatient)
    return render(request, "outpatients/outpatient_edit.html", {"form": form})


def outpatient_detail(request, outpatient_id):
    outpatient = get_object_or_404(Outpatient, pk=outpatient_id)
    return render(
        request, "outpatients/outpatient_detail.html", {"outpatient": outpatient}
    )
