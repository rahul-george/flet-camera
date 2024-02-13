import base64
import os
import time
import traceback
from io import BytesIO

import cv2
import numpy as np
import pypylon.pylon as pylon
import matplotlib.pyplot as plt     # Plotting library
from PIL import Image
from flet import PubSub
from flet.pubsub import PubSubHub
from pubsub import pub
from PIL import Image as pilImage


class Cam(object):
    def __init__(self):
        self.tlf = pylon.TlFactory.GetInstance()
        self.cam = None
        self.img = None
        self.image_history = []
        self.img_capture = None
        self.image_subs = []

    def enumerate_devices(self):
        return self.tlf.EnumerateDevices()

    def open_camera(self, device):
        self.cam = pylon.InstantCamera(self.tlf.CreateDevice(device))
        self.cam.Open()

    def close_camera(self):
        if self.cam:
            self.cam.Close()

    def register_image_handler(self, handler):
        self.image_subs.append(handler)

    def start_capture(self, image_control):
        # res =self.cam.GrabOne(1000)
        # self.img = Image.fromarray(res.Array)
        # dt_namr = f"img1_{time.time()}.jpg"
        # self.img.save(dt_namr)
        # path = os.path.join(os.getcwd(), dt_namr)
        #
        # self.image_history.append(path)
        #
        # return path

        # It should start a thread. The thread will capture the images and update the page control.

        image_handler = ImageHandler()
        # image_handler.configure(control=image_control)
        for handler in self.image_subs:
            image_handler.register_subs(handler)

        self.img_capture = ImageCapture(self.cam, 1000)

        self.img_capture.start_capture(handler=image_handler)
        return ""


    def stop_capture(self):
        self.img_capture.stop_capture()

    def clear_backlog(self):
        if len(self.image_history) > 1:
            os.remove(self.image_history[0])
            self.image_history.pop(0)


class ImageCapture():
    def __init__(self, camera, max_image_capture):
        self.stop_capture_flag = False
        self.cam = camera
        self.max_image_capture = max_image_capture
        self.handler = None

    def start_capture(self, handler=None):
        self.stop_capture_flag = False

        if handler:
            self.cam.RegisterImageEventHandler(handler, pylon.RegistrationMode_ReplaceAll, pylon.Cleanup_None)
            self.handler = handler

        self.cam.StartGrabbingMax(self.max_image_capture,
                                  pylon.GrabStrategy_LatestImages,
                                  pylon.GrabLoop_ProvidedByInstantCamera)

    def stop_capture(self):
        self.stop_capture_flag = True
        self.cam.StopGrabbing()
        if self.handler:
            self.cam.DeregisterImageEventHandler(self.handler)
            self.handler = None
        self.cam.Close()


class ImageHandler(pylon.ImageEventHandler):
    def __init__(self):
        super().__init__()
        self.control = None
        self.ps = PubSub(PubSubHub(), "1")

        # Additionally, get the Image control

    def configure(self, control):
        self.control = control

    def register_subs(self, handler):
        pub.subscribe(handler, "image_received")
        pass

    def OnImageGrabbed(self, camera: "InstantCamera", grabResult: "GrabResult") -> "void":
        try:
            if grabResult.GrabSucceeded():
                # Check image contents
                img = grabResult.Array

                # print(type(img))
                img = Image.fromarray(img)
                buffered = BytesIO()
                img.save(buffered, format='JPEG')
                img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
                # print(img_str)



                # dt_name = f"img1_{time.time()}.jpg"
                # img.save(dt_name)
                # path = os.path.join(os.getcwd(), dt_name)

                # Update image on screen
                # self.control.src = path
                # self.control.src_base64 = img_str
                # self.control.update()

                # self.ps.send_all(img_str)
                pub.sendMessage("image_received", **{"msg":img_str})
            else:
                raise RuntimeError("Grab Failed")

        except Exception as err:
            traceback.print_exc()


def np_array_to_base64(img):
    img = Image.fromarray(img)
    buffered = BytesIO()
    img.save(buffered, format='png')
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return img_str


def base64_to_np_array(img_str):
    imgdata = base64.b64decode(img_str)
    image = Image.open(BytesIO(imgdata))
    np_array = np.array(image)
    return np_array