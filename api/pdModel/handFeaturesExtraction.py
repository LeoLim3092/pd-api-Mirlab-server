import os
import joblib
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks
import pandas as pd
from itertools import combinations
from utils import find_period
from scipy.signal import stft


fps = 59
shift = fps
coverage = 0.5


def get_thumb_index_dis(hand_landmarks):
    hand_thumb = hand_landmarks[:, 4, :-1]
    hand_index = hand_landmarks[:, 8, :-1]

    hand_4_8_dis = []
    for t, i in zip(hand_thumb, hand_index):
        hand_4_8_dis.append(np.linalg.norm(i - t))
    hand_4_8_dis = np.array(hand_4_8_dis)

    return hand_4_8_dis


def get_thumb_pinky_dis(hand_landmarks):
    hand_thumb = hand_landmarks[:, 4, :]
    hand_index = hand_landmarks[:, 20, :]

    hand_4_20_dis = []
    for t, i in zip(hand_thumb, hand_index):
        hand_4_20_dis.append(np.linalg.norm(i - t))
    hand_4_20_dis = np.array(hand_4_20_dis)

    return hand_4_20_dis


def extract_thumb_index_periods(hand_pose, ax=None, title=""):
    hand_dis = get_thumb_index_dis(hand_pose)
    mean_hand_dis = np.mean(hand_dis)
    hand_dis = hand_dis / hand_dis.max()

    T, _ = find_period(hand_dis)
    p, values = find_peaks(hand_dis, height=np.mean(hand_dis),
                           distance=int(T * 0.4))

    if ax:
        ax.plot(hand_dis)
        ax.plot(p, np.array(hand_dis)[p], "x", ms=10)
        ax.set_xlabel("Frames")
        ax.set_ylabel("Relative thumb-index distance")
        ax.set_title(title)

    return np.diff(p, prepend=0).mean() / fps, (
                np.diff(p, prepend=0)[:4].mean() / fps - np.diff(p, prepend=0)[-5:].mean() / fps) / 2, mean_hand_dis


def preprocess_landmarks(dt):
    hand_pose_arr = list(dt["landmarks"].values())
    hand_pose_ls = []

    for a, arr in enumerate(hand_pose_arr):
        if isinstance(arr, list):
            if arr:
                hand_pose_ls.append(arr)
            else:
                hand_pose_ls.append([np.zeros((21, 3))])
        else:
            if arr[0].shape[0] != 0:
                hand_pose_ls.append(arr)
            else:
                hand_pose_ls.append([np.zeros((21, 3))])

    hand_pose_arr = np.array(hand_pose_ls)
    return hand_pose_arr


def get_freq_inten(arr):

    dis = get_thumb_index_dis(arr)
    
    # Perform STFT
    fs = 30
    f, t, Zxx = stft(dis, fs=fs, nperseg=300)
    
    # Determine midpoint in time for the first half of the signal
    mid_point = np.where(t >= t.max() / 2)[0][0]
    
    # Extract STFT data for the first half
    Zxx_first_half = Zxx[:, :mid_point]
    Zxx_last_half = Zxx[:, mid_point:]
    
    # Calculate magnitude
    magnitude = np.abs(Zxx_first_half)
    last_msg = np.abs(Zxx_last_half)
    
    # Calculate the weighted average frequency
    _1st_half_average_frequency = np.mean(np.sum(magnitude * f[:, None], axis=0) / np.sum(magnitude, axis=0))
    _last_half_average_frequency = np.mean(np.sum(last_msg * f[:, None], axis=0) / np.sum(last_msg, axis=0))
    avr_frq = (_1st_half_average_frequency + _last_half_average_frequency)/2
    frq_dff = _1st_half_average_frequency - _last_half_average_frequency
    
    # df, dt = f[1] - f[0], t[1] - t[0]
    # e = sum(np.sum(Zxx.real**2 + Zxx.imag**2, axis=0) * df) * dt

    T, _ = find_period(dis)
    p, values = find_peaks(dis, height=np.mean(dis),
                           distance=int(T * 0.4))
    height = values["peak_heights"]

    return avr_frq, np.mean(height), avr_frq*np.mean(height), frq_dff


def single_thumb_index_hand(r_path, l_path, out_dir):

    r_dt = joblib.load(r_path)
    right_hand_arr = preprocess_landmarks(r_dt)[:, 0, :, :]
    r_hf = extract_thumb_index_periods(right_hand_arr, title=f"Thumb-index right hand")
    
    l_dt = joblib.load(l_path)
    left_hand_arr = preprocess_landmarks(l_dt)[:, 0, :, :]
    l_hf = extract_thumb_index_periods(left_hand_arr, title=f"Thumb-index left hand")

    l_hf2 = get_freq_inten(left_hand_arr)
    r_hf2 = get_freq_inten(right_hand_arr)

    return list(r_hf) + list(l_hf) + list(l_hf2) + list(r_hf2)


if __name__ == '__main__':
    right_path = "/mnt/pd_app/results/test/right_hand_202008069_AR.txt"
    left_path = "/mnt/pd_app/results/test/left_hand_202008069_AR.txt"
    out_d = "/mnt/pd_app/results/test/"
    single_thumb_index_hand(right_path, left_path, out_d)
