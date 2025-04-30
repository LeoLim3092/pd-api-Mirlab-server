from django.contrib import admin
from django.http import HttpResponseRedirect, FileResponse
from django.urls import path, reverse
from django.contrib import messages
from django.template.response import TemplateResponse
from django.conf import settings
from django import forms
from rest_framework_simplejwt.tokens import AccessToken
import requests
import zipfile
import io
import os
from .models import Patient, Article, PatientRecord, FileUploaded, Results, PatientQuestionaireRecord
import logging
from django.contrib.auth.models import Group, User
from rest_framework.authtoken.models import Token
from django.utils.html import format_html
import datetime


logger = logging.getLogger('django')

# Mapping between file_type and base folder
FILE_TYPE_STORAGE_PATHS = {
    'sound': '/mnt/pd_app/sound',
    'gait': '/mnt/pd_app/walk',
    'right_hand': '/mnt/pd_app/gesture',
    'left_hand': '/mnt/pd_app/gesture',
    'spiral_paint':  [
        '/mnt/pd_app/paint/spiral/right',
        '/mnt/pd_app/paint/spiral/left'
    ],
    'three': '/mnt/pd_app/paint/three/right',
    'questionnaires': '/mnt/pd_app/results',  # or if you save JSON here
}

# -----------------------------
# Custom Admin Site
# -----------------------------

class CustomAdminSite(admin.AdminSite):
    site_header = "My Admin Dashboard"
    site_title = "Admin Portal"
    index_title = "Welcome to the Backend Control Panel"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('backend-functions/', self.admin_view(self.backend_functions_view), name="backend-functions"),
            path('backend-functions/rerun-predictions/', self.admin_view(self.rerun_predictions), name="rerun-predictions"),
            path('backend-functions/download-data/', self.admin_view(self.download_data_view), name="download-data"),
            path('backend-functions/view-logs/', self.admin_view(self.view_logs_view), name="view-logs"),
            path('api/patient/<int:patient_id>/rerun/', self.admin_view(self.rerun_single_patient), name="rerun-patient"),
        
            # (you can add more backend function URLs here)
        ]
        return custom_urls + urls

    def backend_functions_view(self, request):
        context = dict(
            self.each_context(request),
            title='Backend Functions',
        )
        return TemplateResponse(request, "admin/backend_functions.html", context)

    def rerun_predictions(self, request):
        url = "http://140.112.91.59:10409/api/rerun_all_predictions"

        try:
            token = str(AccessToken.for_user(request.user))
            headers = {
                "Authorization": f"Bearer {token}"
            }

            response = requests.post(url, headers=headers)
            if response.status_code == 200:
                messages.success(request, "✅ Rerun completed successfully.", level='SUCCESS')
            else:
                messages.error(request, f"❌ Failed with status code: {response.status_code}", level='ERROR')
        except Exception as e:
           messages.error(request, f"⚠️ Exception occurred: {str(e)}", level='ERROR')

        return HttpResponseRedirect(reverse('admin:backend-functions'))
    

    def rerun_single_patient(self, request, patient_id):
        try:
            url = "http://140.112.91.59:10409/api/predict_without_model_extraction"

            token = str(AccessToken.for_user(request.user))
            headers = {
                "Authorization": f"Bearer {token}"
            }

            response = requests.post(url, data={"pid": patient_id}, headers=headers)

            if response.status_code == 200:
                messages.success(request, f"✅ Prediction rerun for patient {patient_id}.")
            else:
                messages.error(request, f"❌ Prediction failed. Status: {response.status_code}")
        except Exception as e:
            messages.error(request, f"❌ Error running prediction: {e}")

        return HttpResponseRedirect(reverse('admin:api_patient_changelist'))

    
    def download_data_view(self, request):
        if request.method == 'POST':
            form = DownloadDataForm(request.POST)
            if form.is_valid():
                from_date = form.cleaned_data['from_date']
                to_date = form.cleaned_data['to_date']
                data_type = form.cleaned_data['data_type']

                base_dirs = FILE_TYPE_STORAGE_PATHS.get(data_type, [])
                if not base_dirs:
                    messages.error(request, f"⚠️ Unknown data type: {data_type}")
                    return redirect('admin:download-data')

                if isinstance(base_dirs, str):
                    base_dirs = [base_dirs]

                from_ts = datetime.datetime.combine(from_date, datetime.time.min).timestamp()
                to_ts = datetime.datetime.combine(to_date, datetime.time.max).timestamp()

                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for base_dir in base_dirs:
                        for root, _, files in os.walk(base_dir):
                            for fname in files:
                                fpath = os.path.join(root, fname)
                                if is_valid_file(fpath, from_ts, to_ts):
                                    arcname = os.path.relpath(fpath, base_dir)
                                    zip_file.write(fpath, arcname=arcname)

                zip_buffer.seek(0)
                return FileResponse(
                    zip_buffer,
                    as_attachment=True,
                    filename=f"{data_type}_files_{from_date}_to_{to_date}.zip"
                )

        else:
            form = DownloadDataForm()

        context = dict(
            self.each_context(request),
            title="Download Data",
            form=form
        )
        return TemplateResponse(request, "admin/download_data.html", context)


    def view_logs_view(self, request):
        log_file_path = os.path.join(settings.BASE_DIR, 'django.log')

        if not os.path.exists(log_file_path):
            messages.error(request, "Log file not found.")
            return HttpResponseRedirect(reverse('admin:backend-functions'))

        with open(log_file_path, 'r') as f:
            log_content = f.readlines()[-200:]  # only show last 200 lines (for speed)

        context = dict(
            self.each_context(request),
            title="Server Logs",
            log_content=log_content,
        )
        return TemplateResponse(request, "admin/view_logs.html", context)

    

class DownloadDataForm(forms.Form):
    from_date = forms.DateField(label="From Date", widget=forms.DateInput(attrs={'type': 'date'}))
    to_date = forms.DateField(label="To Date", widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        file_type_choices = FileUploaded.objects.values_list('file_type', 'file_type').distinct()
        self.fields['data_type'] = forms.ChoiceField(label="Data Type", choices=file_type_choices)


# Instantiate the custom admin site
admin_site = CustomAdminSite(name='custom_admin')

# -----------------------------
# Model Admins
# -----------------------------

@admin.register(Patient, site=admin_site)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('patientId', 'name', 'rerun_button')

    def rerun_button(self, obj):
        url = reverse('admin:rerun-patient', args=[obj.patientId])
        return format_html('<a class="button" href="{}">Rerun Prediction</a>', url)

    rerun_button.short_description = 'Actions'
    
def is_valid_file(path, from_ts, to_ts):
    try:
        stat = os.stat(path)
        return from_ts <= stat.st_ctime <= to_ts
    except Exception:
        return False  # Skip problematic files

# Register other models to the custom admin site
admin_site.register(Article)
admin_site.register(PatientRecord)
admin_site.register(FileUploaded)
admin_site.register(Results)
admin_site.register(PatientQuestionaireRecord)

admin_site.register(Group)
admin_site.register(User)
admin_site.register(Token)
