# -*- coding: utf-8 -*-

# Copyright Puzzlebox Productions, LLC (2010-2016)
#
# This code is released under the GNU Affero Pulic License (AGPL) version 3
# For more information please refer to https://www.gnu.org/licenses/agpl.html
#
# Author: Steve Castellotti <sc@puzzlebox.io>

__changelog__ = """\
Last Update: 2014.02.12
"""

#####################################################################
# Imports
#####################################################################

import os, sys, time
import math

import simplejson as json

import Puzzlebox.Synapse.Configuration as configuration

if configuration.ENABLE_PYSIDE:
	try:
		import PySide as PyQt4
		from PySide import QtCore, QtGui, QtNetwork
	except Exception, e:
		print "ERROR: Exception importing PySide:",
		print e
		configuration.ENABLE_PYSIDE = False
	else:
		print "INFO: [Synapse:ThinkGear:Server] Using PySide module"

if not configuration.ENABLE_PYSIDE:
	print "INFO: [Synapse:ThinkGear:Server] Using PyQt4 module"
	from PyQt4 import QtCore, QtGui, QtNetwork


if configuration.ENABLE_CLOUDBRAIN:
	#from brainsquared.publishers.PikaPublisher import PikaPublisher
	import Puzzlebox.Synapse.Cloudbrain.Publisher as cloudbrain_publisher


import Puzzlebox.Synapse.Server as synapse_server
import Puzzlebox.Synapse.ThinkGear.Protocol as thinkgear_protocol



#####################################################################
# Globals
#####################################################################

DEBUG = configuration.DEBUG

COMMUNICATION_MODE = 'Emit Signal'
#COMMUNICATION_MODE = 'Call Parent'

SERVER_INTERFACE = configuration.THINKGEAR_SERVER_INTERFACE
SERVER_PORT = configuration.THINKGEAR_SERVER_PORT
DEFAULT_DEVICE_MODEL = 'NeuroSky MindWave'
THINKGEAR_DEVICE_SERIAL_PORT = configuration.THINKGEAR_DEVICE_SERIAL_PORT

CLIENT_NO_REPLY_WAIT = configuration.CLIENT_NO_REPLY_WAIT * 1000

FLASH_POLICY_FILE_REQUEST = configuration.FLASH_POLICY_FILE_REQUEST
FLASH_SOCKET_POLICY_FILE = configuration.FLASH_SOCKET_POLICY_FILE

DELIMITER = configuration.THINKGEAR_DELIMITER

MESSAGE_FREQUENCY_TIMER = 1 * 1000 # 1 Hz (1000 ms)

ENABLE_SIMULATE_HEADSET_DATA = configuration.THINKGEAR_ENABLE_SIMULATE_HEADSET_DATA

BLINK_FREQUENCY_TIMER = configuration.THINKGEAR_BLINK_FREQUENCY_TIMER

DEFAULT_SAMPLE_WAVELENGTH = configuration.THINKGEAR_DEFAULT_SAMPLE_WAVELENGTH

THINKGEAR_EMULATION_MAX_ESENSE_VALUE = \
	configuration.THINKGEAR_EMULATION_MAX_ESENSE_VALUE
THINKGEAR_EMULATION_MAX_EEG_POWER_VALUE = \
	configuration.THINKGEAR_EMULATION_MAX_EEG_POWER_VALUE

THINKGEAR_ATTENTION_MULTIPLIER = configuration.THINKGEAR_ATTENTION_MULTIPLIER
THINKGEAR_MEDITATION_MULTIPLIER = configuration.THINKGEAR_MEDITATION_MULTIPLIER
THINKGEAR_MEDITATION_PLOT_OFFSET = configuration.THINKGEAR_MEDITATION_PLOT_OFFSET

THINKGEAR_EEG_POWER_MULTIPLIERS = configuration.THINKGEAR_EEG_POWER_MULTIPLIERS

DEFAULT_AUTHORIZATION_MESSAGE = \
	{"isAuthorized": True}
		# Tells the client whether the server has authorized
		# access to the user's headset data. The value is
		# either true or false.

DEFAULT_SIGNAL_LEVEL_MESSAGE = \
	{"poorSignalLevel": 0}
		# A quantifier of the quality of the brainwave signal.
		# This is an integer value that is generally in the
		# range of 0 to 200, with 0 indicating a
		# good signal and 200 indicating an off-head state.

