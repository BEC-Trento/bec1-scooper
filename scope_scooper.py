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
import time

import json
program_log_path = r'C:\SIScam\SIScamProgram\Prog\img\last-program.json'
save_sequence_path = r'scooper_save_sequence.json'


scope_id = 'USB0::0x0957::0x1796::MY55140782::INSTR'


# get some default paramaters for scooper

attrs = {}
temp_sequence_index = 0
attrs['run number'] = 0
attrs['run repeat'] = 0
h5path_0 = Path(r'D:\SIScam\SIScamProgram\Prog\img')

scope = InfiniiVision2000Scope(scope_id)   



while True:
# This happens at the very end of ---------------------
    with open(save_sequence_path, 'r') as f:
            save_dict = json.load(f)
    scope.arm()
    time.sleep(save_dict['scope_timeout'])   
    
    with open(program_log_path, 'r') as f:
            program_dict = json.load(f)
    now = datetime.now()
    if save_dict['save']:
        h5path = h5path_0/now.strftime('%Y/%Y-%m-%d')/save_dict['run_name']
        h5path.mkdir(parents=True, exist_ok=True)
        count = len(glob.glob1(h5path, '*.h5'))
        attrs['sequence_index'] = count
        attrs['sequence_id'] = now.strftime('%Y_%m_%d') + '_' + save_dict['run_name']
    else:
        h5path = h5path_0/'_temp'
        attrs['sequence_index'] = temp_sequence_index
        temp_sequence_index += 1
        attrs['sequence_id'] = now.strftime('%Y_%m_%d') + '_data'
        # make scooper clean up now
        try:
            os.remove(h5filepath)
        except Exception as e:
            print(e)
            pass
    
    # -------------------------------------------------------
        
    attrs['run time'] = now.isoformat()
    h5filepath = h5path / f"{attrs['sequence_id']}_{attrs['sequence_index']}.h5"
    scooper.make_new_h5file(h5filepath, attrs)
    
    
    # print(program_dict)
    # -------------------------------------------------------
    # here put whatever data you want in the h5 file
    with h5py.File(h5filepath) as h5file:
        data, t = scope.get_all_traces()
        h5file['data/scope/t'] = t
        h5file['data/scope/data'] = data
        h5file['data'].attrs['run_name'] = save_dict['run_name']
        
        for k, v in program_dict['variables'].items():
            h5file['globals'].attrs[k] = v
        h5file['experiment'] = str(program_dict)
    
    # submit to lyse
    scooper.submit_to_lyse(h5filepath)
    time.sleep(2)
       
        
        
        