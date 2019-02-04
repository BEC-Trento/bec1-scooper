from vimba_camera import Vimba_Camera
import numpy as np
from sis2_lib import write_sis
import os

path = r'\\BEC2-PC\c-siscam-img\test_0.sis'
cam_id = 'DEV_0xA4701110AE920'
cam_id = 'DEV_0xA4701110A5767'
number_of_frames = 3

# these settings should work well for capturing 3 images
settings = {
    'BlackLevel': 0,
    'ExposureAuto': 'Off',
    'ExposureMode': 'Timed',
    'ExposureTime': 70000,
    'GainAuto': 'Off',
    'Gain': 10,
    'Gamma': 1,
    'IIDCMode': 'Mode0',
    'TriggerActivation': 'FallingEdge',
    'TriggerDelay': 0,
    'TriggerMode': 'On',
    'TriggerSelector': 'ExposureStart',
    'TriggerSource': 'InputLines',
    'Height': 1234,
    'Width': 1624,
}

# Binning can increase SNR while reducing field of view.
# See Format7 modes for details.
# settings['IIDCMode'] = 'Mode1'


with Vimba_Camera(cam_id) as cam:
    cam.set_features(settings)
    
    while True:
        data = cam.grab_multiple(N=number_of_frames, trigger=True)
        
        # cast them from uint16 to float64
        data = np.float64(data)
        
        # probe, atoms, bg, _ = data
        probe, atoms, bg = data
        atoms -= bg
        probe -= bg
        od = -np.log(atoms.clip(1) / probe.clip(1))
        
        # get rid of the file first
        os.remove(path)
        write_sis(path, od)
        np.save(path+'.raw.npy', data)
        
        
        