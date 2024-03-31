from django import forms

from outpatients.models import Outpatient


class OutpatientForm(forms.ModelForm):
    class Meta:
        model = Outpatient
        fields = (
            "is_outpatient",
            "is_positive_patients",
            "medical_institution_name",
            "public_health_care_center",
            "medical_institution_name",
            "city",
            "address",
            "phone_number",
            "is_target_not_family",
            "is_pediatrics",
            "mon",
            "tue",
            "wed",
            "thu",
            "fri",
            "sat",
            "sun",
            "is_face_to_face_for_positive_patients",
            "is_online_for_positive_patients",
            "is_home_visitation_for_positive_patients",
            "memo",
        )
