"""
extract_landmarks.py

Converts your recorded sign-language video clips into small numeric
landmark files that a model can actually train on.

WHAT THIS DOES:
    For every video in RSL/data/raw_videos/<sign_name>/*.mp4,
    it runs MediaPipe Holistic to detect hand/pose landmarks on every
    frame, resamples the sequence to a fixed length, and saves the
    result as a small .npy file in RSL/data/landmarks/<sign_name>/.

    Your original videos are NEVER modified or uploaded anywhere by
    this script — it only reads them and writes small numeric files.

BEFORE RUNNING:
    1. Install Python 3.9-3.11 if you don't have it (python.org).
    2. Open Command Prompt in your RSL folder and run:
           pip install mediapipe opencv-python numpy
    3. Make sure your folders look like this:
           RSL/data/raw_videos/muraho/muraho_01.mp4 ... muraho_50.mp4
           RSL/data/raw_videos/amazina/amazina_01.mp4 ...

TO RUN:
    From inside the RSL folder:
        python extract_landmarks.py

WHAT YOU'LL GET:
    RSL/data/landmarks/muraho/muraho_01.npy ... (one per clip)
    RSL/data/landmarks/amazina/amazina_01.npy ...

    This "landmarks" folder is what you zip and upload next — it will
    be a tiny fraction of the size of your raw videos.
"""

import os
import cv2
import numpy as np
import mediapipe as mp

# ---------------------------------------------------------------
# CONFIG — change these if your folder names are different
# ---------------------------------------------------------------
RAW_VIDEOS_DIR = os.path.join("data", "raw_videos")
LANDMARKS_DIR = os.path.join("data", "landmarks")
SEQUENCE_LENGTH = 30   # every clip becomes exactly 30 frames of data
VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi", ".mkv")

# ---------------------------------------------------------------
# MediaPipe setup
# ---------------------------------------------------------------
mp_holistic = mp.solutions.holistic


def extract_landmarks_from_results(results):
    """
    Pulls out pose (33 points) + left hand (21 points) + right hand (21 points)
    as a single flat array of numbers per frame. Missing landmarks
    (e.g. a hand that's off-screen) are filled with zeros instead of
    crashing, so the array length is always the same.
    """
    def to_array(landmark_list, num_points, num_dims=3):
        if landmark_list is None:
            return np.zeros(num_points * num_dims)
        return np.array(
            [[lm.x, lm.y, lm.z] for lm in landmark_list.landmark]
        ).flatten()

    pose = to_array(results.pose_landmarks, 33)
    left_hand = to_array(results.left_hand_landmarks, 21)
    right_hand = to_array(results.right_hand_landmarks, 21)

    return np.concatenate([pose, left_hand, right_hand])


def resample_sequence(frames, target_length):
    """
    Every video has a slightly different number of frames. This picks
    `target_length` evenly-spaced frames from the sequence so every
    clip ends up the same length, which the model requires.
    """
    frames = np.array(frames)
    if len(frames) == 0:
        return np.zeros((target_length, frames.shape[-1] if frames.ndim > 1 else 225))

    if len(frames) == target_length:
        return frames

    indices = np.linspace(0, len(frames) - 1, target_length).astype(int)
    return frames[indices]


def process_video(video_path, holistic):
    cap = cv2.VideoCapture(video_path)
    frame_landmarks = []

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        # MediaPipe expects RGB, OpenCV gives BGR
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = holistic.process(frame_rgb)

        frame_landmarks.append(extract_landmarks_from_results(results))

    cap.release()
    return resample_sequence(frame_landmarks, SEQUENCE_LENGTH)


def main():
    if not os.path.isdir(RAW_VIDEOS_DIR):
        print(f"ERROR: Could not find '{RAW_VIDEOS_DIR}'.")
        print("Run this script from inside your RSL folder, and make sure")
        print("data/raw_videos/<sign_name>/ exists with your video clips.")
        return

    sign_folders = sorted(
        f for f in os.listdir(RAW_VIDEOS_DIR)
        if os.path.isdir(os.path.join(RAW_VIDEOS_DIR, f))
    )

    if not sign_folders:
        print(f"No sign folders found inside {RAW_VIDEOS_DIR}.")
        return

    print(f"Found {len(sign_folders)} sign(s): {', '.join(sign_folders)}")

    with mp_holistic.Holistic(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as holistic:

        for sign_name in sign_folders:
            input_folder = os.path.join(RAW_VIDEOS_DIR, sign_name)
            output_folder = os.path.join(LANDMARKS_DIR, sign_name)
            os.makedirs(output_folder, exist_ok=True)

            video_files = sorted(
                f for f in os.listdir(input_folder)
                if f.lower().endswith(VIDEO_EXTENSIONS)
            )

            print(f"\n[{sign_name}] Processing {len(video_files)} clip(s)...")

            for i, filename in enumerate(video_files, start=1):
                video_path = os.path.join(input_folder, filename)
                output_name = os.path.splitext(filename)[0] + ".npy"
                output_path = os.path.join(output_folder, output_name)

                if os.path.exists(output_path):
                    print(f"  [{i}/{len(video_files)}] {filename} -> already done, skipping")
                    continue

                sequence = process_video(video_path, holistic)
                np.save(output_path, sequence)
                print(f"  [{i}/{len(video_files)}] {filename} -> {output_name}  shape={sequence.shape}")

    print("\nDone! Your landmark files are in:", LANDMARKS_DIR)
    print("Zip that 'landmarks' folder (it will be tiny) and upload it next.")


if __name__ == "__main__":
    main()