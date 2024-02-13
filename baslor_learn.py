import pypylon.pylon as pylon
import numpy as np      # Numeric Python
import matplotlib.pyplot as plt     # Plotting library
import cv2      # Open CV

# Read image as grayscale
# img = cv2.imread(r"C:\Users\Pramod Variyam\Pictures\Screenshots\Screenshot 2023-04-28 094841.png", cv2.IMREAD_GRAYSCALE)
#
# plt.gray()
# plt.imshow(img)
# plt.show()
#
# print(img.size)
#
# plt.imshow(img[150:300, 150: 400])
# plt.show()

# First we need to discover devices using the transport layer factory (TlFactory) Singlton class
tlf = pylon.TlFactory.GetInstance()
devices = tlf.EnumerateDevices()
for device in devices:
    print("Device details", device.GetModelName(), device.GetSerialNumber())

cam = pylon.InstantCamera(tlf.CreateDevice(devices[0]))

cam.Open()

if 0:
    # Gain
    cam.Gain
    print(cam.Gain.GetValue())
    cam.Gain = 12.1
    print(cam.Gain.GetValue())
    cam.Gain = 0.0
    print(cam.Gain.Value)

print(cam.TriggerSource.Value)
print(cam.PixelFormat.Value)
print(cam.BslTemperatureStatus.Value)

res = cam.GrabOne(1000)         # Grab one image
# arr = res.GetBuffer()[:100]     # It is a bytearray

img = res.Array

print(img)

print(cam.UserSetSelector.Value)

plt.imshow(img)
plt.show()

cam.Close()