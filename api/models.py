from email.policy import default
from django.db import models
from rest_framework import serializers, viewsets
from django.contrib.auth.models import User, Group, Permission
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.decorators import permission_required
from .permissions import ViewPatientListPermssion


# Create your models here.
# Serializers define the API representation.
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'is_staff']


# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class Patient(models.Model):
    patientId = models.IntegerField(primary_key=True)
    user_name = models.CharField(max_length=200, default='')
    name = models.CharField(max_length=200, default='')
    email = models.CharField(max_length=320, default='')
    phone_no = models.CharField(max_length=30, default='')
    id_no = models.CharField(max_length=30, default='')
    gender = models.IntegerField(default=0)  # 0 = non, 1 = male, 2 = female
    age = models.IntegerField(default=0)
    birthday = models.CharField(max_length=20, default='')

    class Meta:
        permissions = ((ViewPatientListPermssion.codename,
                       ViewPatientListPermssion.describe),)
        ordering = ["patientId"]

    def __str__(self):
        return self.name


class PatientSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Patient
        fields = ['name', 'user_name', 'patientId', 'gender', 'age', 'birthday', 'email', 'phone_no', 'id_no']


class PatientRecord(models.Model):
    # patientId = models.CharField(max_length=200)
    patientId = models.ForeignKey(Patient, on_delete=models.CASCADE, default=1)
    time = models.CharField(max_length=200)
    taking_pd_medicine = models.BooleanField(default=False)
    taking_pd_med3hr = models.BooleanField(default=False)

    def __str__(self):
        return self.patientId.name + '_' + self.time


class PatientRecordSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PatientRecord
        fields = ['patientId', 'time', 'taking_pd_medicine', 'taking_pd_med3hr']


class PatientRecordViewSet(viewsets.ModelViewSet):
    queryset = PatientRecord.objects.all()
    serializer_class = PatientRecordSerializer

    def list(self, request, *args, **kwargs):
        return super().list(self, request, args, kwargs)


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [ViewPatientListPermssion]

    def list(self, request, *args, **kwargs):
        return super().list(self, request, args, kwargs)


class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.CharField(max_length=800)


class FileUploaded(models.Model):
    patientId = models.ForeignKey(Patient, on_delete=models.CASCADE, default=1)
    patient = models.CharField(max_length=255)  #patient name
    file_type = models.CharField(max_length=255)
    file_path = models.CharField(max_length=255)
    upload_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.patientId.name + '_' + self.file_type


class Results(models.Model):
    patientId = models.ForeignKey(Patient, on_delete=models.CASCADE, default=1)
    patient = models.CharField(max_length=255)   #patient name
    upload_time = models.CharField(max_length=255)
    gait_result = models.CharField(max_length=200)
    voice_result = models.CharField(max_length=200)
    hand_result = models.CharField(max_length=200)
    multimodal_results = models.CharField(max_length=200)

    def __str__(self):
        return self.patientId.name + '_' + self.upload_time


class PatientQuestionaireRecord(models.Model):
    # patientId = models.CharField(max_length=200)
    patientId = models.ForeignKey(Patient, on_delete=models.CASCADE, default=1)
    time = models.CharField(max_length=200)
    riskMarker = models.FloatField(default=0.0)
    PLR = models.FloatField(default=0.0)
    TELR = models.FloatField(default=0.0)
    PostProb = models.FloatField(default=0.0)
    PPPD = models.CharField(max_length=20)
    response = models.CharField(max_length=1000)

    def __str__(self):
        return self.patientId.name + '_' + self.time


class PatientQuestionaireSerializerRecord(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PatientQuestionaireRecord
        fields = ['patientId', 'time', 'riskMarker', 'PLR', 'TELR', 'PostProb', 'PPPD', 'response']
