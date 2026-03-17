import os
import asyncio
import json
import threading
import datetime
import csv

from .pdModel.deployModel import features_extraction, extract_gait, extract_hand, predict_models, data_checking

from django.shortcuts import render, redirect
from django.contrib.auth.models import User, Group
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, FileResponse, JsonResponse
from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.storage import default_storage
from django.core.files.storage import FileSystemStorage
from django.db.models import Max
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.views import View

from api.models import PatientSerializer
from .models import PatientRecord, Patient, FileUploaded, Results, PatientQuestionaireRecord, Article

from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from datetime import timedelta


print(settings.MEDIA_ROOT, settings.MEDIA_URL)

base_path = '/mnt/pd_app'
gaitlandmark_pth = base_path + "/" + "gaitLandmarks/"
handlandmark_pth = base_path + "/" + "handLandmarks/"
sound_storage = FileSystemStorage(location=f'{base_path}/sound')
walk_storage = FileSystemStorage(location=f'{base_path}/walk')
gesture_storage = FileSystemStorage(location=f'{base_path}/gesture')
paint_spiral_right_storage = FileSystemStorage(location=f'{base_path}/paint/spiral/right')
paint_spiral_left_storage = FileSystemStorage(location=f'{base_path}/paint/spiral/left')
paint_three_right_storage = FileSystemStorage(location=f'{base_path}/paint/three/right')
paint_three_left_storage = FileSystemStorage(location=f'{base_path}/paint/three/left')

result_storage = FileSystemStorage(location=f'{base_path}/results')


# Create your views here.
class MedicalStaffLogin(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request: WSGIRequest):
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is None:
            return HttpResponseBadRequest()

        # Check if the user is in the "Staff" group
        if user.groups.filter(name='MedicalStaff').exists():
            ans = get_tokens_for_user(user)
            ans = json.dumps(ans, indent=4)
            return HttpResponse(ans)
        else:
            # User is not in the "Staff" group, return an error message
            return JsonResponse({'message': 'Unauthorized.'}, status=401)


class Login(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request: WSGIRequest):
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is None:
            return HttpResponseBadRequest()

        ans = get_tokens_for_user(user)
        ans = json.dumps(ans, indent=4)
        return HttpResponse(ans)


class UploadSound(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request: WSGIRequest):

        file = request.FILES['file']
        pid = request.POST["pid"]
        format = '%Y-%m-%d %H:%M:%S'
        time = datetime.datetime.now().strftime(format)
        current_pid = Patient.objects.get(patientId=int(pid))
        patient = current_pid.name

        file_path = sound_storage.save(time + "_sound_" + patient + '_' + pid + '_' + file.name, file)
        file = FileUploaded(patientId = current_pid, patient=patient, file_type='sound', file_path=file_path)
        file.save()

        return HttpResponse()


