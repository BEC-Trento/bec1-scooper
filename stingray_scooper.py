from vimba_camera import Vimba_Camera
from InfiniiVision import InfiniiVision2000Scope
import numpy as np
from sis2_lib import write_sis
import os
import scooper
from datetime import datetime
from pathlib import Path
import h5py
import glob

import json
program_log_path = r'C:\SIScam\SIScamProgram\Prog\img\last-program.json'
save_sequence_path = r'scooper_save_sequence.json'

sispath = r'C:\SIScam\SIScamProgram\Prog\img\test_0.sis'

# cam_id = 'DEV_0xA4701110AE920' # testing camera on Dimitri's pc

cam_id, camera_name = 'DEV_0xA4701110A5767', 'horiz1' # Stingary horiz1 (M = 1.3)
# cam_id, camera_name = 'DEV_0xA4701110AE920', 'horiz4' # Stingary horiz4 (M = 4.2)
# cam_id, camera_name = 'DEV_0xA4701110A64FE', 'vert' # Stingary horiz4 (M = 4.2)

scope_ids = [
             ['USB0::0x0957::0x1796::MY55140782::INSTR', 'scope'], # scope 1
             ['USB0::0x0957::0x1796::MY55140778::INSTR', 'scope2'], # scope 1
             ]
# scope_id = '' # scope 2

# number_of_frames = 3
WRITE_SYS = False

# these settings should work well for capturing 3 images
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
        }
    }

settings.update(settings_per_camera[camera_name])
# Binning can increase SNR while reducing field of view.
# See Format7 modes for details.
# settings['IIDCMode'] = 'Mode1'


# get some default paramaters for scooper

attrs = {}
attrs['run number'] = 0
attrs['run repeat'] = 0
h5path_0 = Path(r'D:\SIScam\SIScamProgram\Prog\img')

scopes = []
scope_names = []
for id, name in scope_ids:
    scopes.append(InfiniiVision2000Scope(id))
    scope_names.append(name)


with Vimba_Camera(cam_id) as cam:
    cam.set_features(settings)
    i = 0
    while True: # i < 1:
    # This happens at the very end of ---------------------
        with open(save_sequence_path, 'r') as f:
                save_dict = json.load(f)
        if save_dict['get_scope']:
            for scope in scopes:
                scope.arm()
        number_of_frames = save_dict['number_of_frames']
        print(f"Waiting for {number_of_frames} frames on {camera_name} camera")
        images = cam.grab_multiple(N=number_of_frames, trigger=True)
        print(images.dtype) # here it will say uint16
        
        with open(program_log_path, 'r') as f:
            program_dict = json.load(f)
        program_attrs = program_dict.copy()
        program_attrs.pop('program')
        program_attrs.pop('variables')
        # cast them from uint16 to float64

        if WRITE_SYS:
            probe, atoms, bg = images.copy()
            atoms -= bg
            probe -= bg
            od = -np.log(atoms.clip(1) / probe.clip(1)) 
        
             # get rid of the file first
            os.remove(sispath)
            write_sis(sispath, od)
            np.save(sispath+'.raw.npy', images)
        
        
        
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
            h5file['data/images/raw'] = images
            if save_dict['get_scope']:
                for scope, name in zip(scopes, scope_names):
                    data, t = scope.get_all_traces()
                    h5file[f'data/{name}/t'] = t
                    h5file[f'data/{name}/data'] = data
            h5file['data'].attrs['run_name'] = save_dict['run_name']
            h5file['data/images/raw'].attrs['camera'] = camera_name
            for k, v in program_dict['variables'].items():
                h5file['globals'].attrs[k] = v
            h5file['experiment'] = str(program_dict)
            for k, v in program_attrs.items():
                # print(k)
                h5file['experiment'].attrs[k] = v
        
        # submit to lyse
        scooper.submit_to_lyse(h5filepath)
        i += 1
    print('END')
        
        
        