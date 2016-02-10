# -*- coding: utf-8 -*-

# Copyright Puzzlebox Productions, LLC (2010-2012)
#
# This code is released under the GNU Pulic License (GPL) version 2
# For more information please refer to http://www.gnu.org/copyleft/gpl.html

__changelog__ = """\
Last Update: 2012.05.11
"""

### IMPORTS ###

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
		print "INFO: [Synapse:Emotiv:Server] Using PySide module"

if not configuration.ENABLE_PYSIDE:
	print "INFO: [Synapse:Emotiv:Server] Using PyQt4 module"
	from PyQt4 import QtCore, QtGui, QtNetwork

import Puzzlebox.Synapse.Server as synapse_server
import Puzzlebox.Synapse.ThinkGear.Server as thinkgear_server
import Puzzlebox.Synapse.Emotiv.Client as emotiv_client
try:
	import Puzzlebox.Synapse.Emotiv.Protocol as emotiv_protocol
except Exception, e:
	print "ERROR: [Synapse:Emotiv:Server] Exception importing Emotiv.Protocol:",
	print e
	emotiv_protocol = None

#####################################################################
# Globals
#####################################################################

DEBUG = configuration.DEBUG

COMMUNICATION_MODE = 'Emit Signal'
#COMMUNICATION_MODE = 'Call Parent'

SERVER_INTERFACE = configuration.EMOTIV_SERVER_HOST
SERVER_PORT = configuration.EMOTIV_SERVER_PORT_CONTROL_PANEL
#SERVER_PORT = configuration.EMOTIV_SERVER_PORT_EMOCOMPOSER
DEFAULT_DEVICE_MODEL = 'Emotiv EPOC'
#THINKGEAR_DEVICE_SERIAL_PORT = configuration.THINKGEAR_DEVICE_SERIAL_PORT

EMULATE_THINKGEAR_FOR_EMOTIV = configuration.EMULATE_THINKGEAR_FOR_EMOTIV

CLIENT_NO_REPLY_WAIT = configuration.CLIENT_NO_REPLY_WAIT * 1000

FLASH_POLICY_FILE_REQUEST = configuration.FLASH_POLICY_FILE_REQUEST
FLASH_SOCKET_POLICY_FILE = configuration.FLASH_SOCKET_POLICY_FILE

DELIMITER = configuration.SYNAPSE_DELIMITER

MESSAGE_FREQUENCY_TIMER = 1 * 1000 # 1 Hz (1000 ms)

ENABLE_SIMULATE_HEADSET_DATA = configuration.THINKGEAR_ENABLE_SIMULATE_HEADSET_DATA

#BLINK_FREQUENCY_TIMER = configuration.THINKGEAR_BLINK_FREQUENCY_TIMER

#DEFAULT_SAMPLE_WAVELENGTH = configuration.THINKGEAR_DEFAULT_SAMPLE_WAVELENGTH

#THINKGEAR_ATTENTION_MULTIPLIER = configuration.THINKGEAR_ATTENTION_MULTIPLIER
#THINKGEAR_MEDITATION_MULTIPLIER = configuration.THINKGEAR_MEDITATION_MULTIPLIER

#THINKGEAR_EEG_POWER_MULTIPLIERS = configuration.THINKGEAR_EEG_POWER_MULTIPLIERS

DEFAULT_AUTHORIZATION_MESSAGE = \
	{"isAuthorized": True}
		# Tells the client whether the server has authorized
		# access to the user's headset data. The value is
		# either true or false.

#DEFAULT_SIGNAL_LEVEL_MESSAGE = \
	#{"poorSignalLevel": 0}
		## A quantifier of the quality of the brainwave signal.
		## This is an integer value that is generally in the
		## range of 0 to 200, with 0 indicating a
		## good signal and 200 indicating an off-head state.

#DEFAULT_EEG_POWER_MESSAGE = \
	#{"eegPower": { \
		#'delta': 0, \
		#'theta': 0, \
		#'lowAlpha': 0, \
		#'highAlpha': 0, \
		#'lowBeta': 0, \
		#'highBeta': 0, \
		#'lowGamma': 0, \
		#'highGamma': 0, \
		#}, \
	#} # A container for the EEG powers. These may
	  ## be either integer or floating-point values.
	  ## Maximum values are undocumented but assumed to be 65535

#DEFAULT_ESENSE_MESSAGE = \
	#{"eSense": { \
		#'attention': 0, \
		#'meditation': 0, \
		#}, \
	#} # A container for the eSense™ attributes.
	  ## These are integer values between 0 and 100,
	  ## where 0 is perceived as a lack of that attribute
	  ## and 100 is an excess of that attribute.

