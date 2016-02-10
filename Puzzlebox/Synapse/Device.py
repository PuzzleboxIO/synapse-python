# -*- coding: utf-8 -*-

# Copyright Puzzlebox Productions, LLC (2010-2012)
#
# This code is released under the GNU Pulic License (GPL) version 2
# For more information please refer to http://www.gnu.org/copyleft/gpl.html

__changelog__ = """\
Last Update: 2012.04.23
"""

__todo__ = """
"""

### IMPORTS ###
import os, sys

import Puzzlebox.Synapse.Configuration as configuration

if configuration.ENABLE_PYSIDE:
	try:
		import PySide as PyQt4
		from PySide import QtCore, QtGui
	except Exception, e:
		print "ERROR: [Synapse:Device] Exception importing PySide:",
		print e
		configuration.ENABLE_PYSIDE = False
	else:
		print "INFO: [Synapse:Device] Using PySide module"

if not configuration.ENABLE_PYSIDE:
	print "INFO: [Synapse:Device] Using PyQt4 module"
	from PyQt4 import QtCore, QtGui

if (sys.platform == 'win32'):
	import _winreg as winreg
	import itertools
	import re
	import serial
	DEFAULT_IMAGE_PATH = 'images'
elif (sys.platform == 'darwin'):
	DEFAULT_IMAGE_PATH = 'images'
else:
	import bluetooth
	DEFAULT_IMAGE_PATH = '/usr/share/puzzlebox_synapse/images'


#####################################################################
# Globals
#####################################################################

DEBUG = configuration.DEBUG

PATH_TO_HCITOOL = '/usr/bin/hcitool'


#####################################################################
# Classes
#####################################################################

