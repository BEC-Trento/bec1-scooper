from vimba_camera import Vimba_Camera
from pymba import Vimba
from collections import OrderedDict

from InfiniiVision import InfiniiVision2000Scope
import numpy as np
from sis2_lib import write_sis
import os, sys
import traceback
import time
import scooper
from datetime import datetime
from pathlib import Path

from concurrent.futures import ThreadPoolExecutor
import h5py
import glob

import json
program_log_path = r'C:\SIScam\SIScamProgram\Prog\img\last-program.json'
save_sequence_path = r'scooper_save_sequence.json'


# cam_id = 'DEV_0xA4701110AE920' # testing camera on Dimitri's pc
# cam_id, camera_name = 'DEV_0xA4701110A5767', 'horiz1' # Stingary horiz1 (M = 1.3)
# cam_id, camera_name = 'DEV_0xA4701110AE920', 'horiz4' # Stingary horiz4 (M = 4.2)
# cam_id, camera_name = 'DEV_0xA4701110A64FE', 'vert' # Stingary horiz4 (M = 4.2)

cam_ids =   [# Firewire ID, camera_name
             # ['DEV_0xA4701110AE920', 'horiz4'],# Stingary horiz1 (M = 1.3)
             ['DEV_0xA4701110A5767', 'horiz1'],
            ]
 
scope_ids = [
             ['USB0::0x0957::0x1796::MY55140782::INSTR', 'scope'], # scope 1
             ['USB0::0x0957::0x1796::MY55140778::INSTR', 'scope2'], # scope 1
             ['USB0::0x0957::0x1796::MY53100138::INSTR', 'scope3'], # scope 1
             ]
# these settings should work well for capturing 3 images
# Binning can increase SNR while reducing field of view.
# See Format7 modes for details.
# settings['IIDCMode'] = 'Mode1'
settings = {
    'BlackLevel': 0,
    'ExposureAuto': 'Off',
    'ExposureMode': 'Timed',
    'ExposureTime': 70000,
    'GainAuto': 'Off',
    'Gain': 18,
    'Gamma': 1,
    'IIDCMode': 'Mode0',
    'TriggerActivation': 'RisingEdge',
    'TriggerDelay': 0,
    'TriggerMode': 'On',
    'TriggerSelector': 'ExposureStart',
    'TriggerSource': 'InputLines',
    # -- ROI settings: it just works if you set them in this order
    # cool, you don't even need OrderedDicts for this
    # invalid ROIs will raise a VimbaException
    'OffsetX': 0,
    'OffsetY': 0,
    'Height': 1234,
    'Width': 1624,
    'PixelFormat': 'Mono16'
}

settings_per_camera = {
    'horiz1':{
        'Gain': 10,
        },
    'horiz4':{
        'Gain': 16,
        'ExposureTime': 22000,
        }
    }
    
ROIs = {
    'horiz1': None,
        # {
        # 'OffsetY': 0,
        # 'OffsetX': 0,
        # 'Height': 800,
        # 'Width': 1234,
        # },
    'horiz4':
        {
        'OffsetY': 524,
        'OffsetX': 154,
        'Height': 240,
        'Width': 1200,
        }
    }

# get some default paramaters for scooper

attrs = {}
attrs['run number'] = 0
attrs['run repeat'] = 0
h5path_0 = Path(r'D:\SIScam\SIScamProgram\Prog\img')

cameras = {}
scopes = {name: InfiniiVision2000Scope(id) for id, name in scope_ids}

vimba = Vimba()
vimba.startup()
print(id(vimba))
print(vimba.getCameraIds())
# time.sleep(1)
for cam_id, name in cam_ids:
    cam = Vimba_Camera(cam_id, vimba=vimba)
    sett = settings.copy()
    sett.update(settings_per_camera[name])
    cam.set_features(sett)
    roi = ROIs[name]
    if roi is not None:
        cam.set_roi(roi)
    # cam.print_feature_description('TriggerMode')
    cameras[name] = cam
    # time.sleep(0.2)


