import base64
import os

import flet as ft
import numpy as np
from flet import ElevatedButton, Dropdown, IconButton, Image
from flet_core import Column
from baslor_cam import Cam, base64_to_np_array, np_array_to_base64
import cv2


class BaslorHomeUi(ft.UserControl):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cam = None
        self.devices = {}
        self.devices_options = []
        self.device_selected = ''

        # Controllable UI Elements
        self.d = None   # drop down
        self.connect_button = None
        self.img_display = None
        self.stop_capture_flag = False
        self.filtered_image = None
        self.filter_column = None
        self.apply_button = None
        self.filter_list = None

    def set_cam(self, cam):
        self.cam = cam

    def build(self):
        self.d = Dropdown(on_change=self.on_device_select)
        self.features_dropdown = Dropdown(label='Camera Properties', on_change=self.list_features)
        self.current_value = ft.TextField(on_change=self.text_changed)
        self.connect_button = ElevatedButton(on_click=self.connect_action)
        self.connect_button.text = 'Connect'
        self.img_display = Image(
                                    width=400,
                                    height=300
                                )
        self.filter_list = Dropdown(
            label='Select Filter',
            width=150
        )
        self.apply_button = ElevatedButton(
            text='Apply',
            width=150
        )
        self.filter_column = Column(
            controls=[
                self.filter_list,
                self.apply_button
            ]
        )
        self.filtered_image = Image(
            width=400,
            height=300
        )
        return ft.Container(
                content=Column(
                    controls=[
                        ft.Row(
                            controls=[
                                IconButton(
                                    icon=ft.icons.REFRESH,
                                    on_click=self.devices_enumerated
                                ),
                                self.d,
                                self.connect_button
                            ],
                            alignment=ft.MainAxisAlignment.CENTER
                        ),
                        ft.Row(
                            controls=[
                                ElevatedButton('Start', bgcolor='#98D8AA', color='#41644A', on_click=self.start_capture),
                                ElevatedButton('Stop', bgcolor='#FF9F45', color='#CE5959', on_click=self.stop_capture),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER
                        ),
                        ft.Row(
                            controls=[
                                self.img_display,
                                self.filter_column,
                                self.filtered_image
                            ],
                            height=300,
                            alignment=ft.MainAxisAlignment.CENTER
                        ),
                        ft.Row(
                            controls=[self.features_dropdown,
                                      self.current_value,
                                      ft.Row(controls=[ft.ElevatedButton('Apply'),
                                                       ft.ElevatedButton('Cancel')],
                                             alignment=ft.MainAxisAlignment.CENTER)
                                      ]

                        )
                    ]
                )
            )

    def text_changed(self, event):
        self.current_value.value = event.control.value
        self.update()

    def list_features(self, event):
        self.features_dropdown.value = event.control.value
        self.update()

    def on_raw_image_recieved(self, msg):
        """Message is an object"""

        self.img_display.src_base64 = msg
        self.img_display.update()

    def on_apply_filter(self, msg):
        # self.filtered_image.src_base64 = msg
        # self.filtered_image.update()

        im_bytes = base64.b64decode(msg)
        im_arr = np.frombuffer(im_bytes, dtype=np.uint8)  # im_arr is one-dim Numpy array
        img = cv2.imdecode(im_arr, flags=cv2.IMREAD_UNCHANGED)

        # Perform edge detection here.
        img_blur = cv2.GaussianBlur(img, (3, 3), 0)
        # sobelxy = cv2.Sobel(src=img_blur, ddepth=cv2.CV_64F, dx=1, dy=1, ksize=7)
        edges = cv2.Canny(image=img_blur, threshold1=10, threshold2=30)
        # print(sobelxy)
        # img_str = np_array_to_base64(sobelxy)
        # self.filtered_image.src_base64 = img_str
        # self.filtered_image.update()

        _, im_arr = cv2.imencode('.jpg', edges)  # im_arr: image in Numpy one-dim array format.
        im_bytes = im_arr.tobytes()
        im_b64 = base64.b64encode(im_bytes).decode('utf-8')
        self.filtered_image.src_base64 = im_b64
        # print(sobelxy)

        self.filtered_image.update()

    def devices_enumerated(self, event):
        self.d.options.clear()
        self.devices = {f"{device.GetModelName()} - {device.GetSerialNumber()}": device for device in self.cam.enumerate_devices()}
        self.devices_options = [ft.dropdown.Option(device) for device
                                in self.devices.keys()]
        self.d.options.extend(list(self.devices_options))

        self.update()

    def on_device_select(self, event):
        self.device_selected = self.d.value

    def disconnect_action(self, event):
        self.cam.close_camera()
        self.connect_button.text = 'Connect'
        self.connect_button.on_click = self.connect_action
        self.update()

    # Update the dropdown the with list of features the camera has.
    def camera_features(self):
        self.features_dropdown = ['Gain']

    def connect_action(self, event):
        """things to happen:
        1. check if device is selected.
        2. create a camera instance
        3. change label to disconnect"""

        if self.device_selected:
            try:
                self.cam.open_camera(self.devices[self.device_selected])
                self.connect_button.text = 'Disconnect'
                self.connect_button.on_click = self.disconnect_action
                self.update()
            except:
                pass

        return True

    def start_capture(self, event):
        self.stop_capture_flag = False

        self.cam.register_image_handler(self.on_raw_image_recieved)
        self.cam.register_image_handler(self.on_apply_filter)
        self.cam.start_capture(image_control=self.img_display )

        # while not self.stop_capture_flag:
        #     self.img_display.src = ''
        #
        #     img_path = self.cam.start_capture()
        #     self.img_display.src = img_path
        #
        #     self.img_display.update()
        #     self.cam.clear_backlog()

    def stop_capture(self, event):
        # self.stop_capture_flag = True
        self.cam.stop_capture()

def main(page: ft.Page):
    page.title = "Baslor Camera Study App"
    page.theme_mode = ft.ThemeMode.LIGHT

    page.window_resizable = False
    page.window_height = 800
    page.window_width = 1000


    ui = BaslorHomeUi()
    # create an instance of camera here.
    cam = Cam()
    ui.set_cam(cam)

    page.add(ui)




ft.app(target=main)