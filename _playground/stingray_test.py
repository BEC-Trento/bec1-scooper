from pymba import Vimba, VimbaException
import numpy as np
import matplotlib.pyplot as plt

cam_id = 'DEV_0xA4701110AE920'

# vimba can be used as a context manager. Otherwise call vimba.startup()
with Vimba() as vimba:
    # get connected camera ids
    ids = vimba.getCameraIds()
    
    # connect to the camera you want
    try:
        cam = vimba.getCamera(cam_id)
    except VimbaException:
        if cam_id not in ids:
            print(f'Camera {cam_id} not found in list of connected cameras.')
        raise
        
    
    # need to open it to do anything with it
    cam.openCamera()
    
    # list all the features
    names = cam.getFeatureNames()
    
    # all the listed features exist as attributes of the camera class and
    # can be assigned to directly but do not appear on Tab completion.
    for name in names:
        info = cam.getFeatureInfo(name)
        print(info.category, info.name)
        # try:
            # print(name, cam.__getattr__(name))
        # except VimbaException:
            # # this exception probably only occurs for features that are not
            # # implemented in pymba yet. Don't worry about it.
            # print(name)
    
    if True:
        # test single frame catpure
        cam.TriggerMode = 'On'
        cam.AcquisitionMode = 'SingleFrame'
        # cam.AcquisitionMode = 'MultiFrame'
        # cam.AcquisitionFrameCount = 2
        
        frame = cam.getFrame()
        frame.announceFrame()
        
        # capture a camera image
        cam.startCapture()
        frame.queueFrameCapture()
        cam.runFeatureCommand('AcquisitionStart')
        
        # this will never time out
        while frame.waitFrameCapture() != 0:
            print('.', end='')
        cam.runFeatureCommand('AcquisitionStop')
        # frame.waitFrameCapture()
        

        # clean up after capture
        cam.endCapture()
        cam.revokeAllFrames()
        
        data = np.ndarray(buffer=frame.getBufferByteData(), dtype=np.uint16,
                              shape=(frame.height, frame.width, 1))

        plt.imshow(data[..., 0])
        plt.show()
    
    
    
    # test multiple frames catpure
    cam.TriggerMode = 'On'
    # cam.AcquisitionMode = 'Continuous'
    cam.AcquisitionMode = 'MultiFrame'
    cam.AcquisitionFrameCount = 5
    cam.ExposureTime = 2000
    
    frame0 = cam.getFrame()
    frame1 = cam.getFrame()
    frame0.announceFrame()
    frame1.announceFrame()
    
    # capture a camera image
    cam.startCapture()
    frame0.queueFrameCapture()
    frame1.queueFrameCapture()
    cam.runFeatureCommand('AcquisitionStart')
    
    # this will never time out
    while frame1.waitFrameCapture() != 0:
        print('.', end='')
    cam.runFeatureCommand('AcquisitionStop')
    # frame.waitFrameCapture()
    

    # clean up after capture
    cam.endCapture()
    cam.revokeAllFrames()
    
    data0 = np.ndarray(buffer=frame0.getBufferByteData(), dtype=np.uint16,
                          shape=(frame0.height, frame0.width, 1))
    data1 = np.ndarray(buffer=frame1.getBufferByteData(), dtype=np.uint16,
                          shape=(frame1.height, frame1.width, 1))

    plt.imshow(data0[..., 0])
    plt.title('frame0')
    plt.show()
    
    plt.imshow(data1[..., 0])
    plt.title('frame1')
    plt.show()
    
    
    cam.closeCamera()
    