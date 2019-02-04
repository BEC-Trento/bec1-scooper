from pymba import Vimba, VimbaException
import logging
import sys

__version__ = '0.1.0'

log = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


class Vimba_Camera:
		
	def enumerate_cameras():
		# get connected camera ids
		with Vimba() as vimba:
			return vimba.getCameraIds()  # list of camera ids
	
	def __init__(self, name):
		# need to startup to do anything
		self.startup()
		
		cams = Vimba_Camera.enumerate_cameras()
		
		# check if the camera exists
		if name not in cams:
			raise NameError(
				f'Camera {cam_id} not found in list of connected cameras.')
		
		# connect to the camera you want
		self.camera = self.vimba.getCamera(name)
	
	def startup(self):
		vimba = Vimba()
		vimba.startup()
		self.vimba = vimba
			
	def open(self):
		# need to open it to do anything with it
		self.camera.openCamera()
		log.info(f'Opening camera.')
	
	def close(self):
		# need to open it to do anything with it
		self.camera.closeCamera()
		log.info(f'Closing camera.')
		
		self.vimba.shutDown()
		log.info(f'Shutting down vimba.')
	

	def version():
		return Vimba().getVersion()
	

	
		
	
		



if __name__ == '__main__':
	
	cam_id = 'DEV_0xA4701110AE920'
	
	# class methods
	print(Vimba_Camera.version())
	print(Vimba_Camera.enumerate_cameras())
	
	# object methods
	cam = Vimba_Camera(cam_id)
	# cam.open()
	# cam.close()
	
	
	
	
	
	