# Parkinsons Disease APP backend API

# Install package
pip install -r ./requirement.txt
# Change Settings in mysites.settings
change the paths of MEDIA_ROOT and MODEL_PATHS to your media storage folder and installed models folders
# run server
# Local
conda activate pdapp
python manage.py runserver
cd to Sdk platfrom-tools
cd C:/User/limwe/AppData/Local/android/Sdk/platform-tools/
adb reverse tcp:8000 tcp:8000
# Server
sudo Path_to_envs/bin/python manage.py runserver 0:80
remember to allow portforward
