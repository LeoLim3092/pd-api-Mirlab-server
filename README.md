# Parkinsons Disease APP backend API

# Install package
pip install -r ./requirements.txt
install pytorch
conda install pytorch==1.10.1 torchvision==0.11.2 torchaudio==0.10.1 cudatoolkit=11.3 -c pytorch -c conda-forge
install mmpose
pip install -U openmim
mim install mmengine
mim install mmcv-full==1.7.0
mim install "mmdet==2.28.1"
mim install mmpose==0.29.0 --user
Download checkpoints from google drive and copy it into checkpoints folder
link
path: /pdmodel/checkpoint/

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
