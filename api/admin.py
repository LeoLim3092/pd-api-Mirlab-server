from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path
from django.contrib import messages
import requests

from .models import Patient, Article, PatientRecord, FileUploaded, Results, PatientQuestionaireRecord

class PatientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')  # Add fields as needed

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('rerun_predictions/', self.admin_site.admin_view(self.rerun_predictions))
        ]
        return custom_urls + urls

    def rerun_predictions(self, request):
        # Modify this URL and token if needed
        url = "http://140.112.91.59:10409/api/rerun_all_predictions"
        token = "<YOUR_JWT_ACCESS_TOKEN>"  # <-- Replace this with a valid access token

        headers = {
            "Authorization": f"Bearer {token}"
        }

        try:
            response = requests.post(url, headers=headers)
            if response.status_code == 200:
                messages.success(request, "✅ Rerun completed successfully.")
            else:
                messages.error(request, f"❌ Failed with status code: {response.status_code}")
        except Exception as e:
            messages.error(request, f"⚠️ Exception occurred: {str(e)}")

        return HttpResponseRedirect("../")  # Redirect back to the patient list

admin.site.register(Patient, PatientAdmin)
admin.site.register(Article)
admin.site.register(PatientRecord)
admin.site.register(FileUploaded)
admin.site.register(Results)
admin.site.register(PatientQuestionaireRecord)
