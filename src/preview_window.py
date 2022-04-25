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

CAMERA_SPEED = 50
CAMERA_NEAR = 1
CAMERA_FAR = 99999
AXIS_LENGTH = 999999

class DkrPreviewWidget(QOpenGLWindow):
    def __init__(self):
        super(DkrPreviewWidget, self).__init__()
        self.setMinimumSize(QSize(640, 480))
        self.renderModel = None
        self.showAxis = True
        self.controls = DkrPreviewControls()
        self.targetFPS = 60
        self.fov = 60

        self.takeScreenshot = False
        self.screenshotDelay = 0

        QTimer.singleShot(1000 // self.targetFPS, self.updateControls)

    def updateControls(self):
        if self.screenshotDelay > 0:
            self.screenshotDelay -= 1
        if self.controls.active:
            if self.controls.is_flag_set(CONTROL_FLAG_FORWARD):
                self.controls.move_ahead(CAMERA_SPEED)
            elif self.controls.is_flag_set(CONTROL_FLAG_BACKWARD):
                self.controls.move_ahead(-CAMERA_SPEED)
            if self.controls.is_flag_set(CONTROL_FLAG_LEFT):
                self.controls.move_left(CAMERA_SPEED)
            elif self.controls.is_flag_set(CONTROL_FLAG_RIGHT):
                self.controls.move_left(-CAMERA_SPEED)
            if self.controls.zoomAmount != 0:
                self.controls.move_ahead(self.controls.zoomAmount)
                self.controls.zoomAmount = 0
            if self.controls.is_flag_set(CONTROL_FLAG_DEBUG):
                if self.screenshotDelay == 0:
                    self.calculate_segment_bitfields()
                    self.screenshotDelay = 120
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
        gluPerspective(self.fov, 640/480, CAMERA_NEAR, CAMERA_FAR)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()

    def load_model(self, model):
        self.model = model
        modelBoundingBox = model.get_bounding_box()
        # Set camera position to look at the entire map
        camX = modelBoundingBox[1][0] # Camera X = max X
        camY = modelBoundingBox[1][1] # Camera Y = max Y
        camZ = modelBoundingBox[1][2] # Camera Z = max Z
        tarX = modelBoundingBox[0][0] # Target X = min X
        tarY = modelBoundingBox[0][1] # Target Y = min Y
        tarZ = modelBoundingBox[0][2] # Target Z = min Z
        self.controls.set_cam_position(camX, camY, camZ, tarX, tarY, tarZ)

    def draw_axis(self):
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

    def set_viewport(self, width, height, clearColor=(0.5, 0.5, 1.0, 1.0)):
        glClearColor(clearColor[0], clearColor[1], clearColor[2], clearColor[3])
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fov, width/height, CAMERA_NEAR, CAMERA_FAR)

    def resizeGL(self, w, h):
        try:
            self.set_viewport(w, h)
        except OpenGL.error.GLError:
            pass # This try-catch prevents an error from showing when the preview window is closed.

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        camPos = self.controls.cameraPos
        tarPos = self.controls.targetPos
        gluLookAt(camPos.x, camPos.y, camPos.z, tarPos.x, tarPos.y, tarPos.z, 0, 1, 0)
        if self.renderModel != None:
            self.renderModel.render()
        if self.showAxis:
            self.draw_axis()
        glPopMatrix()
        glFlush()
