# Parkinson's Disease App — Backend API

This project is the backend API for a Parkinson's Disease detection application. It includes machine learning models, pose estimation using MMPose, and a Django-based API server.

---

## Installation

### 1. Install Python Packages

```bash
pip install -r ./requirements.txt
```

### 2. Install PyTorch via Conda

```bash
conda install pytorch==1.10.1 torchvision==0.11.2 torchaudio==0.10.1 cudatoolkit=11.3 -c pytorch -c conda-forge
```

### 3. Install MMPose and Dependencies

```bash
pip install -U openmim

mim install mmengine
mim install mmcv-full==1.7.0
mim install "mmdet==2.28.1"
mim install mmpose==0.29.0 --user
```

---

## Model Checkpoints

Download pretrained model checkpoints from **Google Drive** and place them into:
[Checkpoint Folder on Google Drive](https://drive.google.com/drive/folders/1-t5fXd-pe2c48fQHrZJpapY9H0K5WUvs?usp=drive_link)
```
/pdmodel/checkpoints/
```

---

## Configuration

Edit the file: `mysite/settings.py`

Update the following:

```python
MEDIA_ROOT = "/path/to/your/media/folder"
MODEL_PATHS = "/path/to/your/checkpoints/folder"
```

---

## Running the Server

### Local Development

```bash
conda activate pdapp
python manage.py runserver
```

(Optional) If connecting an Android device:

```bash
cd ~/AppData/Local/Android/Sdk/platform-tools/
adb reverse tcp:8000 tcp:8000
```

### 🌍 On a Production Server

```bash
sudo /path/to/envs/bin/python manage.py runserver 0.0.0.0:80
```

Make sure port 80 is allowed through your firewall (e.g., `sudo ufw allow 80`)

---