i = 0

pool = ThreadPoolExecutor(max_workers=5)

def close_all():
    pass
    # for cam in cameras.values():
        # cam.close()
    # vimba.shutdown()
    # pool.shutdown(wait=True)
    
# def loop():

while True:
# This happens at the very end of ---------------------
    with open(save_sequence_path, 'r') as f:
            save_dict = json.load(f)
    if save_dict['get_scope']:
        for scope in scopes.values():
            scope.arm()
    
    cameras_threads = {}
    for camera_name, cam in cameras.items():        
        number_of_frames = save_dict['number_of_frames'][camera_name]
        print(f"Submit to pool for {number_of_frames} frames on {camera_name} camera")
        thread = pool.submit(cam.grab_multiple, N=number_of_frames, trigger=True)
        cameras_threads[camera_name] = thread
        
    # images = {name: thread.result() for name, thread in cameras_threads.items()}
    images = {}
    for camera_name, thread in cameras_threads.items():
        print(f"Wait images from {camera_name}")
        # print("I would ask for the thread.result here")
        # time.sleep(1)
        images[camera_name] = thread.result()

        
    
    for name, im in images.items():
        print(name, im.dtype) # here it will say uint16
    
    with open(program_log_path, 'r') as f:
        program_dict = json.load(f)
    program_attrs = program_dict.copy()
    program_attrs.pop('program')
    program_attrs.pop('variables')
    # cast them from uint16 to float64

    
    
    now = datetime.now()
    if save_dict['save']:
        h5path = h5path_0/now.strftime('%Y/%Y-%m-%d')/save_dict['run_name']
        h5path.mkdir(parents=True, exist_ok=True)
        ix = scooper.get_last_sequence_index(h5path)
        attrs['sequence_index'] = ix + 1
        attrs['sequence_id'] = now.strftime('%Y_%m_%d') + '_' + save_dict['run_name']
    else:
        h5path = h5path_0/'_temp'
        ix = scooper.get_last_sequence_index(h5path)
        attrs['sequence_index'] = ix + 1
        attrs['sequence_id'] = now.strftime('%Y_%m_%d') + '_data'
        # make scooper clean up now
        try:
            os.remove(h5filepath)
        except Exception as e:
            print(e)
            pass
    
    # -------------------------------------------------------
        
    attrs['run time'] = now.isoformat()
    h5filepath = h5path / f"{attrs['sequence_id']}_{attrs['sequence_index']:04d}.h5"
    scooper.make_new_h5file(h5filepath, attrs)
    
    
    # print(program_dict)
    # -------------------------------------------------------
    # here put whatever data you want in the h5 file
    with h5py.File(h5filepath) as h5file:
        for camera_name, im in images.items():
            h5file[f'data/{camera_name}/raw'] = im
            h5file[f'data/{camera_name}/raw'].attrs['camera'] = camera_name
        if save_dict['get_scope']:
            for name, scope in scopes.items():
                data, t = scope.get_all_traces()
                h5file[f'data/{name}/t'] = t
                h5file[f'data/{name}/data'] = data
        h5file['data'].attrs['run_name'] = save_dict['run_name']
        for k, v in program_dict['variables'].items():
            h5file['globals'].attrs[k] = v
        h5file['experiment'] = str(program_dict)
        for k, v in program_attrs.items():
            # print(k)
            h5file['experiment'].attrs[k] = v
    
    # submit to lyse
    scooper.submit_to_lyse(h5filepath)
    i += 1
    

# try:
    # while True:
        # loop()  
    # print('END')
# except KeyboardInterrupt as e:
    # print(e)
    # close things here
    # for cam in cameras.values():
        # cam.close()
    # pool.shutdown(wait=True)
    
    # traceback.print_exc(file=sys.stdout)
    # try:
        # sys.exit(0)
    # except SystemExit:
        # os._exit(0)
    
        
        