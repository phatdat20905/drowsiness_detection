# ============================================================
#  training/train_eye_model.py
#  Huấn luyện MobileNetV2 – Eye: Open (0) / Closed (1)
#
#  Dataset:  dataset/train/   dataset/valid/   dataset/test/
#            └─ open/            └─ open/          └─ open/
#            └─ closed/          └─ closed/        └─ closed/
#
#  Chạy: python training/train_eye_model.py
# ============================================================

import os, sys, random
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Cố định seed TRƯỚC mọi import TF ─────────────────────────
SEED = 42
os.environ["PYTHONHASHSEED"] = str(SEED)
random.seed(SEED)
import numpy as np
np.random.seed(SEED)
import tensorflow as tf
tf.random.set_seed(SEED)
try:
    tf.config.experimental.enable_op_determinism()
except Exception:
    pass

import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix

from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.layers import GlobalAveragePooling2D, Dense, Dropout, BatchNormalization
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.preprocessing.image import ImageDataGenerator

from config import (
    TRAIN_DIR, VALID_DIR, TEST_DIR,
    EYE_MODEL_PATH, MODELS_DIR,
    IMG_SIZE, BATCH_SIZE, EPOCHS, LEARNING_RATE,
)

CLASSES = ["open", "closed"]   # open=0, closed=1


# ── Generators ────────────────────────────────────────────────

def build_generators():
    """
    3 generator độc lập, mỗi tập từ thư mục riêng.
    - Train  : augmentation + preprocess_input
    - Valid  : chỉ preprocess_input, không augment, không shuffle
    - Test   : chỉ preprocess_input, không augment, không shuffle
    """
    train_gen = ImageDataGenerator(
        preprocessing_function=preprocess_input,
        rotation_range=15,
        width_shift_range=0.10,
        height_shift_range=0.10,
        horizontal_flip=True,
        brightness_range=[0.8, 1.2],
        zoom_range=0.10,
        fill_mode="nearest",
    ).flow_from_directory(
        TRAIN_DIR,
        target_size=IMG_SIZE, batch_size=BATCH_SIZE,
        class_mode="binary", classes=CLASSES,
        shuffle=True, seed=SEED,
    )

    val_gen = ImageDataGenerator(
        preprocessing_function=preprocess_input,
    ).flow_from_directory(
        VALID_DIR,
        target_size=IMG_SIZE, batch_size=BATCH_SIZE,
        class_mode="binary", classes=CLASSES,
        shuffle=False,
    )

    test_gen = ImageDataGenerator(
        preprocessing_function=preprocess_input,
    ).flow_from_directory(
        TEST_DIR,
        target_size=IMG_SIZE, batch_size=BATCH_SIZE,
        class_mode="binary", classes=CLASSES,
        shuffle=False,
    )

    print(f"  Train : {train_gen.samples:>5} ảnh  |  class_indices: {train_gen.class_indices}")
    print(f"  Valid : {val_gen.samples:>5} ảnh")
    print(f"  Test  : {test_gen.samples:>5} ảnh")
    return train_gen, val_gen, test_gen


# ── Model ─────────────────────────────────────────────────────

def build_model():
    base = MobileNetV2(input_shape=(*IMG_SIZE, 3), include_top=False, weights="imagenet")
    base.trainable = False

    x = base.output
    x = GlobalAveragePooling2D()(x)
    x = BatchNormalization()(x)
    x = Dense(128, activation="relu",
              kernel_initializer=tf.keras.initializers.GlorotUniform(seed=SEED))(x)
    x = Dropout(0.40, seed=SEED)(x)
    x = Dense(64,  activation="relu",
              kernel_initializer=tf.keras.initializers.GlorotUniform(seed=SEED))(x)
    x = Dropout(0.30, seed=SEED)(x)
    out = Dense(1, activation="sigmoid")(x)
    return Model(inputs=base.input, outputs=out), base


# ── Train ─────────────────────────────────────────────────────

