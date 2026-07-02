# ============================================================
#  training/evaluate_models.py
#  Đánh giá và so sánh 2 model đã train trên TEST SET độc lập.
#
#  Chạy: python training/evaluate_models.py
#  Yêu cầu: models/eye_model.h5 và models/mouth_model.h5 đã tồn tại.
# ============================================================

import os, sys, random
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Cố định seed ──────────────────────────────────────────────
SEED = 42
os.environ["PYTHONHASHSEED"] = str(SEED)
random.seed(SEED)
import numpy as np
np.random.seed(SEED)
import tensorflow as tf
tf.random.set_seed(SEED)

import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    classification_report, confusion_matrix,
    roc_curve, auc, precision_recall_curve,
)

from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import ImageDataGenerator

from config import (
    TEST_DIR,
    EYE_MODEL_PATH, MOUTH_MODEL_PATH, MODELS_DIR,
    IMG_SIZE, BATCH_SIZE,
)


# ── Generator ─────────────────────────────────────────────────

def load_test_generator(classes: list):
    """Test set: chỉ preprocess_input, không augment, không shuffle."""
    return ImageDataGenerator(
        preprocessing_function=preprocess_input,
    ).flow_from_directory(
        TEST_DIR,
        target_size=IMG_SIZE, batch_size=BATCH_SIZE,
        class_mode="binary", classes=classes,
        shuffle=False,
    )


# ── Evaluate 1 model ──────────────────────────────────────────

def evaluate_model(
    model_path: str,
    classes: list,
    label_names: list,
    title: str,
    cmap: str = "Blues",
) -> dict:
    print(f"\n{'='*52}")
    print(f"  {title}  –  Test Set")
    print(f"{'='*52}")

    if not os.path.exists(model_path):
        print(f"  [SKIP] Model không tồn tại: {model_path}")
        return {}

    model    = tf.keras.models.load_model(model_path)
    test_gen = load_test_generator(classes)

    print(f"  Samples: {test_gen.samples}  |  class_indices: {test_gen.class_indices}")

    y_prob = model.predict(test_gen, verbose=1).flatten()
    y_pred = (y_prob > 0.5).astype(int)
    y_true = test_gen.classes

    # ── Metrics text ──────────────────────────────────────────
    loss, acc = model.evaluate(test_gen, verbose=0)
    print(f"\nTest Loss: {loss:.4f}   Test Accuracy: {acc:.4f} ({acc*100:.2f}%)")
    print("\n" + classification_report(y_true, y_pred, target_names=label_names))

    # ── Plots (3 biểu đồ trên 1 hàng) ────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    sns.heatmap(cm, annot=True, fmt="d", cmap=cmap, ax=axes[0],
                xticklabels=label_names, yticklabels=label_names)
    axes[0].set_title(f"Confusion Matrix\n{title}")
    axes[0].set_ylabel("Actual"); axes[0].set_xlabel("Predicted")

    # ROC curve
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    roc_auc = auc(fpr, tpr)
    axes[1].plot(fpr, tpr, color="darkorange", lw=2,
                 label=f"AUC = {roc_auc:.3f}")
    axes[1].plot([0, 1], [0, 1], color="navy", linestyle="--", lw=1)
    axes[1].set_xlabel("False Positive Rate")
    axes[1].set_ylabel("True Positive Rate")
    axes[1].set_title(f"ROC Curve\n{title}"); axes[1].legend()

    # Precision-Recall curve
    precision, recall, _ = precision_recall_curve(y_true, y_prob)
    pr_auc = auc(recall, precision)
    axes[2].plot(recall, precision, color="green", lw=2,
                 label=f"AUC = {pr_auc:.3f}")
    axes[2].set_xlabel("Recall"); axes[2].set_ylabel("Precision")
    axes[2].set_title(f"Precision-Recall Curve\n{title}"); axes[2].legend()

    plt.tight_layout()
    fname = title.lower().replace(" ", "_") + "_evaluation.png"
    fpath = os.path.join(MODELS_DIR, fname)
    plt.savefig(fpath, dpi=150); plt.close()
    print(f"✓ Biểu đồ lưu: {fpath}")

    return {"accuracy": float(acc), "roc_auc": roc_auc, "pr_auc": pr_auc}


# ── So sánh 2 model ───────────────────────────────────────────

def compare_models(eye_metrics: dict, mouth_metrics: dict):
    if not eye_metrics or not mouth_metrics:
        print("\n[SKIP] Thiếu metrics – bỏ qua bước so sánh.")
        return

    print(f"\n{'='*52}")
    print("  So sánh Eye Model vs Mouth Model (Test Set)")
    print(f"{'='*52}")
    print(f"{'Metric':<20} {'Eye Model':>12} {'Mouth Model':>12}")
    print("-" * 46)
    for key in eye_metrics:
        print(f"{key:<20} {eye_metrics[key]:>12.4f} {mouth_metrics[key]:>12.4f}")

    labels     = list(eye_metrics.keys())
    eye_vals   = list(eye_metrics.values())
    mouth_vals = list(mouth_metrics.values())
    x = np.arange(len(labels))
    w = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))
    bars_e = ax.bar(x - w/2, eye_vals,   w, label="Eye Model",   color="steelblue")
    bars_m = ax.bar(x + w/2, mouth_vals, w, label="Mouth Model", color="darkorange")
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.12)
    ax.set_title("So sánh Eye Model vs Mouth Model (Test Set)")
    ax.legend()

    for bar in list(bars_e) + list(bars_m):
        ax.annotate(f"{bar.get_height():.3f}",
                    (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    fpath = os.path.join(MODELS_DIR, "model_comparison.png")
    plt.savefig(fpath, dpi=150); plt.close()
    print(f"\n✓ Biểu đồ so sánh: {fpath}")


# ── Entry point ───────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs(MODELS_DIR, exist_ok=True)

    eye_metrics = evaluate_model(
        model_path  = EYE_MODEL_PATH,
        classes     = ["open", "closed"],
        label_names = ["Open", "Closed"],
        title       = "Eye Model",
        cmap        = "Blues",
    )

    mouth_metrics = evaluate_model(
        model_path  = MOUTH_MODEL_PATH,
        classes     = ["no_yawn", "yawn"],
        label_names = ["No_Yawn", "Yawn"],
        title       = "Mouth Model",
        cmap        = "Oranges",
    )

    compare_models(eye_metrics, mouth_metrics)
