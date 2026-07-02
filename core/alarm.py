# ============================================================
#  core/alarm.py
#  Phát cảnh báo âm thanh khi phát hiện buồn ngủ
# ============================================================

import time
import threading
import os

from config import ALARM_WAV_PATH, ALARM_COOLDOWN_SEC


class AlarmSystem:
    """
    Phát âm thanh cảnh báo không chặn (non-blocking thread).
    Có cooldown để tránh alarm liên tục.
    """

    def __init__(self):
        self._last_alarm_time: float = 0.0
        self._is_playing: bool = False
        self._pygame_ok: bool = self._init_pygame()

    def _init_pygame(self) -> bool:
        try:
            import pygame
            pygame.mixer.init()
            return True
        except Exception as e:
            print(f"[Alarm] pygame không khả dụng: {e}. Sẽ dùng beep hệ thống.")
            return False

    def trigger(self, force: bool = False) -> bool:
        """
        Kích hoạt alarm nếu cooldown đã hết.
        Args:
            force: True → bỏ qua cooldown.
        Returns: True nếu alarm được phát.
        """
        now = time.time()
        if not force and (now - self._last_alarm_time) < ALARM_COOLDOWN_SEC:
            return False

        self._last_alarm_time = now
        thread = threading.Thread(target=self._play, daemon=True)
        thread.start()
        return True

    def _play(self):
        self._is_playing = True
        try:
            if self._pygame_ok and os.path.exists(ALARM_WAV_PATH):
                self._play_pygame()
            else:
                self._play_beep()
        except Exception as e:
            print(f"[Alarm] Lỗi phát âm thanh: {e}")
        finally:
            self._is_playing = False

    def _play_pygame(self):
        import pygame
        pygame.mixer.music.load(ALARM_WAV_PATH)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)

    def _play_beep(self):
        """Fallback: beep hệ thống (hoạt động trên mọi OS)."""
        import sys
        if sys.platform == "win32":
            import winsound
            for _ in range(3):
                winsound.Beep(1000, 300)
                time.sleep(0.1)
        else:
            # Linux / macOS: dùng terminal bell
            print("\a\a\a", end="", flush=True)

    def stop(self):
        """Dừng âm thanh đang phát."""
        try:
            if self._pygame_ok:
                import pygame
                pygame.mixer.music.stop()
        except Exception:
            pass

    @property
    def cooldown_remaining(self) -> float:
        """Giây còn lại trước khi có thể phát alarm tiếp."""
        elapsed = time.time() - self._last_alarm_time
        return max(0.0, ALARM_COOLDOWN_SEC - elapsed)