def train():
    os.makedirs(MODELS_DIR, exist_ok=True)
    print("\n=== [Eye] Chuẩn bị dữ liệu ===")
    train_gen, val_gen, test_gen = build_generators()

    model, base = build_model()

    # ── Phase 1: Chỉ train phần head, base frozen ─────────────
    model.compile(
        optimizer=Adam(LEARNING_RATE),
        loss="binary_crossentropy",
        metrics=["accuracy"],
    )
    print("\n=== [Eye] Phase 1 – Head only (base frozen) ===")
    h1 = model.fit(
        train_gen, epochs=10, validation_data=val_gen,
        callbacks=[
            EarlyStopping(patience=5, restore_best_weights=True, verbose=1),
            ReduceLROnPlateau(factor=0.5, patience=3, min_lr=1e-7, verbose=1),
        ],
    )

    # ── Phase 2: Fine-tune 30 layer cuối của base ─────────────
    base.trainable = True
    for layer in base.layers[:-30]:
        layer.trainable = False

    model.compile(
        optimizer=Adam(LEARNING_RATE / 10),
        loss="binary_crossentropy",
        metrics=["accuracy"],
    )
    print("\n=== [Eye] Phase 2 – Fine-tune (30 layers cuối) ===")
    h2 = model.fit(
        train_gen, epochs=EPOCHS, validation_data=val_gen,
        callbacks=[
            ModelCheckpoint(EYE_MODEL_PATH, monitor="val_accuracy",
                            save_best_only=True, verbose=1),
            EarlyStopping(patience=7, restore_best_weights=True, verbose=1),
            ReduceLROnPlateau(factor=0.5, patience=3, min_lr=1e-8, verbose=1),
        ],
    )

    # ── Đánh giá trên TEST SET ────────────────────────────────
    print("\n=== [Eye] Đánh giá trên TEST SET (held-out) ===")
    evaluate(model, test_gen)
    plot_history(h1, h2)
    print(f"\n✓ Model lưu tại: {EYE_MODEL_PATH}")


# ── Evaluate ──────────────────────────────────────────────────

def evaluate(model, test_gen):
    test_gen.reset()
    y_prob = model.predict(test_gen, verbose=1).flatten()
    y_pred = (y_prob > 0.5).astype(int)
    y_true = test_gen.classes

    loss, acc = model.evaluate(test_gen, verbose=0)
    print(f"Test Loss: {loss:.4f}   Test Accuracy: {acc:.4f}")
    print("\n" + classification_report(y_true, y_pred, target_names=["Open", "Closed"]))

    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=["Open", "Closed"], yticklabels=["Open", "Closed"])
    plt.title("Confusion Matrix – Eye Model (Test Set)")
    plt.ylabel("Actual"); plt.xlabel("Predicted")
    plt.tight_layout()
    path = os.path.join(MODELS_DIR, "eye_confusion_matrix.png")
    plt.savefig(path); plt.close()
    print(f"✓ Confusion matrix: {path}")


def plot_history(h1, h2):
    acc   = h1.history["accuracy"]     + h2.history["accuracy"]
    val   = h1.history["val_accuracy"] + h2.history["val_accuracy"]
    loss  = h1.history["loss"]         + h2.history["loss"]
    vloss = h1.history["val_loss"]     + h2.history["val_loss"]
    sep   = len(h1.history["accuracy"])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    for ax, y_tr, y_v, title in [
        (ax1, acc, val, "Accuracy"), (ax2, loss, vloss, "Loss")
    ]:
        ax.plot(y_tr, label="Train")
        ax.plot(y_v,  label="Valid")
        ax.axvline(sep, color="gray", linestyle="--", label="Fine-tune start")
        ax.set_title(f"Eye Model – {title}"); ax.legend()

    plt.tight_layout()
    path = os.path.join(MODELS_DIR, "eye_training_curves.png")
    plt.savefig(path); plt.close()
    print(f"✓ Training curves: {path}")


if __name__ == "__main__":
    train()
