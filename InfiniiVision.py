import visa
import time
import numpy as np
import logging
import sys

__version__ = '0.1.0'

log = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


class InfiniiVision2000Scope(object):

    def __init__(self, name='USB0::0x0699::0x0368::C102896::INSTR'):

        rm = visa.ResourceManager()
        self.visa = rm.open_resource(name)
        log.info(f'Opening scope {name}.')
        self.channels = [f'channel{idx}' for idx in range(1, 5)]
        
        # use all the channels
        for channel in self.channels:
            self.visa.write(f'{channel}:display on')
        
        # make sure we are acquiring without averaging
        self.visa.write('acquire:type normal')
        self.name = name
    
    def arm(self):
        log.info(f'Arming scope {self.name}.')
        self.visa.write('digitize')
    
    def get_trace(self, channel):
        
        # point to the right channel
        self.visa.write(f'waveform:source {channel}')
        
        while True:
            try:
                self.visa.query('ter?')
            except visa.VisaIOError:  # probably a timeout
                print('.', end='')
                pass
            else:
                break
            
        data = self.visa.query_binary_values('waveform:data?', 
                    datatype=u'B', is_big_endian=True, container=np.array) # datatype='b'
        data = data.astype(np.float)
        # print(data.dtype)
        data =  self._rescale_data(data, channel)
        return data, self._get_timescale()

        
    def get_all_traces(self):
    
        def _delayed_get(channel):
            time.sleep(0.5)
            data, t = self.get_trace(channel)
            return data
            
    
        return np.array([_delayed_get(channel) for channel in self.channels]), self._get_timescale()
            
    def _get_trace_info(self, channel):
        # preamble block from p.476 in Programmer's Manual
        # <format, type, points, count, xincrement, xorigin, xreference, 
        # yincrement, yorigin, yreference>
        preamble = self.visa.query('waveform:preamble?')
        # print(preamble)
        params = np.fromstring(preamble, sep=',')
        # print(f'params {params.dtype}') # this is already float64
        return params
    
    def _rescale_data(self, data, channel):

        params = self._get_trace_info(channel)
        data = params[8] + params[7] * (data - params[9])

        return data


    def _get_timescale(self):

        params = self._get_trace_info('channel1')
        data = params[5] + params[4] * (np.arange(params[2]) - params[6])

        return data
    


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    from scipy.signal import medfilt
    
    scope = InfiniiVision2000Scope('USB0::0x0957::0x1796::MY55140782::INSTR')
    scope.arm()
    time.sleep(5)
    # data = scope.get_all_traces()
    info = scope._get_trace_info('channel2')
    print(info)
    data, t = scope.get_trace('channel2')
    print(data.dtype)
    data = scope._rescale_data(data, 'channel2')
    # data, t = scope.get_all_traces()
    print(data.shape)
    plt.plot(t*1e-6, data)
    plt.show()
