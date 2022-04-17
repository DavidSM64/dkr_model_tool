import math
from model import *
from PyQt5.Qt import Qt

class Vec3:
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        return '(' + str(self.x) + ', ' + str(self.y) + ', ' + str(self.z) + ')'

    def __repr__(self):
        return self.__str__()

CONTROL_FLAG_FORWARD         = 1 << 0
CONTROL_FLAG_BACKWARD        = 1 << 1
CONTROL_FLAG_LEFT            = 1 << 2
CONTROL_FLAG_RIGHT           = 1 << 3
CONTROL_FLAG_ROTATING_CAMERA = 1 << 4

KEY_TO_FLAG = {
    Qt.Key_W: CONTROL_FLAG_FORWARD,
    Qt.Key_S: CONTROL_FLAG_BACKWARD,
    Qt.Key_A: CONTROL_FLAG_LEFT,
    Qt.Key_D: CONTROL_FLAG_RIGHT,
}

MOUSE_TO_FLAG = {
    Qt.LeftButton: CONTROL_FLAG_ROTATING_CAMERA
}

class DkrPreviewControls():
    def __init__(self):
        self.controlFlags = 0
        self.zoomAmount = 0
        self.lastMouseX = -1
        self.lastMouseY = -1
        self.cameraPos = Vec3(-10, 10, -10)
        self.targetPos = Vec3()
        self.forceUpdate = False
        self.set_cam_angle_from_target()
        self.update()

    def handle_key_down(self, keyCode):
        if keyCode in KEY_TO_FLAG:
            self.set_flag(KEY_TO_FLAG[keyCode])

    def handle_key_up(self, keyCode):
        if keyCode in KEY_TO_FLAG:
            self.clear_flag(KEY_TO_FLAG[keyCode])

    def handle_mouse_down(self, mouseButton, x, y):
        if mouseButton in MOUSE_TO_FLAG:
            self.set_flag(MOUSE_TO_FLAG[mouseButton])
            if self.is_flag_set(CONTROL_FLAG_ROTATING_CAMERA):
                self.lastMouseX = x
                self.lastMouseY = y

    def handle_mouse_up(self, mouseButton, x, y):
        if mouseButton in MOUSE_TO_FLAG:
            self.clear_flag(MOUSE_TO_FLAG[mouseButton])

    def handle_mouse_wheel(self, moveAmount):
        if abs(moveAmount) > 10:
            self.zoomAmount = moveAmount
        self.update()

    def is_flag_set(self, flag):
        return (self.controlFlags & flag) != 0

    def set_flag(self, flag):
        self.controlFlags |= flag
        self.update()

    def clear_flag(self, flag):
        self.controlFlags &= ~flag
        self.update()

    def check_active(self):
        self.active = self.forceUpdate or (self.controlFlags != 0) or (self.zoomAmount != 0)

    def update(self):
        self.check_active()

    def set_cam_angle_from_target(self):
        xDiff = self.targetPos.x - self.cameraPos.x
        yDiff = self.targetPos.y - self.cameraPos.y
        zDiff = self.targetPos.z - self.cameraPos.z
        if xDiff == 0:
            xDiff = 0.001
        if yDiff == 0:
            yDiff = 0.001
        dist = math.sqrt(xDiff*xDiff + zDiff*zDiff)
        self.yaw = math.atan2(-zDiff, xDiff) - (math.pi / 2)
        self.pitch = math.atan2(yDiff, dist) - (math.pi)

    def update_target_pos(self):
        camLX = math.sin(self.yaw) * math.cos(self.pitch)
        camLY = -math.sin(self.pitch)
        camLZ = math.cos(self.yaw) * math.cos(self.pitch)
        self.targetPos.x = self.cameraPos.x + camLX
        self.targetPos.y = self.cameraPos.y + camLY
        self.targetPos.z = self.cameraPos.z + camLZ

    def move_left(self, amount):
        camLX = math.sin(self.yaw + (math.pi / 2)) * math.cos(self.pitch)
        camLZ = math.cos(self.yaw + (math.pi / 2)) * math.cos(self.pitch)
        self.cameraPos.x += camLX * amount
        self.cameraPos.z += camLZ * amount
        self.update_target_pos()

    def move_ahead(self, amount):
        camLX = math.sin(self.yaw) * math.cos(self.pitch)
        camLY = -math.sin(self.pitch)
        camLZ = math.cos(self.yaw) * math.cos(self.pitch)
        self.cameraPos.x += camLX * amount
        self.cameraPos.y += camLY * amount
        self.cameraPos.z += camLZ * amount
        self.update_target_pos()

    def rotate_camera(self, mouseX, mouseY):
        mouseDiffX = mouseX - self.lastMouseX
        mouseDiffY = mouseY - self.lastMouseY
        self.yaw   -= mouseDiffX * 0.01
        self.pitch -= mouseDiffY * 0.01
        self.pitch = clamp(self.pitch, -4.7, -1.6)
        self.lastMouseX = mouseX
        self.lastMouseY = mouseY
        self.move_ahead(0)
        self.forceUpdate = True
        self.update()