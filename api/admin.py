from django.contrib import admin
from django.http import (
    HttpResponseRedirect, FileResponse, JsonResponse, HttpResponseBadRequest,
    HttpResponse, StreamingHttpResponse,
)
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
import time
import subprocess
import shutil
from django.core.signing import Signer, BadSignature
from .models import Patient, Article, PatientRecord, FileUploaded, Results, PatientQuestionaireRecord
import logging
from django.contrib.auth.models import Group, User
from rest_framework.authtoken.models import Token
from django.utils.html import format_html
import datetime


logger = logging.getLogger('django')

# Upload media roots (same as api/views base_path)
UPLOAD_MEDIA_ROOT = '/mnt/pd_app'
UPLOAD_SUBFOLDERS = {'gait': 'walk', 'left_hand': 'gesture', 'right_hand': 'gesture', 'sound': 'sound'}

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
# Stream token for video/audio (so <video src="..."> works when cookie isn't sent)
# -----------------------------
STREAM_TOKEN_MAX_AGE = 600  # seconds

def _make_stream_token(request):
    print("[play-media] _make_stream_token: entry")
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        print("[play-media] _make_stream_token: no user or not authenticated, return None")
        return None
    signer = Signer(key=settings.SECRET_KEY)
    payload = {'user_id': request.user.pk, 'exp': int(time.time()) + STREAM_TOKEN_MAX_AGE}
    import json
    token = signer.sign(json.dumps(payload))
    print("[play-media] _make_stream_token: token created for user_id=%s" % request.user.pk)
    return token

