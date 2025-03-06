from django.contrib import admin

# Register your models here.
from .models import Patient, Article, PatientRecord, FileUploaded, Results, PatientQuestionaireRecord

admin.site.register(Patient)
admin.site.register(Article)
admin.site.register(PatientRecord)
admin.site.register(FileUploaded)
admin.site.register(Results)
admin.site.register(PatientQuestionaireRecord)