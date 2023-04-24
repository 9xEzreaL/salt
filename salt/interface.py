import cv2
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsView, QGraphicsScene
from PyQt5.QtGui import QImage, QPixmap, QPainter, QWheelEvent, QMouseEvent, QPen
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtWidgets import (
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLabel,
    QRadioButton,
    QComboBox,
)


class CustomGraphicsView(QGraphicsView):
    def __init__(self, editor):
        super(CustomGraphicsView, self).__init__()

        self.editor = editor
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setRenderHint(QPainter.TextAntialiasing)

        self.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing, True)
        self.setOptimizationFlag(QGraphicsView.DontSavePainterState, True)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setInteractive(True)

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.image_item = None
        self.flag = False

    def set_image(self, q_img):
        pixmap = QPixmap.fromImage(q_img)
        if self.image_item:
            self.image_item.setPixmap(pixmap)
            self.setSceneRect(QRectF(pixmap.rect()))
        else:
            self.image_item = self.scene.addPixmap(pixmap)
            self.setSceneRect(QRectF(pixmap.rect()))

    def wheelEvent(self, event: QWheelEvent):
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor
        old_pos = self.mapToScene(event.pos())
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
        self.scale(zoom_factor, zoom_factor)
        new_pos = self.mapToScene(event.pos())
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())

    def imshow(self, img):
        height, width, channel = img.shape
        bytes_per_line = 3 * width
        q_img = QImage(
            img.data, width, height, bytes_per_line, QImage.Format_RGB888
        ).rgbSwapped()
        self.set_image(q_img)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        pos = event.pos()
        pos_in_item = self.mapToScene(pos) - self.image_item.pos()
        x, y = pos_in_item.x(), pos_in_item.y()
        if self.mode == 'point':
            self.flag = False
            if event.button() == Qt.LeftButton:
                label = 1
            elif event.button() == Qt.RightButton:
                label = 0
            self.editor.add_click([int(x), int(y)], label)
        elif self.mode == 'paint':
            self.flag = True
            self.editor.curr_inputs.add_paint_mask(int(x), int(y))
        elif self.mode == 'eraser':
            self.flag = True
            self.editor.curr_inputs.era_paint_mask(int(x), int(y))
        self.editor.online_draw()
        self.imshow(self.editor.display)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pos = event.pos()
        pos_in_item = self.mapToScene(pos) - self.image_item.pos()
        x, y = pos_in_item.x(), pos_in_item.y()
        if self.flag:
            if self.mode == 'paint':
                self.editor.curr_inputs.add_paint_mask(int(x), int(y))
            elif self.mode == 'eraser':
                self.editor.curr_inputs.era_paint_mask(int(x), int(y))
            self.editor.online_draw()
            self.imshow(self.editor.display)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.flag = False

    def update_PPE_mode(self, mode):
        self.mode = mode


