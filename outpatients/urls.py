from django.urls import path

from outpatients import views

urlpatterns = [
    path("new/", views.outpatient_new, name="outpatient_new"),
    path("<int:outpatient_id>/", views.outpatient_detail, name="outpatient_detail"),
    path("<int:outpatient_id>/edit/", views.outpatient_edit, name="outpatient_edit"),
]
