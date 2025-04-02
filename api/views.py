import os
import asyncio
from django.shortcuts import render, redirect
from django.contrib.auth.models import User, Group
from .models import PatientRecord, Patient, FileUploaded, Results, PatientQuestionaireRecord, Article
from rest_framework.decorators import api_view
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, FileResponse, JsonResponse
from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.core.files.storage import default_storage
from django.core.files.storage import FileSystemStorage
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
import json
import datetime
from django.db.models import Max
from .pdModel.deployModel import model_extraction, predict_models, data_checking
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.views import View
from api.models import PatientSerializer


print(settings.MEDIA_ROOT, settings.MEDIA_URL)

base_path = '/mnt/pd_app'
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
            cooridinates = request.POST['coordinates']
            coordinates_data = json.loads(cooridinates)
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid Json format")
        
        format = '%Y-%m-%d %H:%M:%S'
        time = datetime.datetime.now().strftime(format)

        current_pid = Patient.objects.get(patientId = int(pid))
        patient = current_pid.name

        if(type == 'spiral_right'):
            file_path = paint_spiral_right_storage.save(time + "_spiral_right_" + patient + '_' + '_' + pid + '_' + file.name, file)
            file = FileUploaded(patientId=current_pid, patient=patient, file_type='spiral_paint', file_path=file_path)
            file.save()
            
            # Save coordinates as JSON file
            json_filename = os.path.splitext(file_path)[0] + '.json'
            json_path = os.path.join(paint_spiral_right_storage.location, os.path.basename(json_filename))

            with open(json_path, 'w') as json_file:
                json.dump(coordinates_data, json_file)
            
        if(type == 'spiral_left'):
            file_path = paint_spiral_left_storage.save(time + "_spiral_left_" + patient + '_' + '_' + pid + '_' + file.name, file)
            file = FileUploaded(patientId=current_pid, patient=patient, file_type='spiral_paint', file_path=file_path)
            file.save()
            
            # Save coordinates as JSON file
            json_filename = os.path.splitext(file_path)[0] + '.json'
            json_path = os.path.join(paint_spiral_right_storage.location, os.path.basename(json_filename))

            with open(json_path, 'w') as json_file:
                json.dump(coordinates_data, json_file)
                
        if(type == 'three'):
            file_path = paint_three_right_storage.save(time + "_three_right_" + patient + '_' + '_' + pid + '_' + file.name, file)
            file = FileUploaded(patientId=current_pid, patient=patient, file_type='three', file_path=file_path)
            file.save()
            
            # Save coordinates as JSON file
            json_filename = os.path.splitext(file_path)[0] + '.json'
            json_path = os.path.join(paint_spiral_right_storage.location, os.path.basename(json_filename))

            with open(json_path, 'w') as json_file:
                json.dump(coordinates_data, json_file)
                
        elif(type == 'three_left'):
            file_path = paint_three_left_storage.save(time + "_three_left_" + patient + '_' + '_' + pid + '_' + file.name, file)
            file = FileUploaded(patientId=current_pid, patient=patient, file_type='three_paint', file_path=file_path)
            file.save()
            
            # Save coordinates as JSON file
            json_filename = os.path.splitext(file_path)[0] + '.json'
            json_path = os.path.join(paint_spiral_right_storage.location, os.path.basename(json_filename))

            with open(json_path, 'w') as json_file:
                json.dump(coordinates_data, json_file)
                
        print(json_path)

        return HttpResponse()


class UploadWalk(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request: WSGIRequest):
        file = request.FILES['file']
        pid = request.POST["pid"]
        format = '%Y-%m-%d %H:%M:%S'
        time = datetime.datetime.now().strftime(format)
        current_pid = Patient.objects.get(patientId=int(pid))
        patient = current_pid.name

        file_path = walk_storage.save(time + "_walk_" + patient + '_' + '_' + pid + '_' + file.name, file)
        file = FileUploaded(patientId=current_pid, patient=patient, file_type='gait', file_path=file_path)
        file.save()

        return HttpResponse()


class UploadGesture(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request: WSGIRequest):
        file = request.FILES['file']
        pid = request.POST["pid"]
        type = request.POST['type']
        format = '%Y-%m-%d %H:%M:%S'
        time = datetime.datetime.now().strftime(format)
        current_pid = Patient.objects.get(patientId=int(pid))
        patient = current_pid.name

        if type == '右手':
            file_path = gesture_storage.save(time + "_gesture_" + patient + '_' + '_' + pid + '_' + type + '_' + file.name, file)
            file = FileUploaded(patientId=current_pid, patient=patient, file_type='right_hand', file_path=file_path)
            file.save()
        else:
            file_path = gesture_storage.save(time + "_gesture_" + patient + '_' + '_' + pid + '_' + type + '_' + file.name, file)
            file = FileUploaded(patientId=current_pid, patient=patient, file_type='left_hand', file_path=file_path)
            file.save()

        return HttpResponse()


