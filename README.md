# Driver Drowsiness Detection System

Hệ thống phát hiện buồn ngủ của tài xế sử dụng Deep Learning (MobileNetV2 + MediaPipe).

## Cấu trúc dự án

```
drowsiness_detection/
├── dataset/            ← Kaggle Yawn Eye Dataset
├── models/             ← File .h5 sau khi train
├── training/           ← Script huấn luyện & đánh giá
├── core/               ← Logic chính (detector, predictor, score)
├── gui/                 ← Giao diện 
├── logs/               ← CSV thống kê
├── config.py           ← Tất cả hằng số
└── main.py             ← Chạy không cần GUI
```

## Cài đặt

```bash
# Tạo virtual environment
python -m venv .venv
source .venv/bin/activate       # Linux/macOS
.venv\Scripts\activate.bat           # Windows

# Cài thư viện
pip install -r requirements.txt
```

## Bước 1: Chuẩn bị Dataset

1. Download dataset: https://drive.google.com/drive/folders/1NpMwIarw7To-9PmgRwCnoWVoaOg4OhV_?usp=sharing

## Bước 2: Huấn luyện Model

```bash
# Train Eye Model (Open/Closed)
python training/train_eye_model.py

# Train Mouth Model (Yawn/No_Yawn)
python training/train_mouth_model.py

# Đánh giá & so sánh 2 model
python training/evaluate_models.py
```

Model tốt nhất sẽ được lưu tự động vào `models/eye_model.h5` và `models/mouth_model.h5`.

## Bước 3: Chạy hệ thống

**Chế độ console:**
```bash
python main.py
```

**Chế độ GUI:**
```bash
streamlit run gui/app.py
```

Nhấn `Q` hoặc `ESC` để thoát.

## Alert Score Logic

| Score  | Trạng thái | Ý nghĩa              |
|--------|------------|----------------------|
| ≥ 70   | NORMAL     | Tài xế tỉnh táo      |
| 40–69  | TIRED      | Bắt đầu mệt mỏi      |
| < 40   | DROWSY     | Nguy hiểm – dừng xe  |

**Công thức tính penalty mỗi frame:**
- Mắt nhắm liên tục ≥ 15 frames → `-2 điểm/frame`
- Đang ngáp → `-YAWN_PENALTY × scale / 30` (tuyến tính theo số lần ngáp trong 60s)
- Trạng thái bình thường → `+0.5 điểm/frame` (hồi phục)

Tất cả threshold có thể điều chỉnh trong `config.py`.

