from django.contrib import admin

from outpatients.models import Location, Outpatient

admin.site.register(Outpatient)
admin.site.register(Location)