def _reencode_mp4_for_browser(src_path, dst_path, timeout=120):
    """Re-encode MP4 to H.264 + AAC with faststart for browser playback. Returns (True, None) or (False, error_msg)."""
    if not shutil.which('ffmpeg'):
        return False, "ffmpeg not installed"
    try:
        cmd = [
            'ffmpeg', '-y', '-i', src_path,
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            '-c:a', 'aac', '-b:a', '128k',
            '-movflags', '+faststart',
            dst_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            return False, (result.stderr or result.stdout or '')[-500:]
        return True, None
    except subprocess.TimeoutExpired:
        return False, "ffmpeg timeout"
    except Exception as e:
        return False, str(e)


def _can_access_stream(request):
    print("[play-media] _can_access_stream: entry")
    if getattr(request, 'user', None) and request.user.is_authenticated and request.user.is_staff:
        print("[play-media] _can_access_stream: allowed by session (staff)")
        return True
    token = (request.GET.get('stream_token') or '').strip()
    print("[play-media] _can_access_stream: stream_token present=%s" % bool(token))
    if not token:
        print("[play-media] _can_access_stream: no token, deny")
        return False
    signer = Signer(key=settings.SECRET_KEY)
    import json
    try:
        data = json.loads(signer.unsign(token))
        print("[play-media] _can_access_stream: token unsigned, exp=%s" % data.get('exp'))
        if data.get('exp', 0) < int(time.time()):
            print("[play-media] _can_access_stream: token expired, deny")
            return False
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.filter(pk=data.get('user_id')).first()
        allowed = user is not None and user.is_staff
        print("[play-media] _can_access_stream: token user_id=%s is_staff=%s => %s" % (data.get('user_id'), getattr(user, 'is_staff', None), allowed))
        return allowed
    except (BadSignature, ValueError, TypeError) as e:
        print("[play-media] _can_access_stream: token invalid (%s), deny" % type(e).__name__)
        return False


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
            path('backend-functions/play-media/', self.admin_view(self.play_media_view), name="play-media"),
            path('backend-functions/play-media/list/', self.admin_view(self.play_media_list_view), name="play-media-list"),
            path('backend-functions/play-media/stream/', self.admin_view(self.play_media_stream_view), name="play-media-stream"),
            path('backend-functions/play-media/reencode/', self.admin_view(self.reencode_media_view), name="play-media-reencode"),
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

    def play_media_view(self, request):
        """Dashboard page to list and play video/audio from results (session auth)."""
        patients = Patient.objects.all().order_by('name')
        context = dict(
            self.each_context(request),
            title="Play Video / Audio",
            patients=patients,
            play_media_list_url=reverse('admin:play-media-list'),
            play_media_stream_url=reverse('admin:play-media-stream'),
            play_media_reencode_url=reverse('admin:play-media-reencode'),
        )
        return TemplateResponse(request, "admin/play_media.html", context)

    def play_media_list_view(self, request):
        """JSON: latest upload per type (gait, left_hand, right_hand, sound) for selected patient."""
        print("[play-media] list_view: entry")
        pid = request.GET.get('pid')
        print("[play-media] list_view: pid=%s" % pid)
        if not pid:
            print("[play-media] list_view: missing pid, 400")
            return JsonResponse({"error": "pid is required"}, status=400)
        try:
            p = Patient.objects.get(patientId=int(pid))
        except (Patient.DoesNotExist, ValueError) as e:
            print("[play-media] list_view: patient not found (%s), 404" % e)
            return JsonResponse({"error": "Patient not found"}, status=404)
        name = p.name
        out = {"patient_name": name, "stream_token": _make_stream_token(request)}

        def latest_for_type(ft):
            qs = FileUploaded.objects.filter(patientId=p, file_type=ft)
            if ft == 'sound':
                qs = qs.exclude(file_path__icontains='freetalk')
            rec = qs.order_by('-upload_time').first()
            if not rec:
                return None
            sub = UPLOAD_SUBFOLDERS.get(ft, '')
            base_dir = os.path.join(UPLOAD_MEDIA_ROOT, sub)
            full = os.path.normpath(os.path.join(base_dir, rec.file_path))
            if not full.startswith(os.path.abspath(base_dir) + os.sep) and full != os.path.abspath(base_dir):
                return None
            has_web = False
            if ft in ('gait', 'left_hand', 'right_hand') and rec.file_path.lower().endswith('.mp4'):
                dir_path = os.path.dirname(full)
                base_name = os.path.splitext(os.path.basename(full))[0]
                web_path = os.path.join(dir_path, base_name + '_web.mp4')
                has_web = os.path.isfile(web_path)
            return {"file_path": rec.file_path, "has_web": has_web}

        for key in ('gait', 'left_hand', 'right_hand', 'sound'):
            out[key] = latest_for_type(key)
        print("[play-media] list_view: returning latest 4 media, stream_token=%s" % bool(out["stream_token"]))
        return JsonResponse(out)

    def reencode_media_view(self, request):
        """Re-encode patient's latest upload videos (gait, left_hand, right_hand) to H.264 in same folder. POST with pid."""
        if request.method != 'POST':
            return JsonResponse({"error": "POST required"}, status=405)
        pid = request.POST.get('pid') or request.GET.get('pid')
        if not pid and request.body:
            try:
                import json as _json
                data = _json.loads(request.body.decode())
                pid = data.get('pid') or pid
            except Exception:
                pass
        if not pid:
            return JsonResponse({"error": "pid is required"}, status=400)
        try:
            p = Patient.objects.get(patientId=int(pid))
        except (Patient.DoesNotExist, ValueError):
            return JsonResponse({"error": "Patient not found"}, status=404)
        encoded = 0
        skipped = 0
        failed = []
        for media_type in ('gait', 'left_hand', 'right_hand'):
            rec = FileUploaded.objects.filter(patientId=p, file_type=media_type).order_by('-upload_time').first()
            if not rec or not rec.file_path.lower().endswith('.mp4'):
                continue
            sub = UPLOAD_SUBFOLDERS.get(media_type, '')
            base_dir = os.path.join(UPLOAD_MEDIA_ROOT, sub)
            src = os.path.normpath(os.path.join(base_dir, rec.file_path))
            if not os.path.isfile(src):
                failed.append({"file": rec.file_path, "error": "file not found"})
                continue
            dir_path = os.path.dirname(src)
            base_name = os.path.splitext(os.path.basename(src))[0]
            web_name = base_name + '_web.mp4'
            dst = os.path.join(dir_path, web_name)
            if os.path.isfile(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
                skipped += 1
                continue
            ok, err = _reencode_mp4_for_browser(src, dst)
            if ok:
                encoded += 1
            else:
                failed.append({"file": rec.file_path, "error": (err or "unknown")[:200]})
        return JsonResponse({
            "encoded": encoded,
            "skipped": skipped,
            "failed": failed,
            "message": "Encoded %d, skipped %d, failed %d" % (encoded, skipped, len(failed)),
        })

    def play_media_stream_view(self, request):
        """Stream a single file: from upload (source=upload, pid, type) or from results (folder_name, file_name)."""
        print("[play-media] stream_view: entry")
        from .views import RESULTS_MEDIA_ROOT, _content_type_for_file
        if not _can_access_stream(request):
            print("[play-media] stream_view: access denied, redirect to login")
            return HttpResponseRedirect(reverse('admin:login') + '?next=' + request.get_full_path())
        print("[play-media] stream_view: access OK")

        source = (request.GET.get('source') or '').strip().lower()
        if source == 'upload':
            pid = request.GET.get('pid', '').strip()
            media_type = (request.GET.get('type') or '').strip().lower()
            prefer_web = request.GET.get('prefer_web', '1') == '1'
            if not pid or media_type not in ('gait', 'left_hand', 'right_hand', 'sound'):
                return HttpResponseBadRequest("source=upload requires pid and type (gait|left_hand|right_hand|sound)")
            try:
                p = Patient.objects.get(patientId=int(pid))
            except (Patient.DoesNotExist, ValueError):
                return JsonResponse({"error": "Patient not found"}, status=404)
            qs = FileUploaded.objects.filter(patientId=p, file_type=media_type)
            if media_type == 'sound':
                qs = qs.exclude(file_path__icontains='freetalk')
            rec = qs.order_by('-upload_time').first()
            if not rec:
                return JsonResponse({"error": "No upload for this type"}, status=404)
            sub = UPLOAD_SUBFOLDERS.get(media_type, '')
            base_dir = os.path.abspath(os.path.join(UPLOAD_MEDIA_ROOT, sub))
            full_path = os.path.normpath(os.path.join(base_dir, rec.file_path))
            if not full_path.startswith(base_dir + os.sep) and full_path != base_dir:
                return HttpResponseBadRequest("Invalid path")
            if media_type != 'sound' and prefer_web and rec.file_path.lower().endswith('.mp4'):
                dir_path = os.path.dirname(full_path)
                base_name = os.path.splitext(os.path.basename(full_path))[0]
                web_path = os.path.join(dir_path, base_name + '_web.mp4')
                if os.path.isfile(web_path):
                    full_path = web_path
        else:
            folder_name = (request.GET.get('folder_name') or '').strip()
            file_name = (request.GET.get('file_name') or '').strip()
            print("[play-media] stream_view: folder_name=%r file_name=%r" % (folder_name[:50] if len(folder_name) > 50 else folder_name, file_name[:50] if len(file_name) > 50 else file_name))
            if not file_name or not folder_name:
                print("[play-media] stream_view: missing folder_name or file_name, 400")
                return HttpResponseBadRequest("folder_name and file_name are required")
            if '..' in file_name or '..' in folder_name or '\\' in file_name or '/' in file_name:
                print("[play-media] stream_view: invalid path chars, 400")
                return HttpResponseBadRequest("Invalid path")
            root = os.path.abspath(RESULTS_MEDIA_ROOT)
            full_path = os.path.normpath(os.path.join(root, folder_name, file_name))
            print("[play-media] stream_view: root=%s full_path=%s" % (root, full_path))
            if not full_path.startswith(root + os.sep) and full_path != root:
                print("[play-media] stream_view: path outside root, 400")
                return HttpResponseBadRequest("Invalid path")

        file_name_for_ct = os.path.basename(full_path)
        if not os.path.isfile(full_path):
            print("[play-media] stream_view: file not found, 404")
            return JsonResponse({"error": "File not found"}, status=404)
        content_type = _content_type_for_file(file_name_for_ct)
        file_size = os.path.getsize(full_path)
        range_header = request.META.get('HTTP_RANGE', '').strip()
        print("[play-media] stream_view: content_type=%s file_size=%s HTTP_RANGE=%r" % (content_type, file_size, range_header[:50] if range_header else ''))
        if range_header.startswith('bytes='):
            # Parse "bytes=start-end" (end can be missing = until end of file)
            try:
                parts = range_header[6:].split('-')
                start = int(parts[0]) if parts[0] else 0
                end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1
                if start < 0 or start >= file_size or end >= file_size or end < start:
                    start, end = 0, file_size - 1
            except (ValueError, IndexError):
                start, end = 0, file_size - 1
            length = end - start + 1
            print("[play-media] stream_view: Range 206 start=%s end=%s length=%s" % (start, end, length))
            with open(full_path, 'rb') as f:
                f.seek(start)
                data = f.read(length)
            response = HttpResponse(data, status=206, content_type=content_type)
            response['Content-Range'] = 'bytes %d-%d/%d' % (start, end, file_size)
            response['Content-Length'] = str(len(data))
            response['Accept-Ranges'] = 'bytes'
            print("[play-media] stream_view: returning 206")
            return response
        # No Range: stream file in chunks so WSGI never sees a closed file handle.
        print("[play-media] stream_view: no Range, streaming full file")
        def _stream_file():
            with open(full_path, 'rb') as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    yield chunk
        response = StreamingHttpResponse(_stream_file(), content_type=content_type)
        response['Content-Length'] = str(file_size)
        response['Accept-Ranges'] = 'bytes'
        print("[play-media] stream_view: returning 200 StreamingHttpResponse")
        return response

    

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
