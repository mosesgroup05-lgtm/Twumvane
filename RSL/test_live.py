"""
test_live.py

Opens your webcam, runs your trained model in real time, and shows
the recognized sign as text on screen.

BEFORE RUNNING:
    Make sure RSL/models/sign_model.h5 and RSL/models/label_map.json
    exist (produced by train_model.py).

TO RUN (from inside your RSL folder):
    python test_live.py

CONTROLS:
    Press 'q' while the camera window is focused to quit.

WHAT YOU'LL SEE:
    A webcam window with your hand/pose landmarks drawn as dots and
    lines (so you can see what the model is actually looking at),
    plus the currently recognized sign printed at the top, with a
    confidence percentage.
"""

import os
import json
import numpy as np
import cv2
import mediapipe as mp
import tensorflow as tf
from collections import deque

# ---------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------
MODELS_DIR = "models"
SEQUENCE_LENGTH = 30
CONFIDENCE_THRESHOLD = 0.75   # only show a word if the model is at least this sure
SMOOTHING_WINDOW = 5          # require this many consistent predictions before switching displayed word

mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils


def extract_landmarks_from_results(results):
    """Same feature extraction as extract_landmarks.py — must match exactly."""
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


def draw_landmarks(image, results):
    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS)
    mp_drawing.draw_landmarks(image, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS)
    mp_drawing.draw_landmarks(image, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS)


def main():
    model_path = os.path.join(MODELS_DIR, "sign_model.h5")
    label_map_path = os.path.join(MODELS_DIR, "label_map.json")

    if not os.path.exists(model_path) or not os.path.exists(label_map_path):
        print(f"ERROR: Couldn't find {model_path} or {label_map_path}.")
        print("Run train_model.py first.")
        return

    model = tf.keras.models.load_model(model_path)
    with open(label_map_path) as f:
        sign_names = json.load(f)

    print(f"Loaded model. Signs it knows: {sign_names}")
    print("Opening webcam... press 'q' in the video window to quit.")

    sequence_buffer = deque(maxlen=SEQUENCE_LENGTH)
    recent_predictions = deque(maxlen=SMOOTHING_WINDOW)
    displayed_word = ""
    displayed_confidence = 0.0

    cap = cv2.VideoCapture(0)

    with mp_holistic.Holistic(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as holistic:

        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                print("Couldn't read from webcam.")
                break

            frame = cv2.flip(frame, 1)  # mirror, feels natural
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = holistic.process(frame_rgb)

            draw_landmarks(frame, results)

            landmarks = extract_landmarks_from_results(results)
            sequence_buffer.append(landmarks)

            if len(sequence_buffer) == SEQUENCE_LENGTH:
                input_data = np.expand_dims(np.array(sequence_buffer), axis=0)
                prediction = model.predict(input_data, verbose=0)[0]

                predicted_index = int(np.argmax(prediction))
                confidence = float(prediction[predicted_index])

                if confidence >= CONFIDENCE_THRESHOLD:
                    recent_predictions.append(predicted_index)
                else:
                    recent_predictions.append(-1)  # "not confident" marker

                # Only update the displayed word if the last several
                # predictions agree — this avoids flickering between
                # words every frame.
                if len(recent_predictions) == SMOOTHING_WINDOW and \
                   len(set(recent_predictions)) == 1 and recent_predictions[0] != -1:
                    displayed_word = sign_names[recent_predictions[0]]
                    displayed_confidence = confidence
                elif len(recent_predictions) == SMOOTHING_WINDOW and recent_predictions[-1] == -1:
                    displayed_word = ""
                    displayed_confidence = 0.0

            # --- Draw the result on screen ---
            cv2.rectangle(frame, (0, 0), (640, 60), (0, 0, 0), -1)
            label_text = f"{displayed_word} ({displayed_confidence*100:.0f}%)" if displayed_word else "..."
            cv2.putText(frame, label_text, (15, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

            cv2.imshow('RSL Live Recognition (press q to quit)', frame)

            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()