DEFAULT_BLINK_MESSAGE = {"blinkStrength": 255}
	# The strength of a detected blink. This is
	# an integer in the range of 0-255.

#DEFAULT_RAWEEG_MESSAGE = {"rawEeg": 255}
	## The raw data reading off the forehead sensor.
	## This may be either an integer or a floating-point value.

DEFAULT_PACKET = {}
#DEFAULT_PACKET.update(DEFAULT_EEG_POWER_MESSAGE)
#DEFAULT_PACKET.update(DEFAULT_SIGNAL_LEVEL_MESSAGE)
#DEFAULT_PACKET.update(DEFAULT_ESENSE_MESSAGE)

#DEFAULT_RESPONSE_MESSAGE = DEFAULT_SIGNAL_LEVEL_MESSAGE
DEFAULT_RESPONSE_MESSAGE = DEFAULT_PACKET

#####################################################################
# Classes
#####################################################################

class puzzlebox_synapse_server_emotiv(thinkgear_server.puzzlebox_synapse_server_thinkgear):
	
	def __init__(self, log, \
		          server_interface=SERVER_INTERFACE, \
		          server_port=SERVER_PORT, \
		          device_model=None, \
		          device_address=SERVER_PORT, \
		          emulate_headset_data=ENABLE_SIMULATE_HEADSET_DATA, \
		          emulate_thinkgear=EMULATE_THINKGEAR_FOR_EMOTIV, \
		          DEBUG=DEBUG, \
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
		self.emulate_thinkgear = emulate_thinkgear
		
		self.name = 'Synapse:Emotiv:Server'
		
		self.connection_timestamp = time.time()
		self.session_start_timestamp = time.time()
		
		self.connections = []
		self.packet_queue = []
		
		#self.serial_device = None
		self.protocol = None
		
		self.connect(self, \
		             QtCore.SIGNAL("sendPacket()"), \
		             self.sendPacketQueue)
		
		self.message_frequency_timer = MESSAGE_FREQUENCY_TIMER
		#self.blink_frequency_timer = BLINK_FREQUENCY_TIMER
		#self.blink_timestamp = time.time()
		
		
		#self.customDataHeaders = 'Time From Start,Headset On,Contact Number Of Quality Channels,Wireless,Expressiv Action,Excitement,Long Term Excitement,Meditation,Frustration,Engagement/Boredom,Cognitiv Action,Cognitiv Action Power'
		self.customDataHeaders = ['Time From Start', \
		                          'Headset On', \
		                          'Contact Number Of Quality Channels', \
		                          'Wireless', \
		                          'Expressiv Action', \
		                          'Excitement', \
		                          'Long Term Excitement', \
		                          'Meditation', \
		                          'Frustration', \
		                          'Engagement/Boredom', \
		                          'Cognitiv Action', \
		                          'Cognitiv Action Power', \
		                         ]
		
		
		self.configureEEG()
		
		self.configureNetwork()
		
		
		#if (self.emulate_headset_data):
			#self.emulationTimer = QtCore.QTimer()
			#QtCore.QObject.connect(self.emulationTimer, \
				                    #QtCore.SIGNAL("timeout()"), \
				                    #self.emulationEvent)
			#self.emulationTimer.start(MESSAGE_FREQUENCY_TIMER)
	
	
	##################################################################
	
	def configureEEG(self):
		
		if self.server_interface == '*':
			self.server_interface = '127.0.0.1'
		
		if emotiv_protocol != None:
		
			# We call Emotiv.Client as Emotiv.Protocol in order
			# to run in a separate from Emotiv.Server
			#self.emotivClient = \
			self.protocol = \
			   emotiv_client.puzzlebox_synapse_client_emotiv( \
			      log=self.log, \
			      server_host=self.server_interface, \
			      server_port=self.device_address, \
			      DEBUG=DEBUG, \
			      parent=self)
			
			#self.emotivClient.start()
			self.protocol.start()
		
		
			#emotiv_protocol.start(host=self.server_interface, \
			                      #port=self.server_port, \
			                      #initialized=False, \
			                      #parent=self)
	
	
	##################################################################
	
	def processPacketEmotiv(self, packet):
		
		if self.DEBUG > 2:
			print packet
		
		
		if self.emulate_thinkgear:
			packet = self.emulateThinkGear(packet)
		
		
		if (packet != {}):
			self.packet_queue.append(packet)
			
			if COMMUNICATION_MODE == 'Emit Signal':
				self.emitSendPacketSignal()
			
			else:
				self.sendPacketQueue()
				
				if (self.parent != None):
					#self.parent.processPacketEmotiv(packet)
					self.parent.processPacketEEG(packet)
	
	
	##################################################################
	
	def emulateThinkGear(self, packet):
		
		if ('emotivStatus' in packet.keys()):
			
			if ('contactNumberOfQualityChannels' in packet['emotivStatus']):
				
				#poorSignalLevel = packet['emotivStatus']['wireless']
				packet['poorSignalLevel'] = \
				   (packet['emotivStatus']['contactNumberOfQualityChannels'] / 18.0) * 200
				packet['poorSignalLevel'] = 200 - int(packet['poorSignalLevel'])
		
		
		if ('expressiv' in packet.keys()):
			
			if self.DEBUG > 2:
				print "INFO [Synapse:Emotiv:Server] packet['expressiv']['currentAction']",
				print packet['expressiv']['currentAction']
			
			if ('currentAction' in packet['expressiv'].keys()):
				if (packet['expressiv']['currentAction'] == 0x0002):
					packet['blinkStrength'] = 255
		
		
		if ('affectiv' in packet.keys()):
			
			packet['eSense'] = {}
			
			if ('excitement' in packet['affectiv'].keys()):
				#packet['eSense']['attention'] = int(packet['affectiv']['excitement'] * 100)
				packet['eSense']['attention'] = int(packet['cognitiv']['currentActionPower'] * 100)
			elif ('engagementBoredom' in packet['affectiv'].keys()):
				packet['eSense']['attention'] = int(packet['affectiv']['engagementBoredom'] * 100)
			
			if ('meditation' in packet['affectiv'].keys()):
				packet['eSense']['meditation'] = int(packet['affectiv']['meditation'] * 100)
		
		
		return(packet)
	
	
	##################################################################
	
	def resetDevice(self):
		
		#if self.serial_device != None:
			#self.serial_device.exitThread()
		
		if self.protocol != None:
			#self.protocol.exitThread()
			self.stopEmotivProtocol()
		
		self.configureEEG()
	
	
	##################################################################
	
	def processPacketForExport(self, packet={}, output={}):
		
		#output['Time From Start'] = ''
		#output['Headset On'] = ''
		#output['Contact Number Of Quality Channels'] = ''
		#output['Wireless'] = ''
		#output['Expressiv Action'] = ''
		#output['Excitement'] = ''
		#output['Long Term Excitement'] = ''
		#output['Meditation'] = ''
		#output['Frustration'] = ''
		#output['Engagement/Boredom'] = ''
		#output['Cognitiv Action'] = ''
		#output['Cognitiv Action Power'] = ''
		
		for header in self.customDataHeaders:
			output[header] = ''
		
		if self.emulate_thinkgear:
			output['Attention'] = ''
			output['Meditation'] = ''
			output['Signal Level'] = ''
		
		
		if 'emotivStatus' in packet.keys():
			if 'timeFromStart' in packet['emotivStatus'].keys():
				output['Time From Start'] = packet['emotivStatus']['timeFromStart']
			if 'headsetOn' in packet['emotivStatus'].keys():
				output['Headset On'] = packet['emotivStatus']['headsetOn']
			if 'Contact Number Of Quality Channels' in packet['emotivStatus'].keys():
				output['Contact Number Of Quality Channels'] = packet['emotivStatus']['contactNumberOfQualityChannels']
			if 'Wireless' in packet['emotivStatus'].keys():
				output['Wireless'] = packet['emotivStatus']['wireless']
		
		if 'expressiv' in packet.keys():
			if 'currentAction' in packet['expressiv'].keys():
				value = packet['expressiv']['currentAction']
				if value == 32:
					output['Expressiv Action'] = ''
				else:
					output['Expressiv Action'] = packet['expressiv']['currentAction']
		
		if 'affectiv' in packet.keys():
			if 'excitement' in packet['affectiv'].keys():
				output['Excitement'] = int(packet['affectiv']['excitement'] * 100)
			if 'longTermExcitement' in packet['affectiv'].keys():
				output['Long Term Excitement'] = int(packet['affectiv']['longTermExcitement'] * 100)
			if 'meditation' in packet['affectiv'].keys():
				output['Meditation'] = int(packet['affectiv']['meditation'] * 100)
			if 'frustration' in packet['affectiv'].keys():
				output['Frustration'] = int(packet['affectiv']['frustration'] * 100)
			if 'engagementBoredom' in packet['affectiv'].keys():
				output['Engagement/Boredom'] = int(packet['affectiv']['engagementBoredom'] * 100)
		
		if 'cognitiv' in packet.keys():
			if 'currentAction' in packet['cognitiv'].keys():
				output['Cognitiv Action'] = packet['cognitiv']['currentAction']
			if 'currentActionPower' in packet['cognitiv'].keys():
				output['Cognitiv Action Power'] = int(packet['cognitiv']['currentActionPower'] * 100)
		
		
		if self.emulate_thinkgear:
			if 'eSense' in packet.keys():
				if 'attention' in packet['eSense'].keys():
					output['Attention'] = packet['eSense']['attention']
				if 'meditation' in packet['eSense'].keys():
					output['Meditation'] = packet['eSense']['meditation']
			
			if 'poorSignalLevel' in packet.keys():
				output['Signal Level'] = packet['poorSignalLevel']
		
		return(output)
	
	
	##################################################################
	
	def exportDataToCSV(self, parent=None, source=None, target=None):
		
		if parent == None:
			if self.parent == None:
				parent = self
			else:
				parent = self.parent
		
		if source == None:
			if self.parent == None:
				source = self
			else:
				source = self.parent
		
		if target == None:
			if self.parent == None:
				target = self
			else:
				target = self.parent
		
		try:
			truncate_csv_timezone = target.configuration.EXPORT_CSV_TRUNCATE_TIMEZONE
		except:
			truncate_csv_timezone = False
		
		try:
			scrub_data = target.configuration.EXPORT_CSV_SCRUB_DATA
		except:
			scrub_data = False
		
		
		headers = 'Date,Time'
		headers = headers + ','
		#headers = headers + 'Time From Start,Headset On,Contact Number Of Quality Channels,Wireless,Excitement,Long Term Excitement,Meditation,Frustration,Engagement/Boredom,Cognitiv Action,Cognitiv Action Power'
		headers = headers + 'Time From Start,Headset On,Contact Number Of Quality Channels,Wireless,Expressiv Action,Excitement,Long Term Excitement,Meditation,Frustration,Engagement/Boredom,Cognitiv Action,Cognitiv Action Power'
		
		if self.emulate_thinkgear:
			headers = headers + ','
			#headers = headers + 'Attention,Meditation,Signal Level,Delta,Theta,Low Alpha,High Alpha,Low Beta,High Beta,Low Gamma,Mid Gamma'
			headers = headers + 'Attention,Meditation,Signal Level'
		
		
		customDataHeaders = []
		for header in parent.customDataHeaders:
			customDataHeaders.append(header)
		for plugin in parent.activePlugins:
			for header in plugin.customDataHeaders:
				customDataHeaders.append(header)
		
		for each in customDataHeaders:
			headers = headers + ',%s' % each
		
		headers = headers + '\n'
		
		
		csv = {}
		
		for packet in source.packets['signals']:
			
			if 'rawEeg' in packet.keys():
				continue
			
			if packet['timestamp'] not in csv.keys():
				
				if 'blinkStrength' in packet.keys():
					# Skip any blink packets from log
					continue
				
				
				timestamp = packet['timestamp']
				(date, localtime) = source.parseTimeStamp(timestamp, \
				                    truncate_time_zone=truncate_csv_timezone)
				
				csv[timestamp] = {}
				csv[timestamp]['Date'] = date
				csv[timestamp]['Time'] = localtime
				
				csv[timestamp]['Time From Start'] = ''
				csv[timestamp]['Headset On'] = ''
				csv[timestamp]['Contact Number Of Quality Channels'] = ''
				csv[timestamp]['Wireless'] = ''
				csv[timestamp]['Expressiv Action'] = ''
				csv[timestamp]['Excitement'] = ''
				csv[timestamp]['Long Term Excitement'] = ''
				csv[timestamp]['Meditation'] = ''
				csv[timestamp]['Frustration'] = ''
				csv[timestamp]['Engagement/Boredom'] = ''
				csv[timestamp]['Cognitiv Action'] = ''
				csv[timestamp]['Cognitiv Action Power'] = ''
				
				if self.emulate_thinkgear:
					csv[timestamp]['Attention'] = ''
					csv[timestamp]['Meditation'] = ''
					csv[timestamp]['Signal Level'] = ''
				
				for header in customDataHeaders:
					csv[timestamp][header] = ''
			
			
			if 'emotivStatus' in packet.keys():
				if 'timeFromStart' in packet['emotivStatus'].keys():
					csv[timestamp]['Time From Start'] = packet['emotivStatus']['timeFromStart']
				if 'headsetOn' in packet['emotivStatus'].keys():
					csv[timestamp]['Headset On'] = packet['emotivStatus']['headsetOn']
				if 'Contact Number Of Quality Channels' in packet['emotivStatus'].keys():
					csv[timestamp]['Contact Number Of Quality Channels'] = packet['emotivStatus']['contactNumberOfQualityChannels']
				if 'Wireless' in packet['emotivStatus'].keys():
					csv[timestamp]['Wireless'] = packet['emotivStatus']['wireless']
			
			if 'expressiv' in packet.keys():
				if 'currentAction' in packet['expressiv'].keys():
					value = packet['expressiv']['currentAction']
					if value == 32:
						csv[timestamp]['Expressiv Action'] = ''
					else:
						csv[timestamp]['Expressiv Action'] = packet['expressiv']['currentAction']
			
			if 'affectiv' in packet.keys():
				if 'excitement' in packet['affectiv'].keys():
					csv[timestamp]['Excitement'] = int(packet['affectiv']['excitement'] * 100)
				if 'longTermExcitement' in packet['affectiv'].keys():
					csv[timestamp]['Long Term Excitement'] = int(packet['affectiv']['longTermExcitement'] * 100)
				if 'meditation' in packet['affectiv'].keys():
					csv[timestamp]['Meditation'] = int(packet['affectiv']['meditation'] * 100)
				if 'frustration' in packet['affectiv'].keys():
					csv[timestamp]['Frustration'] = int(packet['affectiv']['frustration'] * 100)
				if 'engagementBoredom' in packet['affectiv'].keys():
					csv[timestamp]['Engagement/Boredom'] = int(packet['affectiv']['engagementBoredom'] * 100)
			
			if 'cognitiv' in packet.keys():
				if 'currentAction' in packet['cognitiv'].keys():
					csv[timestamp]['Cognitiv Action'] = packet['cognitiv']['currentAction']
				if 'currentActionPower' in packet['cognitiv'].keys():
					csv[timestamp]['Cognitiv Action Power'] = int(packet['cognitiv']['currentActionPower'] * 100)
			
			
			if self.emulate_thinkgear:
				if 'eSense' in packet.keys():
					if 'attention' in packet['eSense'].keys():
						csv[timestamp]['Attention'] = packet['eSense']['attention']
					if 'meditation' in packet['eSense'].keys():
						csv[timestamp]['Meditation'] = packet['eSense']['meditation']
				
				if 'poorSignalLevel' in packet.keys():
					csv[timestamp]['Signal Level'] = packet['poorSignalLevel']
			
			for header in customDataHeaders:
				if 'custom' in packet.keys() and \
				   header in packet['custom'].keys():
					csv[timestamp][header] = packet['custom'][header]
		
		
		#if scrub_data:
			#csv = self.scrubData(csv, truncate_csv_timezone, source=source)
		
		
		output = headers
		
		csv_keys = csv.keys()
		csv_keys.sort()
		
		for key in csv_keys:
			
			row = '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s' % \
			      (csv[key]['Date'], \
			       csv[key]['Time'], \
			       csv[key]['Time From Start'], \
			       csv[key]['Headset On'], \
			       csv[key]['Contact Number Of Quality Channels'], \
			       csv[key]['Wireless'], \
			       csv[key]['Expressiv Action'], \
			       csv[key]['Excitement'], \
			       csv[key]['Long Term Excitement'], \
			       csv[key]['Meditation'], \
			       csv[key]['Frustration'], \
			       csv[key]['Engagement/Boredom'], \
			       csv[key]['Cognitiv Action'], \
			       csv[key]['Cognitiv Action Power'])
			
			if self.emulate_thinkgear:
				row = '%s,%s,%s,%s' % \
				   (row, \
				    csv[key]['Attention'], \
				    csv[key]['Meditation'], \
				    csv[key]['Signal Level'])
			
			for header in customDataHeaders:
				row = row + ',%s' % csv[key][header]
			
			row = row + '\n'
			
			output = output + row
		
		
		return(output)	
	
	
	##################################################################
	
	def exitThread(self, callThreadQuit=True):
		
		#if (self.emulate_headset_data):
			#try:
				#self.emulationTimer.stop()
			#except Exception, e:
				#if self.DEBUG:
					#print "ERROR: Exception when stopping emulation timer:",
					#print e
		
		
		self.stopEmotivProtocol()
		
		
		self.socket.close()
		
		if callThreadQuit:
			QtCore.QThread.quit(self)
		
		if self.parent == None:
			sys.exit()
	
	
	##################################################################
	
	def stopEmotivProtocol(self):
		
		if emotiv_protocol != None:
			emotiv_protocol.KEEP_RUNNING = False
			
			count = 1
			while emotiv_protocol.CONNECTED:
				time.sleep(0.10)
				count = count + 1
				if count >= 10:
					break

