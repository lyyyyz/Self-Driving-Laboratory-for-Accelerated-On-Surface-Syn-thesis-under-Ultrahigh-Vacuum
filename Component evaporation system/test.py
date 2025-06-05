import sys
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox, QPushButton, QVBoxLayout

class DemoWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("弹窗测试")
        self.setGeometry(500, 300, 300, 100)

        layout = QVBoxLayout()
        btn = QPushButton("显示蒸发完成弹窗")
        btn.clicked.connect(self.show_popup)
        layout.addWidget(btn)

        self.setLayout(layout)

    def show_popup(self):
        current = 0.85  # 示例电流
        msg = QMessageBox(self)
        msg.setWindowTitle("蒸发完成")
        msg.setText(f"蒸发稳定，当前电流为: {current:.2f} A")
        msg.setIcon(QMessageBox.Information)
        msg.exec_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DemoWindow()
    window.show()
    sys.exit(app.exec_())
