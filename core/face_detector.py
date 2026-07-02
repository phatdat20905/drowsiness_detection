# ============================================================
#  core/face_detector.py
#  Wrapper cho MediaPipe Face Mesh – detect landmarks khuôn mặt
#
#  FIX: mediapipe >= 0.10.x đã bỏ mp.solutions trên một số build.
#       Dùng import trực tiếp từ mediapipe.python.solutions thay thế.
# ============================================================

import cv2
import numpy as np
from dataclasses import dataclass
from typing import Optional, List, Tuple

# ── Import an toàn cho mọi version mediapipe ─────────────────
try:
    import mediapipe as mp
    # Thử solutions API (mediapipe <= 0.10.14 / legacy)
    _face_mesh_module   = mp.solutions.face_mesh
    _drawing_module     = mp.solutions.drawing_utils
    _MEDIAPIPE_LEGACY   = True
except AttributeError:
    # mediapipe >= 0.10.15+ đã xóa solutions, dùng tasks API
    raise ImportError(
        "mediapipe version này không hỗ trợ solutions API.\n"
        "Vui lòng cài đúng version:\n"
        "  pip install 'mediapipe==0.10.14'"
    )


@dataclass
class FaceResult:
    """Kết quả detect một khuôn mặt."""
    landmarks: object          # mediapipe NormalizedLandmarkList
    frame_h: int
    frame_w: int

    def get_landmark_px(self, idx: int) -> Tuple[int, int]:
        """Trả về tọa độ pixel (x, y) của landmark thứ idx."""
        lm = self.landmarks.landmark[idx]
        return int(lm.x * self.frame_w), int(lm.y * self.frame_h)

    def get_landmarks_px(self, indices: List[int]) -> List[Tuple[int, int]]:
        return [self.get_landmark_px(i) for i in indices]

    def get_bounding_box(
        self,
        indices: List[int],
        padding: float = 0.15,
    ) -> Tuple[int, int, int, int]:
        """
        Tính bounding box bao quanh tập landmarks.
        Returns: (x1, y1, x2, y2) đã clip trong frame.
        """
        pts = self.get_landmarks_px(indices)
        xs  = [p[0] for p in pts]
        ys  = [p[1] for p in pts]

        w_box = max(xs) - min(xs)
        h_box = max(ys) - min(ys)

        pad_x = max(int(w_box * padding), 5)
        pad_y = max(int(h_box * padding), 5)

        x1 = max(0, min(xs) - pad_x)
        y1 = max(0, min(ys) - pad_y)
        x2 = min(self.frame_w, max(xs) + pad_x)
        y2 = min(self.frame_h, max(ys) + pad_y)
        return x1, y1, x2, y2


class FaceDetector:
    """
    Phát hiện khuôn mặt và trả về 478 landmarks dùng MediaPipe Face Mesh.
    Chỉ xử lý 1 khuôn mặt đầu tiên trong frame (1 tài xế).

    Yêu cầu: mediapipe == 0.10.14
      pip install "mediapipe==0.10.14"
    """

    def __init__(
        self,
        static_image_mode: bool = False,
        max_num_faces: int = 1,
        refine_landmarks: bool = True,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ):
        self._mp_face_mesh = _face_mesh_module
        self._mp_draw      = _drawing_module
        self._draw_spec    = self._mp_draw.DrawingSpec(
            color=(0, 255, 0), thickness=1, circle_radius=1
        )

        self.face_mesh = self._mp_face_mesh.FaceMesh(
            static_image_mode=static_image_mode,
            max_num_faces=max_num_faces,
            refine_landmarks=refine_landmarks,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

    def detect(self, frame: np.ndarray) -> Optional[FaceResult]:
        """
        Xử lý 1 frame BGR.
        Returns FaceResult nếu tìm thấy khuôn mặt, None nếu không.
        """
        h, w = frame.shape[:2]

        # MediaPipe yêu cầu RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = self.face_mesh.process(rgb)
        rgb.flags.writeable = True

        if not results.multi_face_landmarks:
            return None

        return FaceResult(
            landmarks=results.multi_face_landmarks[0],
            frame_h=h,
            frame_w=w,
        )

    def draw_landmarks(self, frame: np.ndarray, face: FaceResult) -> np.ndarray:
        """Vẽ toàn bộ landmarks lên frame (dùng để debug)."""
        self._mp_draw.draw_landmarks(
            frame,
            face.landmarks,
            self._mp_face_mesh.FACEMESH_CONTOURS,
            self._draw_spec,
            self._draw_spec,
        )
        return frame

    def close(self):
        """Giải phóng tài nguyên."""
        self.face_mesh.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
