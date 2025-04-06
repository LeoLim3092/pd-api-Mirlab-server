from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.contrib import messages
from rest_framework_simplejwt.tokens import AccessToken
import requests

from .models import Patient, Article, PatientRecord, FileUploaded, Results, PatientQuestionaireRecord


class PatientAdmin(admin.ModelAdmin):
    change_list_template = "admin/patient_changelist.html"  # Custom template for the list view

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('rerun_predictions/', self.admin_site.admin_view(self.rerun_predictions))
        ]
        return custom_urls + urls

    def rerun_predictions(self, request):
        # Modify this URL if needed
        url = "http://140.112.91.59:10409/api/rerun_all_predictions"

        try:
            # Generate a JWT token for the logged-in user
            token = str(AccessToken.for_user(request.user))

            headers = {
                "Authorization": f"Bearer {token}"
            }

            # Make the POST request to the API
            response = requests.post(url, headers=headers)
            if response.status_code == 200:
                messages.success(request, "✅ Rerun completed successfully.")
            else:
                messages.error(request, f"❌ Failed with status code: {response.status_code}")
        except Exception as e:
            messages.error(request, f"⚠️ Exception occurred: {str(e)}")


        # Redirect to changelist view safely
        changelist_url = reverse('admin:api_patient_changelist')
        return HttpResponseRedirect(changelist_url)


# Register models in the admin site
admin.site.register(Patient, PatientAdmin)
admin.site.register(Article)
admin.site.register(PatientRecord)
admin.site.register(FileUploaded)
admin.site.register(Results)
admin.site.register(PatientQuestionaireRecord)