class ApplicationInterface(QWidget):
    def __init__(self, app, editor, panel_size=(1920, 1080)):
        super(ApplicationInterface, self).__init__()

        self.app = app
        self.editor = editor
        self.panel_size = panel_size

        self.layout = QVBoxLayout()

        self.top_bar = self.get_top_bar()
        self.layout.addWidget(self.top_bar)

        self.main_window = QHBoxLayout()

        self.graphics_view = CustomGraphicsView(editor)
        self.main_window.addWidget(self.graphics_view)

        self.panel = self.get_side_panel()
        self.main_window.addWidget(self.panel)
        self.layout.addLayout(self.main_window)

        self.status_panel = self.get_review_side_panel()
        self.main_window.addWidget(self.status_panel)
        self.layout.addLayout(self.main_window)

        self.label = QLabel()
        self.label.resize(200, 100)
        self.label.setText(f'{self.editor.name}    ...     1/{self.editor.dataset_explorer.get_num_images()}    ... {self.editor.get_status_name()}')
        self.layout.addWidget(self.label)

        self.setLayout(self.layout)

        self.graphics_view.imshow(self.editor.display)
        self.execute_mode()


    def reset(self):
        self.editor.reset()
        self.graphics_view.imshow(self.editor.display)

    def add(self):
        self.editor.save_ann()
        self.editor.reset()
        self.graphics_view.imshow(self.editor.display)

    def next_image(self):
        self.editor.next_image()
        self._update_label(self.editor.name, self.editor.image_id)
        self.graphics_view.imshow(self.editor.display)

    def prev_image(self):
        self.editor.prev_image()
        self._update_label(self.editor.name, self.editor.image_id)
        self.graphics_view.imshow(self.editor.display)

    def toggle(self):
        self.editor.toggle()
        self.graphics_view.imshow(self.editor.display)

    def transparency_up(self):
        self.editor.step_up_transparency()
        self.graphics_view.imshow(self.editor.display)

    def transparency_down(self):
        self.editor.step_down_transparency()
        self.graphics_view.imshow(self.editor.display)

    def save_all(self):
        self.editor.save()
        self._update_label(self.editor.name, self.editor.image_id)

    def get_top_bar(self):
        top_bar = QWidget()
        button_layout = QHBoxLayout(top_bar)
        self.layout.addLayout(button_layout)
        buttons = [
            ("Add", lambda: self.add()),
            ("Reset", lambda: self.reset()),
            ("Prev", lambda: self.prev_image()),
            ("Next", lambda: self.next_image()),
            ("Toggle", lambda: self.toggle()),
            ("Transparency Up", lambda: self.transparency_up()),
            ("Transparency Down", lambda: self.transparency_down()),
            ("Save", lambda: self.save_all()),
            ("Delete Annotations", lambda: self.delete_annotations())
        ]
        for button, lmb in buttons:
            bt = QPushButton(button)
            bt.clicked.connect(lmb)
            button_layout.addWidget(bt)

        self.box = QComboBox(top_bar)
        self.box.addItems([str(x + 1) for x in range(self.editor.dataset_explorer.get_num_images())])
        self.box.currentIndexChanged.connect(self.jump2slice)

        self.point_paint_era = QComboBox(top_bar)
        self.point_paint_era.addItems(['point', 'paint', 'eraser'])
        self.point_paint_era.setCurrentIndex(0)
        self.point_paint_era.currentIndexChanged.connect(self.execute_mode)

        button_layout.addWidget(self.box)
        button_layout.addWidget(self.point_paint_era)

        return top_bar

    def get_side_panel(self):
        panel = QWidget()
        panel_layout = QVBoxLayout(panel)
        categories, colors = self.editor.get_categories(get_colors=True)
        label_array = []
        for i, _ in enumerate(categories):
            label_array.append(QRadioButton(categories[i]))
            label_array[i].clicked.connect(
                lambda state, x=categories[i]: self.editor.select_category(x)
            )
            label_array[i].setStyleSheet(
                "background-color: rgba({},{},{},0.6)".format(*colors[i][::-1])
            )
            panel_layout.addWidget(label_array[i])
        return panel

    def get_review_side_panel(self):
        panel = QWidget()
        panel_layout = QVBoxLayout(panel)
        label_array = []
        review_categories = ['not label', 'primary label', 'secondary label', 'final label']
        for i, _ in enumerate(review_categories):
            label_array.append(QRadioButton(review_categories[i]))
            label_array[i].clicked.connect(
                lambda state, x=review_categories[i]: self.editor.select_status(x)
            )
            panel_layout.addWidget(label_array[i])

        return panel

    def _update_label(self, name, image_id):
        self.label.setText(f'{name}     ...     {image_id+1}/{self.editor.dataset_explorer.get_num_images()}    ... {self.editor.get_status_name()}')
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

    def delete_annotations(self):
        self.editor.delete_annotations()

    def jump2slice(self):
        self.editor.jump2image(int(self.box.currentText()))
        self._update_label(self.editor.name, self.editor.image_id)
        self.graphics_view.imshow(self.editor.display)

    def execute_mode(self):
        self.graphics_view.update_PPE_mode(self.point_paint_era.currentText())
        # print(self.point_paint_era.currentText())
        # pass

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.app.quit()
        if event.key() == Qt.Key_A:
            self.prev_image()
        if event.key() == Qt.Key_D:
            self.next_image()
        if event.key() == Qt.Key_K:
            self.transparency_down()
        if event.key() == Qt.Key_L:
            self.transparency_up()
        if event.key() == Qt.Key_N:
            self.add()
        if event.key() == Qt.Key_R:
            self.reset()
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_S:
            self.save_all()
        # elif event.key() == Qt.Key_Space:
        #     # Do something if the space bar is pressed
        #     pass
