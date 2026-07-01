# ============================================================
#  config.py  –  Hằng số toàn cục cho hệ thống
# ============================================================

import os

# ── Đường dẫn ────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
MODELS_DIR  = os.path.join(BASE_DIR, "models")
LOGS_DIR    = os.path.join(BASE_DIR, "logs")
ASSETS_DIR  = os.path.join(BASE_DIR, "assets")

TRAIN_DIR = os.path.join(DATASET_DIR, "train")
VALID_DIR = os.path.join(DATASET_DIR, "valid")
TEST_DIR  = os.path.join(DATASET_DIR, "test")

EYE_MODEL_PATH   = os.path.join(MODELS_DIR, "eye_model.h5")
MOUTH_MODEL_PATH = os.path.join(MODELS_DIR, "mouth_model.h5")

ALARM_WAV_PATH   = os.path.join(ASSETS_DIR, "alarm.wav")
DAILY_STATS_CSV  = os.path.join(LOGS_DIR, "daily_stats.csv")
ALERTS_CSV       = os.path.join(LOGS_DIR, "alerts.csv")

# ── Reproducibility ──────────────────────────────────────────
# Seed cố định cho NumPy, TensorFlow, Python random.
# Dùng xuyên suốt: train/val/test split, data augmentation,
# khởi tạo trọng số, shuffle.
RANDOM_SEED = 42

# ── Mô hình ──────────────────────────────────────────────────
IMG_SIZE    = (224, 224)          # Kích thước đầu vào MobileNetV2
BATCH_SIZE  = 32
EPOCHS      = 20
LEARNING_RATE = 1e-4


# ── MediaPipe Face Mesh ───────────────────────────────────────
# Landmark indices ĐỒNG BỘ với test2.py (nguồn tham chiếu real-time)
# Mắt trái (theo góc nhìn camera = mắt phải người dùng trong gương)
L_OUTER, L_INNER   = 33, 133
L_UPPER_1, L_LOWER_1 = 160, 144
L_UPPER_2, L_LOWER_2 = 158, 153

# Mắt phải
R_OUTER, R_INNER   = 263, 362
R_UPPER_1, R_LOWER_1 = 387, 373
R_UPPER_2, R_LOWER_2 = 385, 380

# Miệng
P_LEFT, P_RIGHT     = 61, 291
P_UPPER_1, P_LOWER_1 = 81, 178
P_UPPER_2, P_LOWER_2 = 13, 14
P_UPPER_3, P_LOWER_3 = 311, 402

# Head pose
NOSE     = 1
HEAD_TOP = 10
CHIN     = 152

# Bounding-box landmark groups (dùng để CROP ảnh cho CNN, khác với
# landmark points dùng để TÍNH EAR/MAR ở trên)
LEFT_EYE_LANDMARKS  = [L_OUTER, L_INNER, L_UPPER_1, L_LOWER_1, L_UPPER_2, L_LOWER_2]
RIGHT_EYE_LANDMARKS = [R_OUTER, R_INNER, R_UPPER_1, R_LOWER_1, R_UPPER_2, R_LOWER_2]
MOUTH_LANDMARKS     = [P_LEFT, P_RIGHT, P_UPPER_1, P_LOWER_1,
                        P_UPPER_2, P_LOWER_2, P_UPPER_3, P_LOWER_3]

# Padding khi crop ROI (tỉ lệ so với kích thước bounding box)
EYE_PADDING   = 0.45   # mắt cần padding lớn hơn vì bbox landmark rất nhỏ
MOUTH_PADDING = 0.25

# ── Ngưỡng đặc trưng hình học (ĐỒNG BỘ với test2.py) ──────────
# Các ngưỡng này dùng làm ĐẶC TRƯNG HỖ TRỢ / lớp cảnh báo bổ sung,
# KHÔNG thay thế quyết định của model deep learning.
EAR_THRESHOLD       = 0.21
EYE_CLOSED_FRAMES   = 15
BLINK_MAX_FRAMES    = 7
BLINK_RATE_THRESHOLD = 35      # lần/phút

MAR_THRESHOLD       = 0.6
YAWN_FRAMES          = 30

DISTRACTED_FRAMES   = 45       # ~1.5s ở 30 FPS

# Ngưỡng head-pose ratio (giữ nguyên từ test2.py)
HEAD_HORIZONTAL_RIGHT = 0.65
HEAD_HORIZONTAL_LEFT  = 1.60
HEAD_VERTICAL_UP      = 0.65
HEAD_VERTICAL_DOWN    = 1.35

# ── Fusion: Kết hợp Model CNN + Đặc trưng hình học ────────────
# Trọng số kết hợp xác suất "closed"/"yawn" từ CNN với tín hiệu
# nhị phân từ EAR/MAR. fusion_prob = w_cnn*p_cnn + w_geo*p_geo
FUSION_WEIGHT_CNN = 0.65
FUSION_WEIGHT_GEO = 0.35

# ── Alert Score ───────────────────────────────────────────────
ALERT_SCORE_MAX = 100

CLOSED_CONSEC_FRAMES = 15
CLOSED_PENALTY_PER_FRAME = 2.0

YAWN_WINDOW_SEC = 60
YAWN_PENALTY_PER_COUNT = 10.0

SCORE_RECOVERY_RATE = 0.5

# Phạt thêm khi mất tập trung (head pose) hoặc mỏi mắt sớm (blink rate)
DISTRACTION_PENALTY_PER_FRAME = 1.0
FATIGUE_BLINK_PENALTY = 0.3   # mỗi frame khi blink_rate vượt ngưỡng

# ── Ngưỡng phân loại trạng thái ──────────────────────────────
TIRED_THRESHOLD  = 70
DROWSY_THRESHOLD = 40

# ── Cảnh báo ─────────────────────────────────────────────────
ALARM_COOLDOWN_SEC = 5

# ── Xác suất phân loại (confidence threshold cho hiển thị) ───
EYE_CONF_THRESHOLD   = 0.70
MOUTH_CONF_THRESHOLD = 0.50

# ── Hiển thị ─────────────────────────────────────────────────
FRAME_WIDTH  = 640
FRAME_HEIGHT = 480
DISPLAY_FPS  = 30

COLOR_NORMAL = (0, 200, 0)
COLOR_TIRED  = (0, 165, 255)
COLOR_DROWSY = (0, 0, 220)
COLOR_TEXT   = (255, 255, 255)
