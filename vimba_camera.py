from pymba import Vimba, VimbaException
import logging
import sys
from contextlib import contextmanager
import numpy as np

__version__ = '0.1.0'

log = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


# class Vimba_Camera:
    
    # def version():
        # return Vimba().getVersion()
        
    # def enumerate_cameras():
        # # get connected camera ids
        # with Vimba() as vimba:
            # return vimba.getCameraIds()  # list of camera ids
    
    # def __init__(self, name):
        # # I should treat Vimba as a singleton but for now I'll just stick
        # # with context managers
        # self.name = name
        # cams = Vimba_Camera.enumerate_cameras()
        
        # # check if the camera exists
        # if self.name not in cams:
            # raise NameError(
                # f'Camera {cam_id} not found in list of connected cameras.')
    
    # @contextmanager
    # def _camera(self):
        # with Vimba() as vimba:
            # camera = vimba.getCamera(self.name)
            # log.info(f'Opening camera.')
            # camera.openCamera()
            # yield camera
            # camera.closeCamera()
            # log.info(f'Closing camera.')
    
    # def list_features(self):
        # with self._camera() as cam:
            # features = cam.getFeatureNames()
            # print(cam.__dict__)
            
            # return [cam.getFeatureInfo(feature) for feature in features]
    
    # def feature_range(self, feature):
        # return cam.getFeatureRange(feature)
    
    # def write_features_to_file(self):
        # features = self.list_features()
        
        # with self._camera() as cam:   
            # for feature in features:
                # # print(feature.name)
                # print(cam.__getattr__[str(feature.name)])
        
        
            
    # # def _open(self):
        # # # need to open it to do anything with it
        # # self.camera.openCamera()
        # # log.info(f'Opening camera.')
    
    # # def _close(self):
        # # # need to open it to do anything with it
        # # self.camera.closeCamera()
        # # log.info(f'Closing camera.')
        
        # # self.vimba.shutDown()
        # # log.info(f'Shutting down vimba.')
    