class UploadPaint(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request: WSGIRequest):
        pid = request.POST["pid"]
        file = request.FILES['file']
        type = request.POST['type']
        
        try:
            coordinates = request.POST['coordinates']
            coordinates_data = json.loads(coordinates)
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid Json format")
        
        format = '%Y-%m-%d %H:%M:%S'
        time = datetime.datetime.now().strftime(format)

        current_pid = Patient.objects.get(patientId = int(pid))
        patient = current_pid.name

        if type == 'spiral_right':
            file_path = paint_spiral_right_storage.save(time + "_spiral_right_" + patient + '_' + '_' + pid + '_' + file.name, file)
            file = FileUploaded(patientId=current_pid, patient=patient, file_type='spiral_paint', file_path=file_path)
            file.save()
            
            # Save coordinates as JSON file
            json_filename = os.path.splitext(file_path)[0] + '.json'
            json_path = os.path.join(paint_spiral_right_storage.location, os.path.basename(json_filename))

            with open(json_path, 'w') as json_file:
                json.dump(coordinates_data, json_file)
            
        elif type == 'spiral_left':
            file_path = paint_spiral_left_storage.save(time + "_spiral_left_" + patient + '_' + '_' + pid + '_' + file.name, file)
            file = FileUploaded(patientId=current_pid, patient=patient, file_type='spiral_paint', file_path=file_path)
            file.save()
            
            # Save coordinates as JSON file
            json_filename = os.path.splitext(file_path)[0] + '.json'
            json_path = os.path.join(paint_spiral_left_storage.location, os.path.basename(json_filename))

            with open(json_path, 'w') as json_file:
                json.dump(coordinates_data, json_file)
                
        elif type == 'three':
            file_path = paint_three_right_storage.save(time + "_three_right_" + patient + '_' + '_' + pid + '_' + file.name, file)
            file = FileUploaded(patientId=current_pid, patient=patient, file_type='three', file_path=file_path)
            file.save()
            
            # Save coordinates as JSON file
            json_filename = os.path.splitext(file_path)[0] + '.json'
            json_path = os.path.join(paint_three_right_storage.location, os.path.basename(json_filename))

            with open(json_path, 'w') as json_file:
                json.dump(coordinates_data, json_file)
                
        elif type == 'three_left':
            file_path = paint_three_left_storage.save(time + "_three_left_" + patient + '_' + '_' + pid + '_' + file.name, file)
            file = FileUploaded(patientId=current_pid, patient=patient, file_type='three_paint', file_path=file_path)
            file.save()
            
            # Save coordinates as JSON file
            json_filename = os.path.splitext(file_path)[0] + '.json'
            json_path = os.path.join(paint_three_left_storage.location, os.path.basename(json_filename))

            with open(json_path, 'w') as json_file:
                json.dump(coordinates_data, json_file)
        else:
            return HttpResponseBadRequest(f"Unknown paint type: {type}")

        print(json_path)

        return HttpResponse()


class UploadWalk(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request: WSGIRequest):
        file_obj = request.FILES['file']
        pid = request.POST["pid"]

        time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        current_pid = Patient.objects.get(patientId=int(pid))
        patient = current_pid.name

        file_name = f"{time_str}_walk_{patient}_{pid}_{file_obj.name}"
        file_path = walk_storage.save(file_name, file_obj)

        uploaded = FileUploaded(
            patientId=current_pid,
            patient=patient,
            file_type='gait',
            file_path=file_path
        )
        uploaded.save()

        full_file_path = os.path.join(base_path, "walk", file_path)

        threading.Thread(
            target=extract_gait,
            args=(full_file_path, gaitlandmark_pth),
            daemon=True
        ).start()

        return HttpResponse()


class UploadGesture(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request: WSGIRequest):
        file_obj = request.FILES['file']
        pid = request.POST["pid"]
        hand_type = request.POST['type']

        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        current_pid = Patient.objects.get(patientId=int(pid))
        patient = current_pid.name

        file_name = f"{now_str}_gesture_{patient}_{pid}_{hand_type}_{file_obj.name}"
        file_path = gesture_storage.save(file_name, file_obj)
        full_file_path = os.path.join(base_path, "gesture", file_path)

        if hand_type == '右手':
            side = 'right'
            file_type = 'right_hand'
        else:
            side = 'left'
            file_type = 'left_hand'

        uploaded = FileUploaded(
            patientId=current_pid,
            patient=patient,
            file_type=file_type,
            file_path=file_path
        )
        uploaded.save()

        threading.Thread(
            target=extract_hand,
            args=(full_file_path, handlandmark_pth, side),
            daemon=True
        ).start()
        
        return HttpResponse()
    

class UploadMedicineRecord(APIView):

    def post(self, request: WSGIRequest):
        medicine_taken = request.POST["medicine"]
        medicine_taken_3hr = request.POST["medicine_3hr"]
        pid = request.POST["pid"]
        format = '%Y-%m-%d %H:%M:%S'
        time = datetime.datetime.now().strftime(format)
        current_pid = Patient.objects.get(patientId=int(pid))
        # Convert POST strings to bool for BooleanField
        taking_pd = str(medicine_taken).lower() in ('true', '1', 'yes')
        taking_pd_3hr = str(medicine_taken_3hr).lower() in ('true', '1', 'yes')
        pr = PatientRecord(
            patientId=current_pid,
            time=time,
            taking_pd_medicine=taking_pd,
            taking_pd_med3hr=taking_pd_3hr,
        )
        pr.save()
        return HttpResponse()


