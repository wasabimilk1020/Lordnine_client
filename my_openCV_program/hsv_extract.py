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

    # 오버레이 제거 후 캡처
    time.sleep(0.2)

    img = ImageGrab.grab(
        bbox=(x, y, x + width, y + height)
    )
    img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    # HSV 변환
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # HSV 범위 자동 계산
    pixels = hsv.reshape(-1, 3)

    # H는 원형 값이므로 sin, cos로 변환
    # 채도가 낮은 색상에서는 H의 영향을 줄임
    h = pixels[:, 0].astype(np.float32) * (2 * np.pi / 180)
    s = pixels[:, 1].astype(np.float32) / 255.0
    v = pixels[:, 2].astype(np.float32) / 255.0

    features = np.column_stack((
        np.cos(h) * s,
        np.sin(h) * s,
        s,
        v
    )).astype(np.float32)

    # 최대 약 5000개 픽셀을 사용하여 색상 분류
    step = max(1, len(pixels) // 5000)
    samples = features[::step]
    sample_pixels = pixels[::step]

    # K-means로 3개의 대표 색상군 분류
    criteria = (
        cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
        50,
        0.01
    )

    _, labels, _ = cv2.kmeans(
        samples, 3, None, criteria, 5,
        cv2.KMEANS_PP_CENTERS
    )

    # 픽셀 수가 가장 많은 색상군 선택
    labels = labels.ravel()
    counts = np.bincount(labels, minlength=3)
    dominant_pixels = sample_pixels[labels == np.argmax(counts)]

    # 선택된 색상군의 HSV 범위 계산
    low = np.percentile(dominant_pixels, 5, axis=0)
    high = np.percentile(dominant_pixels, 95, axis=0)

    # 실제 화면의 색상 변화를 고려해 여유값 추가
    margin = np.array([5, 15, 15])

    lower = np.maximum(0, np.floor(low).astype(int) - margin)
    upper = np.minimum(
        [179, 255, 255],
        np.ceil(high).astype(int) + margin
    )

    # 흰색·회색처럼 채도가 낮으면 H값은 의미가 적음
    if np.median(dominant_pixels[:, 1]) < 30:
        lower[0] = 0
        upper[0] = 179

    lower = tuple(lower)
    upper = tuple(upper)

    # HSV 마스크 생성
    mask = cv2.inRange(
        hsv,
        np.array(lower, dtype=np.uint8),
        np.array(upper, dtype=np.uint8)
    )

    # 노이즈 제거
    kernel = np.ones((3, 3), np.uint8)
    clean_mask = cv2.morphologyEx(
        mask, cv2.MORPH_OPEN, kernel
    )

    # 컨투어 검출
    contours, _ = cv2.findContours(
        clean_mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    # 결과 이미지
    detected = img.copy()
    center = None

    if contours:
        cnt = max(contours, key=cv2.contourArea)

        if cv2.contourArea(cnt) >= min_area:
            M = cv2.moments(cnt)

            if M["m00"] != 0:
                # 선택 영역 내부 좌표
                local_x = int(M["m10"] / M["m00"])
                local_y = int(M["m01"] / M["m00"])

                # 실제 화면 절대 좌표
                cx = local_x + x
                cy = local_y + y

                center = (cx, cy)

                # 녹색 윤곽선
                cv2.drawContours(
                    detected, [cnt], -1, (0, 255, 0), 2
                )

                # 빨간색 중심점
                cv2.circle(
                    detected,
                    (local_x, local_y),
                    5, (0, 0, 255), -1
                )

                # 중심 좌표 표시
                cv2.putText(
                    detected,
                    f"({cx}, {cy})",
                    (max(0, local_x - 30),
                     max(15, local_y - 12)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (0, 0, 255), 1
                )

    # ===== 결과 이미지 구성 =====

    mask_color = cv2.cvtColor(clean_mask, cv2.COLOR_GRAY2BGR)

    def add_title(image, title):
        return cv2.copyMakeBorder(
            image, 32, 0, 0, 0,
            cv2.BORDER_CONSTANT,
            value=(40, 40, 40)
        )

    original_view = add_title(img, "Original")
    mask_view = add_title(mask_color, "HSV Mask")
    detected_view = add_title(detected, "Detected")

    for view, title in [
        (original_view, "Original"),
        (mask_view, "HSV Mask"),
        (detected_view, "Detected")
    ]:
        cv2.putText(
            view, title, (10, 23),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6, (255, 255, 255), 1
        )

    # 세 이미지를 좌우로 결합
    debug_image = np.hstack([
        original_view,
        mask_view,
        detected_view
    ])

    # 작은 이미지 확대
    if width < 300:
        debug_image = cv2.resize(
            debug_image, None,
            fx=2, fy=2,
            interpolation=cv2.INTER_NEAREST
        )

    # ===== 콘솔 출력 =====

    print("\n===== HSV 분석 결과 =====")
    print(f"영역: ({x}, {y}, {width}, {height})")
    print(f"lower: {lower}")
    print(f"upper: {upper}")
    print(f"검출 중심 좌표: {center}")

    print("\n===== 함수 호출 코드 =====")
    print(
        f"find_hsv_center({x}, {y}, {width}, {height}, "
        f"lower={lower}, upper={upper}, min_area={min_area})"
    )

    # 이미지 저장
    cv2.imwrite("hsv_debug.png", debug_image)

    # 이미지 화면 출력
    cv2.namedWindow("HSV Debug", cv2.WINDOW_NORMAL)
    cv2.imshow("HSV Debug", debug_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return x, y, width, height, lower, upper


if __name__ == "__main__":
    app = QApplication.instance() or QApplication(sys.argv)

    print("3초 후 영역 선택 시작")
    time.sleep(3)

    select_hsv_region()


