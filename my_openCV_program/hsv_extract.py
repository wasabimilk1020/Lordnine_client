import sys
import time
import cv2
import numpy as np

from PIL import ImageGrab
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QPen, QColor


class HSVSelector(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)

        self.setGeometry(QApplication.primaryScreen().geometry())

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
                    pos.x(), pos.y(),
                    rect.width(), rect.height()
                )
                self.accept()

    def paintEvent(self, event):
        painter = QPainter(self)

        # 거의 투명하게 유지하면서 마우스 입력 받기
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))

        if self.start is not None and self.end is not None:
            rect = QRect(self.start, self.end).normalized()

            painter.fillRect(rect, QColor(0, 150, 255, 35))
            painter.setPen(QPen(QColor(0, 150, 255), 2))
            painter.drawRect(rect)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()


def select_hsv_region(min_area=300):
    selector = HSVSelector()

    if selector.exec_() != QDialog.Accepted:
        return None

    x, y, width, height = selector.region

    # 오버레이가 사라진 후 캡처
    time.sleep(0.2)

    img = ImageGrab.grab(
        bbox=(x, y, x + width, y + height)
    )

    img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # HSV 분포의 5~95백분위수
    pixels = hsv.reshape(-1, 3)

    lower = tuple(
        np.floor(np.percentile(pixels, 5, axis=0)).astype(int)
    )
    upper = tuple(
        np.ceil(np.percentile(pixels, 95, axis=0)).astype(int)
    )

    print("\n===== HSV 분석 결과 =====")
    print(f"영역: ({x}, {y}, {width}, {height})")
    print(f"lower: {lower}")
    print(f"upper: {upper}")

    print("\n===== 함수 호출 코드 =====")
    print(
        f"find_hsv_center({x}, {y}, {width}, {height}, "
        f"lower={lower}, upper={upper}, min_area={min_area})"
    )

    return x, y, width, height, lower, upper


if __name__ == "__main__":
    app = QApplication.instance() or QApplication(sys.argv)

    print("3초 후 영역 선택 시작")
    time.sleep(3)
    
    select_hsv_region()