class UploadQuestionaireRecord(APIView):

    def post(self, request: WSGIRequest):
        pid = request.POST["pid"]
        format = '%Y-%m-%d %H:%M:%S'
        time = datetime.datetime.now().strftime(format)
        riskMarker = request.POST["riskMarker"]
        PLR = request.POST["PLR"]
        TELR = request.POST["TELR"]
        PostProb = request.POST["PostProb"]
        PPPD = request.POST["PPPD"]
        response = request.POST["response"]
        current_pid = Patient.objects.get(patientId=int(pid))
        try:
            riskMarker_f = float(riskMarker)
            PLR_f = float(PLR)
            TELR_f = float(TELR)
            PostProb_f = float(PostProb)
        except (TypeError, ValueError):
            riskMarker_f = PLR_f = TELR_f = PostProb_f = 0.0
        qr = PatientQuestionaireRecord(
            patientId=current_pid,
            time=time,
            riskMarker=riskMarker_f,
            PLR=PLR_f,
            TELR=TELR_f,
            PostProb=PostProb_f,
            PPPD=PPPD,
            response=response,
        )
        qr.save()
        return HttpResponse()


class CreateNewPatient(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request: WSGIRequest):
        patient_name = request.POST['name']
        user_name = request.POST['user_name']
        patient_gender = request.POST["gender"]
        patient_age = request.POST["age"]
        patient_email = request.POST["email"]
        patient_birthday = request.POST["birthday"]
        phone_no = request.POST["phone_no"]
        id_no = request.POST["id_no"]
        
        # Assign next patientId (Patient has IntegerField primary key with no auto-generation)
        next_id = (Patient.objects.aggregate(m=Max('patientId'))['m'] or 0) + 1
        try:
            gender_int = int(patient_gender)
        except (TypeError, ValueError):
            gender_int = 0
        p = Patient(
            patientId=next_id,
            name=patient_name,
            user_name=user_name,
            gender=gender_int,
            age=int(patient_age),
            birthday=patient_birthday,
            email=patient_email,
            phone_no=phone_no,
            id_no=id_no,
        )
        p.save()
        return HttpResponse()


class GoogleLogin(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request: WSGIRequest):
        
        path = "https://www.googleapis.com/oauth2/v1/tokeninfo?access_token="
        import requests as rq
        res = rq.get(path + request.POST['token'])
        js = res.json()
        email = js["email"]
        email_local, email_domain = email.split("@", 1)
        # User model does not enforce unique email; use filter to avoid MultipleObjectsReturned
        user = User.objects.filter(email=email).first()
        if user is None:
            user = User.objects.create_user(username=email_local, email=email)
        elif not user.username or user.username == "":
            user.username = email_local
            user.save()
        
        if email_domain == 'ntu.edu.tw':
            group = Group.objects.get(name='MedicalStaff')
            user.groups.add(group)
        
        user.save()
        ans = get_tokens_for_user(user)
        ans["username"] = user.username
        ans = json.dumps(ans, indent=4)
        return HttpResponse(ans)


class CreateNewUser(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request: WSGIRequest):
        user_name = request.POST['user_name']
        user_pw = request.POST['user_pw']
        user_email = request.POST['user_email']
        if user_name != "" and user_pw != "":
            if User.objects.filter(username=user_name).exists():
                return JsonResponse({'errors': '使用者名稱已經被使用'}, status=401)
            # todo check password str
            user = User.objects.create_user(user_name, email=user_email, password=user_pw)
            user.save()
            return JsonResponse({'message': 'User created successfully'})
        else:
            return HttpResponseBadRequest()


