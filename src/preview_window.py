import math
from OpenGL.GLU import *
from OpenGL.GL import *
import numpy as np
from PyQt5.QtGui import QOpenGLWindow
from PyQt5.QtCore import QSize
from PyQt5.Qt import QTimer
from preview_window_controls import *
from preview_window_render_model import *
from model import *

# ============================== OpenGL Window =============================== #

class DkrPreviewWidget(QOpenGLWindow):
    def __init__(self):
        super(DkrPreviewWidget, self).__init__()
        self.setMinimumSize(QSize(640, 480))
        self.renderModel = None
        self.showAxis = True
        self.controls = DkrPreviewControls()
        self.targetFPS = 60
        QTimer.singleShot(1000 // self.targetFPS, self.updateControls)

    def updateControls(self):
        if self.controls.active:
            if self.controls.is_flag_set(CONTROL_FLAG_FORWARD):
                self.controls.move_ahead(1)
            elif self.controls.is_flag_set(CONTROL_FLAG_BACKWARD):
                self.controls.move_ahead(-1)
            if self.controls.is_flag_set(CONTROL_FLAG_LEFT):
                self.controls.move_left(1)
            elif self.controls.is_flag_set(CONTROL_FLAG_RIGHT):
                self.controls.move_left(-1)
            if self.controls.zoomAmount != 0:
                self.controls.move_ahead(self.controls.zoomAmount / 100)
                self.controls.zoomAmount = 0
            self.controls.forceUpdate = False
            self.update() # Only repaint the scene if needed.
        QTimer.singleShot(1000 // self.targetFPS, self.updateControls)
    
    def mouseMoveEvent(self, event):
        if self.controls.is_flag_set(CONTROL_FLAG_ROTATING_CAMERA):
            self.controls.rotate_camera(event.x(), event.y())

    def mousePressEvent(self, event):
        self.controls.handle_mouse_down(event.button(), event.x(), event.y())

    def mouseReleaseEvent(self, event):
        self.controls.handle_mouse_up(event.button(), event.x(), event.y())

    def wheelEvent(self, event):
        self.controls.handle_mouse_wheel(event.angleDelta().y())

    def keyPressEvent(self, event):
        if event.isAutoRepeat(): 
            return
        self.controls.handle_key_down(event.key())
    
    def keyReleaseEvent(self, event):
        if event.isAutoRepeat(): 
            return
        self.controls.handle_key_up(event.key())

    def initializeGL(self):
        if self.model == None:
            raise SystemExit("Model is null!")
        self.renderModel = PreviewRenderModel(self.model)
        glClearColor(0.5, 0.5, 1.0, 1.0)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_CULL_FACE)
        glEnable(GL_DEPTH_TEST)
        glFrontFace(GL_CCW)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthFunc(GL_LEQUAL)
        glDepthMask(GL_TRUE)
        glAlphaFunc(GL_GEQUAL, 0.01)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glViewport(0, 0, 640, 480)
        glMatrixMode(GL_PROJECTION)
        gluPerspective(60.0, 640/480, 0.01, 32000.0)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()

    def load_model(self, model):
        self.model = model

    def draw_axis(self):
        AXIS_LENGTH = 10000.0
        glDisable(GL_TEXTURE_2D)
        glBegin(GL_LINES)
        # X Axis (positive)
        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(AXIS_LENGTH, 0.0, 0.0)
        # X Axis (negative)
        glColor3f(0.5, 0.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(-AXIS_LENGTH, 0.0, 0.0)
        # Y Axis (positive)
        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, AXIS_LENGTH, 0.0)
        # Y Axis (negative)
        glColor3f(0.0, 0.5, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, -AXIS_LENGTH, 0.0)
        # Z Axis (positive)
        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, 0.0, AXIS_LENGTH)
        # Z Axis (negative)
        glColor3f(0.0, 0.0, 0.5)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, 0.0, -AXIS_LENGTH)
        glEnd()

    def draw_model(self):
        glDisable(GL_TEXTURE_2D)
        glColor3f(1, 1, 1)
        glBegin(GL_TRIANGLES)
        glVertex3f(-0.5,0,-0.5)
        glVertex3f(0.5,0,-0.5)
        glVertex3f(0.0,0,0.5)
        glEnd()

    def resizeGL(self, w, h):
        try:
            glViewport(0, 0, w, h)
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluPerspective(60.0, w/h, 0.01, 32000.0)
        except:
            pass # This try-catch prevents an error from showing when the preview window is closed.

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        camPos = self.controls.cameraPos
        tarPos = self.controls.targetPos
        gluLookAt(camPos.x, camPos.y, camPos.z, tarPos.x, tarPos.y, tarPos.z, 0, 1, 0)
        if self.renderModel != None:
            glScalef(0.02, 0.02, 0.02)
            self.renderModel.render()
        if self.showAxis:
            self.draw_axis()
        glPopMatrix()
        glFlush()