class puzzlebox_synapse_device(QtGui.QWidget):
	
	def __init__(self, log, \
	             DEBUG=DEBUG, \
	             parent=None, \
	             ):
		
		self.log = log
		self.DEBUG = DEBUG
		self.parent=parent
		
		if self.parent == None:
			QtGui.QWidget.__init__(self, parent)
			#self.setupUi(self)
		
			self.configureSettings()
			self.connectWidgets()
		
		self.name = "Synapse:Device"
	
	
	##################################################################
	
	def configureSettings(self):
		
		pass
	
	
	##################################################################
	
	def connectWidgets(self):
		
		pass
	
	
	##################################################################
	
	def enumerateSerialPorts(self):
		
		""" Uses the Win32 registry to return an
		iterator of serial (COM) ports
		existing on this computer.
		
		from http://eli.thegreenplace.net/2009/07/31/listing-all-serial-ports-on-windows-with-python/
		"""
	 
		path = 'HARDWARE\\DEVICEMAP\\SERIALCOMM'
		try:
			key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
		except WindowsError:
			#raise IterationError
			return
		
		for i in itertools.count():
			try:
				val = winreg.EnumValue(key, i)
				yield str(val[1])
			except EnvironmentError:
				break
	
	
	##################################################################
	
	def fullPortName(self, portname):
		
		""" Given a port-name (of the form COM7,
		COM12, CNCA0, etc.) returns a full
		name suitable for opening with the
		Serial class.
		"""
		
		m = re.match('^COM(\d+)$', portname)
		if m and int(m.group(1)) < 10:
			return portname
		
		return '\\\\.\\' + portname
	
	
	##################################################################
	
	def searchForSerialDevices(self, devices=[]):
		
		if (sys.platform == 'win32'):
			
			for portname in self.enumerateSerialPorts():
				
				if portname not in devices:
					#portname = self.fullPortName(portname)
					devices.append(portname)
		
		
		elif (sys.platform == 'darwin'):
		  
		  # Handle Telekinesis first so it shows up at top of listings
		  for device in os.listdir('/dev'):
			 if (device.startswith('tty.Telekinesis')):
					
					devices.append( os.path.join('/dev', device))
		  
		  for device in os.listdir('/dev'):
			 if (device.startswith('tty.MindWaveMobile') or \
			     device.startswith('tty.MindWave')):
					 
					 devices.append( os.path.join('/dev', device))
			
			
		  # Handle MindSet separately so it shows up second in listings
		  for device in os.listdir('/dev'):
			 if (device.startswith('tty.MindSet')):
					 
					 devices.append( os.path.join('/dev', device))
		
		else:
			
			#if os.path.exists('/dev/tty.MindWaveMobile-SPPDev'):
				#devices.append('/dev/tty.MindWaveMobile-SPPDev')
			#if os.path.exists('/dev/tty.MindWaveMobile-DevA'):
				#devices.append('/dev/tty.MindWaveMobile-DevA')
			#if os.path.exists('/dev/tty.MindWaveMobile-DevB'):
				#devices.append('/dev/tty.MindWaveMobile-DevB')
			
			#if os.path.exists('/dev/tty.MindWave'):
				#devices.append('/dev/tty.MindWave')
			#if os.path.exists('/dev/tty.MindWave1'):
				#devices.append('/dev/tty.MindWave1')
			#if os.path.exists('/dev/tty.MindWave2'):
				#devices.append('/dev/tty.MindWave2')
			#if os.path.exists('/dev/tty.MindWave3'):
				#devices.append('/dev/tty.MindWave3')
			#if os.path.exists('/dev/tty.MindWave4'):
				#devices.append('/dev/tty.MindWave4')
			#if os.path.exists('/dev/tty.MindWave5'):
				#devices.append('/dev/tty.MindWave5')
			
			#if os.path.exists('/dev/tty.MindSet-DevB'):
				#devices.append('/dev/tty.MindSet-DevB')
			
			
		  for device in os.listdir('/dev'):
			 if (device.startswith('ttyUSB') or \
			     device.startswith('ttyACM') or \
			     device.startswith('tty.usbserial') or \
			     device.startswith('rfcomm')):
					 
					 devices.append( os.path.join('/dev', device))
			
			#if os.path.exists('/dev/ttyUSB0'):
				#devices.append('/dev/ttyUSB0')
			#if os.path.exists('/dev/ttyUSB1'):
				#devices.append('/dev/ttyUSB1')
			#if os.path.exists('/dev/ttyUSB2'):
				#devices.append('/dev/ttyUSB2')
			#if os.path.exists('/dev/ttyUSB3'):
				#devices.append('/dev/ttyUSB3')
			#if os.path.exists('/dev/ttyUSB4'):
				#devices.append('/dev/ttyUSB4')
			#if os.path.exists('/dev/ttyUSB5'):
				#devices.append('/dev/ttyUSB5')
			#if os.path.exists('/dev/ttyUSB6'):
				#devices.append('/dev/ttyUSB6')
			#if os.path.exists('/dev/ttyUSB7'):
				#devices.append('/dev/ttyUSB7')
			#if os.path.exists('/dev/ttyUSB8'):
				#devices.append('/dev/ttyUSB8')
			#if os.path.exists('/dev/ttyUSB9'):
				#devices.append('/dev/ttyUSB9')
			
			#if os.path.exists('/dev/rfcomm0'):
				#devices.append('/dev/rfcomm0')
			#if os.path.exists('/dev/rfcomm1'):
				#devices.append('/dev/rfcomm1')
			#if os.path.exists('/dev/rfcomm2'):
				#devices.append('/dev/rfcomm2')
			#if os.path.exists('/dev/rfcomm3'):
				#devices.append('/dev/rfcomm3')
			#if os.path.exists('/dev/rfcomm4'):
				#devices.append('/dev/rfcomm4')
			
			#if os.path.exists('/dev/ttyACM0'):
				#devices.append('/dev/ttyACM0')
			#if os.path.exists('/dev/ttyACM1'):
				#devices.append('/dev/ttyACM1')
			#if os.path.exists('/dev/ttyACM2'):
				#devices.append('/dev/ttyACM2')
			#if os.path.exists('/dev/ttyACM3'):
				#devices.append('/dev/ttyACM3')
			#if os.path.exists('/dev/ttyACM4'):
				#devices.append('/dev/ttyACM4')
		
		
		return(devices)
	
	
	##################################################################
	
	def hcitoolScanForRemoteDevices(self, devices=[]):
		
		bluetooth_devices = []
		
		#command = '%s scan 2> /dev/null' % PATH_TO_HCITOOL
		command = '%s scan' % PATH_TO_HCITOOL
		
		if self.DEBUG > 1:
			print 'INFO: Calling "%s"' % command 
		
		output = os.popen(command, 'r')
		
		try:
			result = output.readlines()
		except Exception, e:
			if self.DEBUG:
				print "ERROR [Synapse-Interface]: Failed reading result from call to hcitool:",
				print e
			result = ''
		
		if result == '':
			return([]) # Under OS X hcitool doesn't exist so we don't see any devices
		
		for line in result:
			line = line.strip()
			if line == '' or line == 'Scanning ...':
				continue
			elif self.DEBUG > 1:
				print line
			try:
				address = line.split('\t')[0]
			except:
				pass
			else:
				bluetooth_devices.append(address)
		
		
		for address in bluetooth_devices:
			
			command = '%s name %s' % (PATH_TO_HCITOOL, address)
			
			if self.DEBUG:
				print 'INFO: Calling "%s"' % command
			
			output = os.popen(command, 'r')
			
			for line in output.readlines():
				line = line.strip()
				if line == '':
					continue
				elif self.DEBUG:
					print '\t',
					print line
				
				device_name = line.strip()
			
				if ((device_name == 'MindSet' or device_name == 'MindWave Mobile') and \
					(address not in devices)):
					devices.append(address)
				
				else:
					if self.DEBUG:
						print 'INFO: Found but not recognized: [%s] %s' % \
							(address, device_name)
		
		
		return (devices)
	
	
	##################################################################
	
	def hcitoolGetActiveConnections(self, devices=[]):
		
		bluetooth_devices = []
		
		#command = '%s con 2> /dev/null' % PATH_TO_HCITOOL
		command = '%s con' % PATH_TO_HCITOOL
		
		if self.DEBUG > 1:
			print 'INFO: Calling "%s"' % command 
		
		output = os.popen(command, 'r')
		
		try:
			result = output.readlines()
		except Exception, e:
			if self.DEBUG:
				print "ERROR [Synapse:Interface]: Failed reading result from call to hcitool:",
				print e
			result = ''

		if result == '':
			return([]) # Under OS X hcitool doesn't exist so we don't see any devices

		for line in result:
			line = line.strip()
			if line == '' or line == 'Connections:':
				continue
			elif self.DEBUG > 1:
				print line
			try:
				address = line.split(' ')[2]
			except:
				pass
			else:
				bluetooth_devices.append(address)
		
		
		for address in bluetooth_devices:
			
			command = '%s name %s' % (PATH_TO_HCITOOL, address)
			
			if self.DEBUG:
				print 'INFO: Calling "%s":' % command
			
			output = os.popen(command, 'r')
			
			for line in output.readlines():
				line = line.strip()
				if line == '':
					continue
				elif self.DEBUG:
					print '\t',
					print line
				
				device_name = line.strip()
			
				if ((device_name == 'MindSet' or device_name == 'MindWave Mobile') and \
					(address not in devices)):
					devices.append(address)
		
		
		return (devices)
	
	
	##################################################################
	
	def searchForDevices(self):
		
		enable_hcitool = configuration.ENABLE_HCITOOL
		
		devices = []
		
		#self.pushButtonBluetoothSearch.setText('Searching')
		
		if ((sys.platform != 'win32' and sys.platform != 'darwin') and \
		     configuration.THINKGEAR_BLUETOOTH_SEARCH):
			
			# Bluetooth module doesn't compile properly under Windows
			# and doesn't exist under OS X
			
			# PyBluez API Documentation
			# http://pybluez.googlecode.com/svn/www/docs-0.7/index.html
			
			bluetooth_devices = []
			
			if not enable_hcitool:
				
				try:
					
					if self.DEBUG:
						print "INFO: Searching for Bluetooth devices using PyBluez module"
					
					bluetooth_devices = bluetooth.discover_devices( \
					      duration=configuration.THINKGEAR_BLUETOOTH_DISCOVER_DEVICES_TIMEOUT, \
					                       flush_cache=True, \
					                       lookup_names=False)
					
					for address in bluetooth_devices:
						
						if self.DEBUG:
							print "INFO: Device discovered",
							print address
						
						device_name = bluetooth.lookup_name(address, \
						                 configuration.THINKGEAR_BLUETOOTH_LOOKUP_NAME_TIMEOUT)
						if ((device_name == 'MindSet' or device_name == 'MindWave Mobile') and \
							(address not in devices)):
							devices.append(address)
					
					
					# There is an issue under recent released of Linux
					# in which already-connected Bluetooth ThinkGear devices
					# are not appearing in a bluetooth device scan. However,
					# using "hcitool" connected devices can be listed correctly.
					# There does not appear to be an equivalent PyBluez feature.
					# (http://pybluez.googlecode.com/svn/www/docs-0.7/index.html)
					
					if devices == []:
						if self.DEBUG:
							print "INFO: No devices found through PyBluez module. Falling back to hcitool."
						devices = self.hcitoolGetActiveConnections(devices)
				
				
				except Exception, e:
					if self.DEBUG:
						print "ERROR: Exception calling Python Bluetooth module. (Is PyBluez installed?):"
						print e
					
					
					#if (sys.platform != 'darwin'):
					enable_hcitool = True
			
			
			if enable_hcitool:
				
				devices = self.hcitoolScanForRemoteDevices(devices)
				devices = self.hcitoolGetActiveConnections(devices)
			
			
			if self.DEBUG > 2:
				print "Bluetooth Devices found:",
				print devices
		
		
		devices = self.searchForSerialDevices(devices)
		
		
		if self.DEBUG:
			print "Devices found:",
			print devices
		
		
		return(devices)

