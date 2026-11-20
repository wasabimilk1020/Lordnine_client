import sys
import time
from pathlib import Path
from datetime import datetime

from PIL import ImageGrab
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QPen, QColor


# 검색 영역 확장 크기
SEARCH_MARGIN = 100


class ImageSelector(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)

        # 주 모니터 전체 영역
        self.screen_rect = QApplication.primaryScreen().geometry()
        self.setGeometry(self.screen_rect)

        self.start = None
        self.end = None
        self.region = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start = event.pos()
            self.end = event.pos()

    def mouseMoveEvent(self, event):
        if self.start is not None:
            self.end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.start is not None:
            rect = QRect(self.start, event.pos()).normalized()

            if rect.width() > 0 and rect.height() > 0:
                pos = self.mapToGlobal(rect.topLeft())

                self.region = (
                    pos.x(),
                    pos.y(),
                    rect.width(),
                    rect.height()
                )
                self.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))

        if self.start is not None and self.end is not None:
            rect = QRect(self.start, self.end).normalized()

            painter.fillRect(rect, QColor(0, 150, 255, 35))
            painter.setPen(QPen(QColor(0, 150, 255), 2))
            painter.drawRect(rect)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()


def select_image_region():
    selector = ImageSelector()

    if selector.exec_() != QDialog.Accepted:
        return None

    x, y, width, height = selector.region

    # 화면 크기 및 경계
    screen = selector.screen_rect
    screen_left = screen.x()
    screen_top = screen.y()
    screen_right = screen.x() + screen.width()
    screen_bottom = screen.y() + screen.height()

    # 검색 영역을 상하좌우 100픽셀 확장
    # 단, 화면 밖으로 나가지 않도록 제한
    region_x = max(screen_left, x - SEARCH_MARGIN)
    region_y = max(screen_top, y - SEARCH_MARGIN)

    region_right = min(
        screen_right, x + width + SEARCH_MARGIN
    )
    region_bottom = min(
        screen_bottom, y + height + SEARCH_MARGIN
    )

    region_width = region_right - region_x
    region_height = region_bottom - region_y

    search_region = (
        region_x,
        region_y,
        region_width,
        region_height
    )

    # 오버레이가 사라진 후 캡처
    time.sleep(0.2)

    # 드래그한 원본 영역만 이미지로 저장
    img = ImageGrab.grab(
        bbox=(x, y, x + width, y + height)
    )

    # image_files 폴더에 저장
    output_dir = Path(__file__).resolve().parent.parent / "image_files"
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"template_{datetime.now():%Y%m%d_%H%M%S}.png"
    output_path = output_dir / filename

    img.save(str(output_path))

    print("\n===== 이미지 저장 완료 =====")
    print("저장 경로:", output_path)
    print(f"템플릿 영역: ({x}, {y}, {width}, {height})")
    print(f"검색 영역: {search_region}")

    print("\n===== searchImg 호출 코드 =====")
    print(
        f"searchImg('{filename}', beforeDelay=0, "
        f"afterDelay=0, _region={search_region})"
    )

    return search_region


if __name__ == "__main__":
    app = QApplication.instance() or QApplication(sys.argv)

    print("3초 후 영역 선택 시작")
    time.sleep(3)

    select_image_region()