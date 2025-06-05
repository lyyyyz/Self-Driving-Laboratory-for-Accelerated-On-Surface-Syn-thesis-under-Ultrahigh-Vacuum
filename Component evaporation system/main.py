# main.py
import sys
from PyQt5.QtWidgets import QApplication
from ControlPanel import ControlPanel  # 引入ControlPanel类

def main():
    app = QApplication(sys.argv)
    panel = ControlPanel()
    panel.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