DEFAULT_EEG_POWER_MESSAGE = \
	{"eegPower": { \
		'delta': 0, \
		'theta': 0, \
		'lowAlpha': 0, \
		'highAlpha': 0, \
		'lowBeta': 0, \
		'highBeta': 0, \
		'lowGamma': 0, \
		'highGamma': 0, \
		}, \
	} # A container for the EEG powers. These may
	  # be either integer or floating-point values.
	  # Maximum values are undocumented but assumed to be 65535

DEFAULT_ESENSE_MESSAGE = \
	{"eSense": { \
		'attention': 0, \
		'meditation': 0, \
		}, \
	} # A container for the eSense™ attributes.
	  # These are integer values between 0 and 100,
	  # where 0 is perceived as a lack of that attribute
	  # and 100 is an excess of that attribute.

DEFAULT_BLINK_MESSAGE = {"blinkStrength": 255}
	# The strength of a detected blink. This is
	# an integer in the range of 0-255.

DEFAULT_RAWEEG_MESSAGE = {"rawEeg": 255}
	# The raw data reading off the forehead sensor.
	# This may be either an integer or a floating-point value.

DEFAULT_PACKET = {}
DEFAULT_PACKET.update(DEFAULT_EEG_POWER_MESSAGE)
DEFAULT_PACKET.update(DEFAULT_SIGNAL_LEVEL_MESSAGE)
DEFAULT_PACKET.update(DEFAULT_ESENSE_MESSAGE)

DEFAULT_RESPONSE_MESSAGE = DEFAULT_SIGNAL_LEVEL_MESSAGE

#PACKET_MINIMUM_TIME_DIFFERENCE_THRESHOLD = 0.75

#####################################################################
# Classes
#####################################################################