class UploadMedicineRecord(APIView):

    def post(self, request: WSGIRequest):
        medicine_taken = request.POST["medicine"]
        medicine_taken_3hr = request.POST["medicine_3hr"]
        pid = request.POST["pid"]
        format = '%Y-%m-%d %H:%M:%S'
        time = datetime.datetime.now().strftime(format)
        current_pid = Patient.objects.get(patientId=int(pid))
        # pr = PatientRecord(patientId=pid, time=time, taking_pd_medicine=medicine_taken,
        #              taking_pd_med3hr=medicine_taken_3hr)
        pr = PatientRecord(patientId=current_pid, time=time, taking_pd_medicine=medicine_taken,
                    taking_pd_med3hr=medicine_taken_3hr)
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
        current_pid = Patient.objects.get(patientId = int(pid))
        qr = PatientQuestionaireRecord(patientId=current_pid, time=time, riskMarker = riskMarker, PLR = PLR,
                                       TELR = TELR, PostProb = PostProb, PPPD = PPPD, response = response)
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
        
        format = '%Y-%m-%d'
        time_now = datetime.datetime.now()

        #p = Patient(name = patient_name, serial_number = '', gender = patient_gender, age = patient_age)
        p = Patient(name=patient_name, user_name=user_name, gender=patient_gender, age=int(patient_age),
                    birthday=patient_birthday, email=patient_email, phone_no=phone_no, id_no=id_no)
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
        user, created = User.objects.get_or_create(email=email)
        email_local, email_domain = email.split("@")
        if created:
            user.username = email_local
        
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
            HttpResponseBadRequest()


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

        if os.path.isdir(f'/mnt/pd_app/results/{name}/'):
            os.makedirs(f'/mnt/pd_app/results/{name}/{current_time}/')
        else:
            os.makedirs(f'/mnt/pd_app/results/{name}/')

        gait_file_pth = f'{base_path}/walk/{gait_file.file_path}'
        l_hand_file_pth = f'{base_path}/gesture/{l_hand_file.file_path}'
        r_hand_file_pth = f'{base_path}/gesture/{r_hand_file.file_path}'
        sound_file_pth = f'{base_path}/sound/{sound_file.file_path}'

        try:
            success, error = data_checking(gait_file_pth, l_hand_file_pth, r_hand_file_pth, sound_file_pth)
            return JsonResponse({"success": success, "error": error})
        
        except:
            error_message = "Failed to process data"
            return Response({"error": error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PredictModel(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request: WSGIRequest):
        pid = request.POST['pid']
        format = '%Y-%m-%d_%H:%M:%S'
        current_time = datetime.datetime.now().strftime(format)

        p = Patient.objects.get(patientId=int(pid))
        age = p.age
        gender = p.gender
        name = p.name

        r_hand_file = FileUploaded.objects.filter(patientId=p, file_type='right_hand').order_by('-upload_time').first()
        l_hand_file = FileUploaded.objects.filter(patientId=p, file_type='left_hand').order_by('-upload_time').first()
        gait_file = FileUploaded.objects.filter(patientId=p, file_type='gait').order_by('-upload_time').first()
        sound_file = FileUploaded.objects.filter(patientId=p, file_type='sound').order_by('-upload_time').first()

        out_d = f'/mnt/pd_app/results/{name}/{current_time}/'

        if os.path.isdir(f'/mnt/pd_app/results/{name}/'):
            os.makedirs(f'/mnt/pd_app/results/{name}/{current_time}/')
        else:
            os.makedirs(f'/mnt/pd_app/results/{name}/')


        gait_file_pth = f'{base_path}/walk/{gait_file.file_path}'
        l_hand_file_pth = f'{base_path}/gesture/{l_hand_file.file_path}'
        r_hand_file_pth = f'{base_path}/gesture/{r_hand_file.file_path}'
        sound_file_pth = f'{base_path}/sound/{sound_file.file_path}'

        try:
            model_extraction(gait_file_pth, l_hand_file_pth, r_hand_file_pth, sound_file_pth, out_d)
            all_features_pth = f'{out_d}all_feature.npy'
            gait_result, hand_result, voice_results, all_results = predict_models(all_features_pth, age, gender, out_d)

            r = Results(patientId=p, patient=name, gait_result=gait_result, voice_result=voice_results,
                        hand_result=hand_result, multimodal_results=all_results, upload_time=current_time)
            r.save()

            return HttpResponse()

        except:
            error_message = "Failed to process data"
            return Response({"error": error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetResults(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    print(authentication_classes, permission_classes)

    def post(self, request: WSGIRequest):
        pid = request.POST['pid']
        p = Patient.objects.get(patientId=int(pid))
        thereshold = Article.objects.get(title="Theresholds")
        thre = thereshold.content.split(", ")  # Split the string into a list
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


class getVideo(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request: WSGIRequest):
        file_name = request.POST['file_name']
        folder_name = request.POST['file_name']
        video_path = f'/mnt/pd_app/results/{folder_name}/{file_name}'

        with open(video_path, 'rb') as video_file:
            response = FileResponse(video_file, content_type='video/mp4')
            return response


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


class getLastUploadData(APIView):

    def post(self, request):
        pid = request.POST['pid']

        p = Patient.objects.get(patientId=int(pid))

        r_hand_file = FileUploaded.objects.filter(patientId=p, file_type='right_hand').order_by('-upload_time').first()
        l_hand_file = FileUploaded.objects.filter(patientId=p, file_type='left_hand').order_by('-upload_time').first()
        gait_file = FileUploaded.objects.filter(patientId=p, file_type='gait').order_by('-upload_time').first()
        sound_file = FileUploaded.objects.filter(patientId=p, file_type='sound').order_by('-upload_time').first()

        rh_last_upload = r_hand_file.upload_time
        lh_last_upload = l_hand_file.upload_time
        gait_last_upload = gait_file.upload_time
        sound_last_upload = sound_file.upload_time
        data = {"rh_time": rh_last_upload,
                "lh_time": lh_last_upload,
                "gait_time": gait_last_upload,
                "sound_time": sound_last_upload}

        return JsonResponse(data, safe=False)


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



