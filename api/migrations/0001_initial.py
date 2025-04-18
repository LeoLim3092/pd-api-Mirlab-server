# Generated by Django 4.0.6 on 2023-04-20 14:43

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('content', models.CharField(max_length=800)),
            ],
        ),
        migrations.CreateModel(
            name='FileUploaded',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('patient', models.CharField(max_length=255)),
                ('file_type', models.CharField(max_length=255)),
                ('file_path', models.CharField(max_length=255)),
                ('upload_time', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Patient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('email', models.CharField(default='', max_length=320)),
                ('serial_number', models.CharField(default='123', max_length=30)),
                ('taking_pd_medicine', models.BooleanField(default=False)),
                ('gender', models.IntegerField(default=0)),
                ('age', models.IntegerField(default=0)),
                ('birthday', models.CharField(default='', max_length=20)),
            ],
            options={
                'permissions': (('view_patient_list', 'Can view patient list'),),
            },
        ),
        migrations.CreateModel(
            name='PatientQuestionaire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('patientId', models.CharField(max_length=200)),
                ('time', models.CharField(max_length=200)),
                ('question_number', models.CharField(max_length=50)),
                ('response', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='PatientRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('patientId', models.CharField(max_length=200)),
                ('time', models.CharField(max_length=200)),
                ('taking_pd_medicine', models.BooleanField(default=False)),
                ('taking_pd_med3hr', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Results',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('patient', models.CharField(max_length=255)),
                ('upload_time', models.CharField(max_length=255)),
                ('gait_result', models.CharField(max_length=200)),
                ('voice_result', models.CharField(max_length=200)),
                ('hand_result', models.CharField(max_length=200)),
                ('multimodal_results', models.CharField(max_length=200)),
            ],
        ),
    ]