class puzzlebox_synapse_server_thinkgear(synapse_server.puzzlebox_synapse_server):
	
	def __init__(self, log,
		          server_interface=SERVER_INTERFACE,
		          server_port=SERVER_PORT,
		          device_model=None,
		          device_address=THINKGEAR_DEVICE_SERIAL_PORT,
		          emulate_headset_data=ENABLE_SIMULATE_HEADSET_DATA,
		          rabbitmq_host=configuration.RABBITMQ_HOST,
		          rabbitmq_username=configuration.RABBITMQ_USERNAME,
		          rabbitmq_password=configuration.RABBITMQ_PASSWORD,
		          publisher_username=configuration.PUBLISHER_USERNAME,
		          publisher_device=configuration.PUBLISHER_DEVICE,
		          publisher_metric=configuration.PUBLISHER_METRIC,
		          DEBUG=DEBUG, 
		          parent=None):
		
		QtCore.QThread.__init__(self,parent)
		
		self.log = log
		self.DEBUG = DEBUG
		self.parent = parent
		
		self.server_interface = server_interface
		self.server_port = server_port
		self.device_address = device_address
		self.device_model = device_model
		self.emulate_headset_data = emulate_headset_data
		
		self.name = 'Synapse:ThinkGear:Server'
		
		self.connection_timestamp = time.time()
		self.session_start_timestamp = time.time()
		
		self.connections = []
		self.packet_queue = []
		
		self.serial_device = None
		self.protocol = None
		self.cloudbrain_publisher = None
		
		self.connect(self, \
		             QtCore.SIGNAL("sendPacket()"), \
		             self.sendPacketQueue)
		
		self.message_frequency_timer = MESSAGE_FREQUENCY_TIMER
		self.blink_frequency_timer = BLINK_FREQUENCY_TIMER
		self.blink_timestamp = time.time()
		
		
		#self.customDataHeaders = 'Attention,Meditation,Signal Level,Delta,Theta,Low Alpha,High Alpha,Low Beta,High Beta,Low Gamma,Mid Gamma'
		self.customDataHeaders = ['Attention', \
		                          'Meditation', \
		                          'Signal Level', \
		                          'Delta', \
		                          'Theta', \
		                          'Low Alpha', \
		                          'High Alpha', \
		                          'Low Beta', \
		                          'High Beta', \
		                          'Low Gamma', \
		                          'Mid Gamma', \
		                         ]
		
		
		self.configureEEG()
		
		if (self.server_interface != None):
			self.configureNetwork()
		
		
		if (self.emulate_headset_data):
			self.emulationTimer = QtCore.QTimer()
			QtCore.QObject.connect(self.emulationTimer, \
				                    QtCore.SIGNAL("timeout()"), \
				                    self.emulationEvent)
			self.emulationTimer.start(MESSAGE_FREQUENCY_TIMER)
			
			
			
		# Cloudbrain
		
		if configuration.ENABLE_CLOUDBRAIN:
			
			self.cloudbrain_publisher = \
				cloudbrain_publisher.puzzlebox_synapse_cloudbrain_publisher( \
					log, \
					rabbitmq_host=configuration.RABBITMQ_HOST,
					rabbitmq_username=configuration.RABBITMQ_USERNAME,
					rabbitmq_password=configuration.RABBITMQ_PASSWORD,
					publisher_username=configuration.PUBLISHER_USERNAME,
					publisher_device=configuration.PUBLISHER_DEVICE,
					publisher_metric=configuration.PUBLISHER_METRIC,
					DEBUG=DEBUG, \
					parent=None)
			
			self.cloudbrain_publisher.start()
	
	
	##################################################################
	
	def configureEEG(self):
		
		if not self.emulate_headset_data:
			
			self.serial_device = \
				thinkgear_protocol.SerialDevice( \
				#self.serial_device = NeuroskyConnector.SerialDevice(
					self.log, \
					device_address=self.device_address, \
					DEBUG=self.DEBUG, \
					parent=self)
			
			self.serial_device.start()
		
		else:
			self.serial_device = None
		
		
		self.protocol = \
			thinkgear_protocol.puzzlebox_synapse_protocol_thinkgear( \
			#NeuroskyConnector.puzzlebox_synapse_protocol_thinkgear( \
				self.log, \
				self.serial_device, \
				device_model=self.device_model, \
				DEBUG=self.DEBUG, \
				parent=self)
		
		#self.plugin_session = self.parent.plugin_session # for Jigsaw compatability
		
		self.protocol.start()
	
	
	##################################################################
	
	def emulationEvent(self):
		
		self.updateStatus()
		
		if COMMUNICATION_MODE == 'Emit Signal':
			self.emitSendPacketSignal()
		else:
			self.sendPacketQueue()
	
	
	##################################################################
	
	def processData(self, data):
		
		response = None
		
		# Special socket handling for Flash applications
		if (data == FLASH_POLICY_FILE_REQUEST):
			
			response = FLASH_SOCKET_POLICY_FILE
			
			#self.packet_queue.insert(0, FLASH_SOCKET_POLICY_FILE)
		
		
		elif (type(data) == type({}) and \
		      data.has_key('appName') and \
		      data.has_key('appKey')):
			
			authorized = self.authorizeClient(data)
			
			response = {}
			response['isAuthorized'] = authorized
			
			#self.packet_queue.insert(0, response)
		
		
		return(response)
	
	
	##################################################################
	
	def validateChecksum(self, checksum):
		
		'''The key used by the client application to identify 
itself. This must be 40 hexadecimal characters, ideally generated
using an SHA-1 digest. The appKey is an identifier that is unique
to each application, rather than each instance of an application.
It is used by the server to bypass the authorization process if a
user had previously authorized the requesting client. To reduce
the chance of overlap with the appKey of other applications, 
the appKey should be generated using an SHA-1 digest.'''
		
		is_valid = True
		
		hexadecimal_characters = '0123456789abcdef'
		
		if len(checksum) != 40:
			is_valid = False
		else:
			for character in checksum:
				if character not in hexadecimal_characters:
					is_valid = False
		
		return(is_valid)
	
	
	##################################################################
	
	def authorizeClient(self, data):
	
		'''The client must initiate an authorization request
and the server must authorize the client before the
server will start transmitting any headset data.'''
		
		is_authorized = self.validateChecksum(data['appKey'])
		
		# A human-readable name identifying the client
		# application. This can be a maximum of 255 characters.
		
		if len(data['appName']) > 255:
			is_authorized = False
		
		
		return(is_authorized)
	
	
	##################################################################
	
	def calculateWavePoint(self, x, max_height=100, wave_length=10):
		
		# start at 0, increase to max value at half of one
		# wavelength, decrease to 0 by end of wavelength
		y = ( (max_height/2) * \
		      math.sin ((x-1) * ( math.pi / (wave_length / 2)))) + \
		      (max_height/2)
		
		# start at max value, decrease to 0 at half of one
		# wavelegnth, increase to max by end of wavelength
		#y = ( (max_height/2) * \
		      #math.cos (x * ( math.pi / (wave_length / 2)))) + \
		      #(max_height/2)
		
		
		return(y)
	
	
	##################################################################
	
	def simulateHeadsetData(self):
		
		response = DEFAULT_PACKET
		
		response['timestamp'] = time.time()
		
		time_value = self.connection_timestamp - time.time()
		
		for key in response.keys():
			
			if key == 'poorSignalLevel':
				pass
			
			elif key == 'eSense':
				
				plot_attention = self.calculateWavePoint( \
					time_value, \
					max_height=100, \
					wave_length=DEFAULT_SAMPLE_WAVELENGTH)
				
				plot_meditation = self.calculateWavePoint( \
					time_value + THINKGEAR_MEDITATION_PLOT_OFFSET, \
					max_height=100, \
					wave_length=DEFAULT_SAMPLE_WAVELENGTH)
				
				for each in response[key].keys():
					
					if ((each == 'attention') and \
						 (THINKGEAR_ATTENTION_MULTIPLIER != None)):
						value = plot_attention * \
						   THINKGEAR_ATTENTION_MULTIPLIER
					
					elif ((each == 'meditation') and \
						   (THINKGEAR_MEDITATION_MULTIPLIER != None)):
						value = plot_meditation * \
						   THINKGEAR_MEDITATION_MULTIPLIER
					
					
					value = int(value)
					
					
					if value < 0:
						value = 0
					elif value > 100:
						value = 100
					
					response[key][each] = value
			
			
			elif key == 'eegPower':
				plot = self.calculateWavePoint( \
					time_value, \
					max_height=65535, \
					wave_length=DEFAULT_SAMPLE_WAVELENGTH)
				
				for each in response[key].keys():
					if ((THINKGEAR_EEG_POWER_MULTIPLIERS != None) and \
						 (each in THINKGEAR_EEG_POWER_MULTIPLIERS.keys())):
						value = int(THINKGEAR_EEG_POWER_MULTIPLIERS[each] * plot)
					else:
						value = plot
					response[key][each] = value
		
		
		return(response)
	
	
	##################################################################
	
	def processPacketThinkGear(self, packet):
		
		if self.DEBUG > 2:
			print packet
		
		if (packet != {}):
			self.packet_queue.append(packet)
			
			
			if configuration.ENABLE_CLOUDBRAIN:
				#self.processPacketCloudbrain(packet)
				#self.cloudbrain_publisher.processPacketCloudbrain(packet)
				self.cloudbrain_publisher.appendPacket(packet)
			
			if COMMUNICATION_MODE == 'Emit Signal':
				self.emitSendPacketSignal()
			
			else:
				self.sendPacketQueue()
				
				if (self.parent != None):
					#self.parent.processPacketThinkGear(packet)
					self.parent.processPacketEEG(packet)
			
			
			#if configuration.ENABLE_CLOUDBRAIN:
				#self.processPacketCloudbrain(packet)
	
	
	##################################################################
	
	def updateStatus(self):
		
		# Craft a simulated data packet
		packet = self.simulateHeadsetData()
		
		self.packet_queue.append(packet)
		
		self.incrementPacketCount()
		
		
		# Include simulated blinks at desired frequency
		if ((self.blink_frequency_timer != None) and \
				(self.blink_frequency_timer > 0) and \
				(time.time() - self.blink_timestamp > \
				self.blink_frequency_timer)):
			
			self.blink_timestamp = time.time()
			
			packet = DEFAULT_BLINK_MESSAGE
			
			packet['timestamp'] = self.blink_timestamp
			
			self.packet_queue.append(packet)
			
			self.incrementPacketCount()
	
	
	##################################################################
	
	#def updateSessionStartTime(self, session_start_timestamp):
		
		#if self.parent != None:
			#self.parent.updateSessionStartTime(session_start_timestamp)

	
	##################################################################
	
	def resetDevice(self):
		
		if self.serial_device != None:
			self.serial_device.exitThread()
		
		if self.protocol != None:
			self.protocol.exitThread()
		
		if self.cloudbrain_publisher != None:
			self.cloudbrain_publisher.exitThread()
		
		self.configureEEG()
	
	
	##################################################################
	
	def processPacketForExport(self, packet={}, output={}):
		
		#print "INFO: [Synapse:ThinkGear:Server] processPacketForExport:",
		#print packet
		
		if 'blinkStrength' in packet.keys():
			# Skip any blink packets from log
			#continue
			return(output)
		
		#output['Attention'] = ''
		#output['Meditation'] = ''
		#output['Signal Level'] = ''
		#output['Delta'] = ''
		#output['Theta'] = ''
		#output['Low Alpha'] = ''
		#output['High Alpha'] = ''
		#output['Low Beta'] = ''
		#output['High Beta'] = ''
		#output['Low Gamma'] = ''
		#output['Mid Gamma'] = ''
		
		for header in self.customDataHeaders:
			if header not in output.keys():
				output[header] = ''
		
		if 'eSense' in packet.keys():
			if 'attention' in packet['eSense'].keys():
				output['Attention'] = packet['eSense']['attention']
			if 'meditation' in packet['eSense'].keys():
				output['Meditation'] = packet['eSense']['meditation']
		
		if 'poorSignalLevel' in packet.keys():
			output['Signal Level'] = packet['poorSignalLevel']
		
		if 'eegPower' in packet.keys():
			if 'delta' in packet['eegPower'].keys():
				output['Delta'] = packet['eegPower']['delta']
			if 'theta' in packet['eegPower'].keys():
				output['Theta'] = packet['eegPower']['theta']
			if 'lowAlpha' in packet['eegPower'].keys():
				output['Low Alpha'] = packet['eegPower']['lowAlpha']
			if 'highAlpha' in packet['eegPower'].keys():
				output['High Alpha'] = packet['eegPower']['highAlpha']
			if 'lowBeta' in packet['eegPower'].keys():
				output['Low Beta'] = packet['eegPower']['lowBeta']
			if 'highBeta' in packet['eegPower'].keys():
				output['High Beta'] = packet['eegPower']['highBeta']
			if 'lowGamma' in packet['eegPower'].keys():
				output['Low Gamma'] = packet['eegPower']['lowGamma']
			if 'highGamma' in packet['eegPower'].keys():
				output['Mid Gamma'] = packet['eegPower']['highGamma']
		
		
		return(output)
	
	
	##################################################################
	
	def setPacketCount(self, value):
		
		if self.parent != None:
			self.parent.setPacketCount(value)
	
	
	##################################################################
	
	def setBadPackets(self, value):
		
		if self.parent != None:
			self.parent.setBadPackets(value)
	
	
	##################################################################
	
	def incrementPacketCount(self):
		
		if self.parent != None:
			self.parent.incrementPacketCount()
	
	
	##################################################################
	
	def incrementBadPackets(self):
		
		if self.parent != None:
			self.parent.incrementBadPackets()
	
	
	##################################################################
	
	def resetSessionStartTime(self):
		
		if self.parent != None:
			self.parent.resetSessionStartTime()
	
	
	##################################################################
	
	#def run(self):
		
		#if self.DEBUG:
			#print "<---- [%s] Main thread running" % self.name
		
		#self.exec_()
	
	
	##################################################################
	
	def exitThread(self, callThreadQuit=True):
		
		if (self.emulate_headset_data):
			try:
				self.emulationTimer.stop()
			except Exception, e:
				if self.DEBUG:
					print "ERROR: Exception when stopping emulation timer:",
					print e
		
		# Calling exitThread() on protocol first seems to occassionally 
		# create the following error:
		# RuntimeError: Internal C++ object (PySide.QtNetwork.QTcpSocket) already deleted.
		# Segmentation fault
		# ...when program is closed without pressing "Stop" button for EEG
		#if self.protocol != None:
			#self.protocol.exitThread()
		
		# Call disconnect block in protocol first due to above error
		self.protocol.disconnectHardware()
		
		if self.serial_device != None:
			self.serial_device.exitThread()
		
		if self.protocol != None:
			self.protocol.exitThread()
		
		if self.cloudbrain_publisher != None:
			self.cloudbrain_publisher.exitThread()
		
		self.socket.close()
		
		if callThreadQuit:
			QtCore.QThread.quit(self)
			#self.join() # threading module
		
		if self.parent == None:
			sys.exit()
	
	
	##################################################################
	
	#def stop(self):
		
		#self.exitThread()
 