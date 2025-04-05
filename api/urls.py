import imp
from django.urls import include, path
from django.contrib.auth.models import User
from django.contrib import admin
from django.views.generic import RedirectView
from api.models import UserViewSet
from api.models import PatientViewSet
from rest_framework import routers
from . import views


# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'patient', PatientViewSet)
urlpatterns = router.urls

urlpatterns += [
    path('login', views.Login.as_view()),
    path('upload_sound_record', views.UploadSound.as_view()),
    path('upload_walk_record', views.UploadWalk.as_view()),
    path('upload_gesture_record', views.UploadGesture.as_view()),
    path('upload_paint', views.UploadPaint.as_view()),
    path('create_new_patient', views.CreateNewPatient.as_view()),
    path('google_login', views.GoogleLogin.as_view()),
    path('predict_model', views.PredictModel.as_view()),
    path('get_results', views.GetResults.as_view()),
    path('upload_medicine_record', views.UploadMedicineRecord.as_view()),
    path('upload_questionaire_record', views.UploadQuestionaireRecord.as_view()),
    path("medical_staff_login", views.MedicalStaffLogin.as_view()),
    path("create_new_user", views.CreateNewUser.as_view()),
    path("get_user_data", views.getUserData.as_view()),
    path("get_last_upload_data", views.getLastUploadData.as_view()),
    path("check_recording", views.CheckRecording.as_view()),
    path("rerun_all_predictions", views.RerunAllPatientPredictModel.as_view()),
    path("rerun_from_date_predictions", views.RerunFromDatePatientPrediction.as_view()),
    path('export-latest-results', views.export_latest_patient_results, name='export_latest_results'),
]