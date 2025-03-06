from pdModel.deployModel import model_extraction, predict_models
from datetime import datetime

gait_v_pth = "/mnt/pd_app/walk/20200818_5C.mp4"
left_v_path = "/mnt/pd_app/gesture/202008069_AL.mp4"
right_v_path = "/mnt/pd_app/gesture/202008069_AR.mp4"
out_d = "/mnt/pd_app/results/test/"

ini_time_for_now = datetime.now()
model_extraction(gait_v_pth, left_v_path, right_v_path, out_d)
finish_time = datetime.now()
print((finish_time - ini_time_for_now).seconds)

# predict_models(f'{out_d}all_feature.npy', 35, 0, out_d)