class Vimba_Camera:
    
    def version():
        with Vimba() as vimba:
            return vimba.getVersion()

    def enumerate_cameras():
        # get connected camera ids
        # otherwise we haven't started yet. Open and close vimba library
        with Vimba() as vimba:
            return vimba.getCameraIds()
    
    def startup_vimba(self):
        log.info('Starting vimba.')
        self.vimba = Vimba()
        self.vimba.startup()
    
    def shutdown_vimba(self):
        self.vimba.shutdown()
        
    
    def __init__(self, name, vimba=None):
        # remember that Vimba as a singleton
        # you can use the camera as a context manager so as to not worry
        # about opening and closing the libary or the camera.
        # Otherwise remember to do it manually

        
        self.name = name
        if vimba is None:
            self.startup_vimba()
        else:
            self.vimba = vimba
            print(f"Received vimba {id(self.vimba)}")
        cams = self.vimba.getCameraIds()
                
        # check if the camera exists
        if self.name not in cams:
            raise NameError(
                f'Camera {name} not found in list of connected cameras.')
        
        self.camera = self.vimba.getCamera(self.name)
        self.camera.openCamera()
        log.info(f'Initialise camera {name}.')
    
    def close(self):
        # release both camera and vimba handles
        self.camera.closeCamera()
        log.info(f'Closing camera.')
        
        # self.vimba.shutdown()
        # log.info(f'Shutting down vimba.')
        
    def __enter__(self):
        log.info('__enter__')
        # __init__ starts vimba and opens the camera. Don't bother here.
        return self
    
    def __exit__(self, type, value, traceback):
        self.close()
    
    def list_features(self):
        features = self.camera.getFeatureNames()
        
        return [self.camera.getFeatureInfo(feature) for feature in features]
    
    def get_feature_range(self, feature):
        try:
            return self.camera.getFeatureRange(feature)
        except VimbaException:
            pass
    
    def get_camera_info(self):
        return self.camera.getInfo()
    
    def print_feature_description(self, feature):
        try:
            print(self.camera.getFeatureInfo(feature).description)
        except VimbaException:
            print('No description available.')
    
    def write_features_and_values_to_file(self):
        features = self.list_features()
        info = self.get_camera_info()
        
        filename = (info.cameraName.decode('utf8') + 
                    info.cameraIdString.decode('utf8') + 
                    '_attributes.txt')
        with open(filename, 'w') as f:
            for feature in features:
                name = feature.name.decode('utf-8')
                try:
                    value = self.camera.__getattr__(name)
                except (VimbaException, TypeError):
                    value = None
                # print(name, value)
                f.write(f"['{name}', ")
                f.write(f"'{value}'],\n")
            
            # delete that last comma
            f.seek(0,2)
            size = f.tell()
            f.truncate(size-3)
    
    def set_feature(self, name, value):
        setattr(self.camera, name, value)
    
    def set_features(self, _dict):
        # ideally this would be an ordered dict since some features can only be
        # set after others, e.g. cannot set Gain Value unless Gain is Manual.
        for k, v in _dict.items():
            self.set_feature(k, v)
            
    def set_roi(self, roi):
        # set the rois with the correct order
        try:    
            self.set_feature('Height', roi['Height'])
            self.set_feature('OffsetY', roi['OffsetY'])
        except VimbaException:
            self.set_feature('OffsetY', roi['OffsetY'])
            self.set_feature('Height', roi['Height'])
        
        try:    
            self.set_feature('Width', roi['Width'])
            self.set_feature('OffsetX', roi['OffsetX'])
        except VimbaException:
            self.set_feature('OffsetX', roi['OffsetX'])
            self.set_feature('Width', roi['Width'])

        
            
    def snap(self, trigger=False):
        self.camera.TriggerMode = 'On' if trigger else 'Off'
        self.camera.AcquisitionMode = 'SingleFrame'
        # self.camera.AcquisitionMode = 'MultiFrame'
        # self.camera.AcquisitionFrameCount = 2
        
        frame = self.camera.getFrame()
        frame.announceFrame()
        
        # capture a camera image
        self.camera.startCapture()
        frame.queueFrameCapture()
        self.camera.runFeatureCommand('AcquisitionStart')
        
        # this will never time out
        while frame.waitFrameCapture() != 0:
            print('.', end='')
        # frame.waitFrameCapture(timeout=-1)
        self.camera.runFeatureCommand('AcquisitionStop')
        # frame.waitFrameCapture()
        

        # clean up after capture
        self.camera.endCapture()
        self.camera.revokeAllFrames()
        
        data = self._decode_image_data(frame)

        return data
    
    def grab_multiple(self, N=3, trigger=True):        
        self.camera.TriggerMode = 'On' if trigger else 'Off'
        self.camera.AcquisitionMode = 'MultiFrame'
        self.camera.AcquisitionFrameCount = N
        
        frames = [self.camera.getFrame() for _ in range(N)]
        for frame in frames:
            frame.announceFrame()

        # start capturing
        self.camera.startCapture()
        # queue the frames
        for frame in frames:
            frame.queueFrameCapture()
        self.camera.runFeatureCommand('AcquisitionStart')
        
        # this will never time out
        # having it the while loop here means that I can get SIGINT to exit
        while frames[-1].waitFrameCapture() != 0:
            print('.', end='')
        # frames[-1].waitFrameCapture(timeout=-1)
        self.camera.runFeatureCommand('AcquisitionStop')
        # frame.waitFrameCapture()
        

        # clean up after capture
        self.camera.endCapture()
        self.camera.revokeAllFrames()
        
        data = [self._decode_image_data(frame) for frame in frames]

        return np.array(data)
        
    
    def _decode_image_data(self, frame):
        bitdepths = {'Mono16': np.uint16,
                     'Mono12Packed': np.uint16,
                     'Mono8': np.uint8}
                     
        bitdepth = bitdepths[self.camera.PixelFormat]

        data = np.ndarray(buffer=frame.getBufferByteData(), dtype=bitdepth,
                          shape=(frame.height, frame.width))
        
        return data.copy()
        

    
        
    
        



if __name__ == '__main__':

    # class methods
    print(Vimba_Camera.version())
    print(Vimba_Camera.enumerate_cameras())
    
    cam_id = 'DEV_0xA4701110AE920'
    
    # can use it as a context manager if you're doing something quick
    # with Vimba_Camera(cam_id) as camera:
        # features = camera.list_features()
        # for feature in features:
            # print(feature.name)
    
    cam = Vimba_Camera(cam_id)
    # features = cam.list_features()
    # for feature in features:
        # print(feature.name, cam.get_feature_range(feature.name.decode('utf-8')))
        
    # cam.write_features_and_values_to_file()
    cam.print_feature_description('TriggerMode')
    
    # cam.camera.ExposureTime = 70000  # ms
    cam.set_feature('ExposureTime', 70000)
    
    import matplotlib.pyplot as plt
    
    N_frames = 2
    if N_frames == 1:
        data = cam.snap(trigger=True)
        print(data.shape)
        # plt.imshow(data[..., 0])
        plt.imshow(data)
        plt.show()
    else:    
        data = cam.grab_multiple(N=N_frames, trigger=True)
        print(data.shape)
        
        for img in data:
            plt.imshow(img)
            plt.show()
    
    cam.close()
    
    
    
    
    
    
    
    
    
    
    