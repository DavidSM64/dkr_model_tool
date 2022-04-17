from model import *
from preview_window import *
from PyQt5.QtWidgets import QApplication

def preview_level(model):
    app = QApplication([])
    widget = DkrPreviewWidget()
    widget.load_model(model)
    widget.show()
    app.exec_()