class CheckRecording(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request: WSGIRequest):
        pid = request.POST['pid']
        format = '%Y-%m-%d_%H:%M:%S'
        current_time = datetime.datetime.now().strftime(format)

        p = Patient.objects.get(patientId=int(pid))
        name = p.name

        r_hand_file = FileUploaded.objects.filter(patientId=p, file_type='right_hand').order_by('-upload_time').first()
        l_hand_file = FileUploaded.objects.filter(patientId=p, file_type='left_hand').order_by('-upload_time').first()
        gait_file = FileUploaded.objects.filter(patientId=p, file_type='gait').order_by('-upload_time').first()
        sound_file = FileUploaded.objects.filter(patientId=p, file_type='sound').order_by('-upload_time').first()

        if not all([r_hand_file, l_hand_file, gait_file, sound_file]):
            missing = []
            if not r_hand_file:
                missing.append("right_hand")
            if not l_hand_file:
                missing.append("left_hand")
            if not gait_file:
                missing.append("gait")
            if not sound_file:
                missing.append("sound")
            return JsonResponse(
                {"success": "failed", "error": f"Missing required uploads: {', '.join(missing)}."},
                status=400
            )

        results_dir = f'/mnt/pd_app/results/{name}/'
        os.makedirs(results_dir, exist_ok=True)
        os.makedirs(f'{results_dir}{current_time}/', exist_ok=True)

        gait_file_pth = f'{base_path}/walk/{gait_file.file_path}'
        l_hand_file_pth = f'{base_path}/gesture/{l_hand_file.file_path}'
        r_hand_file_pth = f'{base_path}/gesture/{r_hand_file.file_path}'
        sound_file_pth = f'{base_path}/sound/{sound_file.file_path}'

        try:
            success, error = data_checking(gait_file_pth, l_hand_file_pth, r_hand_file_pth, sound_file_pth)
            return JsonResponse({"success": success, "error": error})
        
        except Exception:
            error_message = "Failed to process data"
            return Response({"error": error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class PredictWithoutModelExtraction(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request: WSGIRequest):
        
        pid = request.POST.get('pid') or request.data.get('pid')
        if not pid:
            return HttpResponseBadRequest("Missing 'pid'")
        
        p = Patient.objects.get(patientId=int(pid))
        age = p.age
        gender = p.gender
        name = p.name
        format = '%Y-%m-%d_%H:%M:%S'
        current_time = datetime.datetime.now().strftime(format)
        
        out_dir = f'/mnt/pd_app/results/{name}/'
        latest_folder = get_latest_folder_by_creation_time(out_dir)
        if not latest_folder:
            return Response(
                {"error": "No previous extraction found. Run full prediction first."},
                status=status.HTTP_400_BAD_REQUEST
            )
        lastest_extracted_npy = os.path.join(latest_folder, "all_feature.npy")
        
        try:
            gait_result, hand_result, voice_results, all_results = predict_models(lastest_extracted_npy, age, gender)
            r = Results(patientId=p, patient=name, gait_result=gait_result, voice_result=voice_results,
                        hand_result=hand_result, multimodal_results=all_results, upload_time=current_time)
            r.save()
            return HttpResponse()
        except Exception as e:
            error_message = "Failed to process data"
            return Response({"error": error_message, "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class PredictModel(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request: WSGIRequest):

        pid = request.POST['pid']

        try:
            print("Running model prediction!")
            run_predict_model(pid)
            return HttpResponse()

        except Exception as e:
            return JsonResponse(
                {"error": str(e)},
                status=500
            )


class GetResults(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    print(authentication_classes, permission_classes)

    def post(self, request: WSGIRequest):
        pid = request.POST['pid']
        p = Patient.objects.get(patientId=int(pid))
        try:
            threshold_article = Article.objects.get(title="Theresholds")  # DB title kept for backwards compatibility
            thre = threshold_article.content.split(", ")
        except Article.DoesNotExist:
            thre = []
        name = p.name
        latest_results = Results.objects.filter(patientId=p).order_by('-upload_time').first()
        if latest_results:
            upload_time = " ".join(latest_results.upload_time.split("_"))
            gait_result = str(round(float(latest_results.gait_result), 2))
            voice_result = str(round(float(latest_results.voice_result), 2))
            hand_result = str(round(float(latest_results.hand_result), 2))
            all_result = str(round(float(latest_results.multimodal_results), 2))
            
            return JsonResponse({"pid": pid, "patient":name, 'upload_time':upload_time, 'gait': gait_result, 'voice': voice_result,
                                 'hand':hand_result, "all":all_result, "thre":thre})
        else:
            return HttpResponseBadRequest("Previous result doesn't exist!", status=401)


# Base path for results media (videos, audio, images). Use /mnt/results if you mount it there.
RESULTS_MEDIA_ROOT = os.environ.get('RESULTS_MEDIA_ROOT', '/mnt/pd_app/results')

# Content-Type by file extension for streaming media in the frontend
MEDIA_CONTENT_TYPES = {
    'mp4': 'video/mp4',
    'webm': 'video/webm',
    'mov': 'video/quicktime',
    'wav': 'audio/wav',
    'mp3': 'audio/mpeg',
    'm4a': 'audio/mp4',
    'ogg': 'audio/ogg',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'gif': 'image/gif',
}


def _get_media_params(request):
    """Get folder_name and file_name from GET or POST."""
    if request.method == 'GET':
        folder_name = (request.GET.get('folder_name') or '').strip()
        file_name = (request.GET.get('file_name') or '').strip()
    else:
        folder_name = (request.POST.get('folder_name') or request.data.get('folder_name') or '').strip()
        file_name = (request.POST.get('file_name') or request.data.get('file_name') or '').strip()
    return folder_name, file_name


def _content_type_for_file(file_name):
    ext = (file_name.rsplit('.', 1) + [''])[1].lower()
    return MEDIA_CONTENT_TYPES.get(ext, 'application/octet-stream')


class getVideo(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request: WSGIRequest):
        """GET with ?folder_name=...&file_name=... for use with fetch + blob URL in frontend."""
        folder_name, file_name = _get_media_params(request)
        return _serve_media_file(folder_name, file_name, request)

    def post(self, request: WSGIRequest):
        folder_name, file_name = _get_media_params(request)
        return _serve_media_file(folder_name, file_name, request)


def _serve_media_file(folder_name, file_name, request=None):
    """Serve file with optional Range support so video/audio elements can load."""
    if not file_name or not folder_name:
        return HttpResponseBadRequest("folder_name and file_name are required")
    if '..' in file_name or '..' in folder_name or '\\' in file_name:
        return HttpResponseBadRequest("Invalid file or folder name")
    if '/' in file_name:
        return HttpResponseBadRequest("file_name must not contain path separators")
    root = os.path.abspath(RESULTS_MEDIA_ROOT)
    full_path = os.path.normpath(os.path.join(root, folder_name, file_name))
    if not full_path.startswith(root + os.sep) and full_path != root:
        return HttpResponseBadRequest("Invalid path")
    if not os.path.isfile(full_path):
        return JsonResponse({"error": "File not found"}, status=404)
    content_type = _content_type_for_file(file_name)
    file_size = os.path.getsize(full_path)
    range_header = (request.META.get('HTTP_RANGE', '') if request else '').strip()
    if range_header.startswith('bytes='):
        try:
            parts = range_header[6:].split('-')
            start = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1
            if start < 0 or start >= file_size or end >= file_size or end < start:
                start, end = 0, file_size - 1
        except (ValueError, IndexError):
            start, end = 0, file_size - 1
        length = end - start + 1
        with open(full_path, 'rb') as f:
            f.seek(start)
            data = f.read(length)
        response = HttpResponse(data, status=206, content_type=content_type)
        response['Content-Range'] = 'bytes %d-%d/%d' % (start, end, file_size)
        response['Content-Length'] = str(len(data))
        response['Accept-Ranges'] = 'bytes'
        return response
    with open(full_path, 'rb') as f:
        response = FileResponse(f, content_type=content_type)
    response['Accept-Ranges'] = 'bytes'
    response['Content-Length'] = file_size
    return response


class getMedia(APIView):
    """Serve video/audio/image from results. Supports GET and Range for playback after login."""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request: WSGIRequest):
        folder_name, file_name = _get_media_params(request)
        return _serve_media_file(folder_name, file_name, request)

    def post(self, request: WSGIRequest):
        folder_name, file_name = _get_media_params(request)
        return _serve_media_file(folder_name, file_name, request)


class listResultMedia(APIView):
    """List result folders and files for a patient so frontend can build video/audio list."""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request: WSGIRequest):
        pid = request.GET.get('pid')
        if not pid:
            return JsonResponse({"error": "pid is required"}, status=400)
        p = get_object_or_404(Patient, patientId=int(pid))
        name = p.name
        root = os.path.abspath(os.path.join(RESULTS_MEDIA_ROOT, name))
        if not os.path.isdir(root):
            return JsonResponse({"folders": [], "patient_name": name})
        folders = []
        for entry in sorted(os.listdir(root)):
            path = os.path.join(root, entry)
            if not os.path.isdir(path):
                continue
            files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
            folders.append({"folder": entry, "files": sorted(files)})
        return JsonResponse({"patient_name": name, "folders": folders})


class getUserData(View):

    def get(self, request):
        user_name = request.GET.get('user_name')
        print(user_name)

        if user_name:
            patient = get_object_or_404(Patient, user_name=user_name)
            serializer = PatientSerializer(patient)
            data = serializer.data
            print(data)
            return JsonResponse(data, safe=False)
        else:
            return HttpResponseBadRequest("Username doesn't exist!", status=401)

    def post(self, request):
        user_name = request.POST.get('user_name')
        print(user_name)

        if user_name:
            patient = get_object_or_404(Patient, user_name=user_name)
            serializer = PatientSerializer(patient)
            data = serializer.data
            print(data)
            return JsonResponse(data, safe=False)
        else:
            return HttpResponseBadRequest("Username doesn't exist!", status=401)


class RerunAllPatientPredictModel(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request: WSGIRequest):

        patients = Patient.objects.all()
        failed_patients = []

        for patient in patients:
            try:
                run_predict_model(patient.patientId, save_result=False)

            except Exception as e:
                failed_patients.append({
                    "patientId": patient.patientId,
                    "reason": str(e)
                })

        return JsonResponse({
            "message": "Rerun completed",
            "failed_patients": failed_patients
        })


class RerunFromDatePatientPrediction(APIView):
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]

    def post(self, request: WSGIRequest):
        # Get the date from the request
        date_str = request.POST.get('date', None)
        if not date_str:
            return JsonResponse({"error": "Date is required in the format YYYY-MM-DD"}, status=400)

        try:
            # Parse the date
            from_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({"error": "Invalid date format. Use YYYY-MM-DD."}, status=400)

        # Fetch patients created on or after the given date
        patients = Patient.objects.filter(created_at__date__gte=from_date)
        failed_patients = []

        for patient in patients:
            try:
                run_predict_model(patient.patientId, save_result=False)

            except Exception as e:
                # Log the failure for this patient
                failed_patients.append({
                    "patientId": patient.patientId,
                    "reason": str(e)
                })

        # Return a summary of the operation
        return JsonResponse({
            "message": "Rerun completed",
            "failed_patients": failed_patients
        })


class getLastUploadData(APIView):

    def post(self, request):
        pid = request.POST['pid']

        p = Patient.objects.get(patientId=int(pid))

        r_hand_file = FileUploaded.objects.filter(patientId=p, file_type='right_hand').order_by('-upload_time').first()
        l_hand_file = FileUploaded.objects.filter(patientId=p, file_type='left_hand').order_by('-upload_time').first()
        gait_file = FileUploaded.objects.filter(patientId=p, file_type='gait').order_by('-upload_time').first()
        sound_file = FileUploaded.objects.filter(patientId=p, file_type='sound').order_by('-upload_time').first()

        data = {
            "rh_time": r_hand_file.upload_time if r_hand_file else None,
            "lh_time": l_hand_file.upload_time if l_hand_file else None,
            "gait_time": gait_file.upload_time if gait_file else None,
            "sound_time": sound_file.upload_time if sound_file else None,
        }

        return JsonResponse(data, safe=False)


def run_predict_model(patient_id, save_results=True):
    time_format = '%Y-%m-%d_%H:%M:%S'
    current_time = datetime.datetime.now().strftime(time_format)

    p = Patient.objects.get(patientId=int(patient_id))

    age = p.age
    gender = p.gender
    name = p.name
    
    if not save_results:
        print(f"Read patient object: Age {age}, gender {gender}, name {name}")

    r_hand_file = FileUploaded.objects.filter(
        patientId=p, file_type='right_hand'
    ).order_by('-upload_time').first()

    l_hand_file = FileUploaded.objects.filter(
        patientId=p, file_type='left_hand'
    ).order_by('-upload_time').first()

    gait_file = FileUploaded.objects.filter(
        patientId=p, file_type='gait'
    ).order_by('-upload_time').first()

    sound_file = FileUploaded.objects.filter(
        patientId=p, file_type='sound'
    ).exclude(file_path__icontains='freetalk').order_by('-upload_time').first()

    if not (r_hand_file and l_hand_file and gait_file and sound_file):
        raise Exception("Missing required files")

    out_d = f'/mnt/pd_app/results/{name}/{current_time}/'
    os.makedirs(out_d, exist_ok=True)

    gait_file_pth = f'{base_path}/walk/{gait_file.file_path}'
    l_hand_file_pth = f'{base_path}/gesture/{l_hand_file.file_path}'
    r_hand_file_pth = f'{base_path}/gesture/{r_hand_file.file_path}'
    sound_file_pth = f'{base_path}/sound/{sound_file.file_path}'

    features_extraction(
        gait_file_pth,
        l_hand_file_pth,
        r_hand_file_pth,
        sound_file_pth,
        out_d,
        debug=False
    )

    all_features_pth = f'{out_d}all_feature.npy'

    gait_result, hand_result, voice_results, all_results = predict_models(
        all_features_pth,
        age,
        gender,
        out_d
    )

    result_data = {
        "patientId": p,
        "patient": name,
        "gait_result": gait_result,
        "voice_result": voice_results,
        "hand_result": hand_result,
        "multimodal_results": all_results,
        "upload_time": current_time,
    }

    if save_results:
        r = Results.objects.create(**result_data)
        return r
    
    if not save_results:
        print("finish models prediction")
        
    return result_data


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'username': str(user.username)
    }


def check_file_time(file, current_time):
    if file:
        # Calculate the difference between the current time and the upload time of the latest file
        time_difference = current_time - file.upload_time

        # Check if the time difference is less than or equal to one hour
        if time_difference <= timedelta(hours=1):
            pass
        else:
            print("Latest hand file was not uploaded within the last hour! Old data was used!")
    else:
        print("File not found")
        
def get_latest_folder_by_creation_time(path):
    # List all subdirectories
    folders = [os.path.join(path, d) for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]

    if not folders:
        return None

    # Get the folder with the most recent creation time
    latest_folder = max(folders, key=os.path.getctime)
    return latest_folder

@staff_member_required
def export_latest_patient_results(request):
    print("Function called")  # Debug statement

    try:
        # Query the latest results for each patient
        latest_results = (
            Results.objects.values('patientId')  # Group by patientId
            .annotate(latest_upload=Max('upload_time'))  # Get the latest upload time for each patient
        )
        print(f"Latest results: {latest_results}")  # Debug statement

                # Get today's date in the format YYYYMMDD
        today_date = datetime.datetime.now().strftime('%Y%m%d')

        # Create the HTTP response with CSV content type
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{today_date}_results.csv"'

        # Write CSV header and rows
        writer = csv.writer(response)
        writer.writerow(['Patient ID', 'Patient Name', 'Upload Time', 'Gait Result', 'Voice Result', 'Hand Result', 'Multimodal Results'])

        for result in latest_results:
            print(f"Processing result: {result}")  # Debug statement
            full_result = Results.objects.filter(
                patientId=result['patientId'], upload_time=result['latest_upload']
            ).first()

            if full_result:
                writer.writerow([
                    full_result.patientId.patientId,
                    full_result.patient,
                    full_result.upload_time,
                    full_result.gait_result,
                    full_result.voice_result,
                    full_result.hand_result,
                    full_result.multimodal_results
                ])
        print("Export completed")  # Debug statement
        return response

    except Exception as e:
        print(f"Error occurred: {e}")  # Debug statement
        return HttpResponse(f"Error: {e}", status=500)
