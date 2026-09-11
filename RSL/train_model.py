"""
train_model.py

Trains an LSTM neural network to recognize signs from the landmark
data produced by extract_landmarks.py.

BEFORE RUNNING:
    pip install tensorflow scikit-learn numpy

FOLDER EXPECTED:
    RSL/data/landmarks/muraho/*.npy
    RSL/data/landmarks/papa/*.npy
    (one folder per sign, same structure the extraction script created)

TO RUN (from inside your RSL folder):
    python train_model.py

WHAT YOU'LL GET:
    RSL/models/sign_model.h5          <- the trained model
    RSL/models/label_map.json         <- maps model output numbers back to sign names

WITH ONLY 2 SIGNS:
    This is a small first test, not your final model. The goal right
    now is just to confirm the whole pipeline works — record, extract,
    train, recognize. Once this works, keep adding more signs and
    re-run this same script; accuracy and usefulness will grow as
    your vocabulary grows.
"""

import os
import json
import numpy as np
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.utils import to_categorical

# ---------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------
LANDMARKS_DIR = os.path.join("data", "landmarks")
MODELS_DIR = "models"
SEQUENCE_LENGTH = 30
NUM_FEATURES = 225   # 33 pose + 21 left hand + 21 right hand, x/y/z each
EPOCHS = 100
BATCH_SIZE = 8


def load_dataset():
    sign_names = sorted(
        f for f in os.listdir(LANDMARKS_DIR)
        if os.path.isdir(os.path.join(LANDMARKS_DIR, f))
    )

    if len(sign_names) < 2:
        raise SystemExit(
            f"Found only {len(sign_names)} sign(s) in {LANDMARKS_DIR}. "
            "You need at least 2 different signs for the model to learn "
            "to tell them apart."
        )

    print(f"Signs found: {sign_names}")

    X = []
    y = []

    for label_index, sign_name in enumerate(sign_names):
        folder = os.path.join(LANDMARKS_DIR, sign_name)
        files = sorted(f for f in os.listdir(folder) if f.endswith(".npy"))

        print(f"  {sign_name}: {len(files)} sequences")

        for filename in files:
            sequence = np.load(os.path.join(folder, filename))

            if sequence.shape != (SEQUENCE_LENGTH, NUM_FEATURES):
                print(f"    WARNING: {filename} has shape {sequence.shape}, "
                      f"expected ({SEQUENCE_LENGTH}, {NUM_FEATURES}) — skipping")
                continue

            X.append(sequence)
            y.append(label_index)

    X = np.array(X)
    y = np.array(y)

    return X, y, sign_names


def build_model(num_classes):
    model = Sequential([
        LSTM(64, return_sequences=True, activation='tanh',
             input_shape=(SEQUENCE_LENGTH, NUM_FEATURES)),
        Dropout(0.3),
        LSTM(128, return_sequences=False, activation='tanh'),
        Dropout(0.3),
        Dense(64, activation='relu'),
        Dense(num_classes, activation='softmax'),
    ])

    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['categorical_accuracy']
    )

    return model


def main():
    X, y, sign_names = load_dataset()
    num_classes = len(sign_names)

    print(f"\nTotal usable sequences: {len(X)}")
    print(f"Data shape: {X.shape}")

    y_categorical = to_categorical(y, num_classes=num_classes)

    # Keep a held-out test set to honestly check accuracy on data
    # the model has never seen during training.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_categorical, test_size=0.2, random_state=42, stratify=y
    )

    print(f"Training on {len(X_train)} sequences, testing on {len(X_test)}\n")

    model = build_model(num_classes)
    model.summary()

    early_stop = tf.keras.callbacks.EarlyStopping(
        monitor='val_loss', patience=15, restore_best_weights=True
    )

    model.fit(
        X_train, y_train,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        validation_data=(X_test, y_test),
        callbacks=[early_stop],
        verbose=1
    )

    loss, accuracy = model.evaluate(X_test, y_test, verbose=0)
    print(f"\nFinal test accuracy: {accuracy * 100:.1f}%")

    os.makedirs(MODELS_DIR, exist_ok=True)

    model_path = os.path.join(MODELS_DIR, "sign_model.h5")
    model.save(model_path)
    print(f"Model saved to {model_path}")

    label_map_path = os.path.join(MODELS_DIR, "label_map.json")
    with open(label_map_path, "w") as f:
        json.dump(sign_names, f, indent=2)
    print(f"Label map saved to {label_map_path}")

    print("\nDone. Next step: test this model live with your webcam, "
          "or keep recording more signs and re-run this script.")


if __name__ == "__main__":
    main()