# -*- coding: utf-8 -*-

# Copyright Puzzlebox Productions, LLC (2010-2015)
#
# This code is released under the GNU Pulic License (GPL) version 2
# For more information please refer to http://www.gnu.org/copyleft/gpl.html

__changelog__ = """\
Last Update: 2015.01.17
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
		print "INFO: [Synapse:Muse:Server] Using PySide module"

if not configuration.ENABLE_PYSIDE:
	print "INFO: [Synapse:Muse:Server] Using PyQt4 module"
	from PyQt4 import QtCore, QtGui, QtNetwork

import Puzzlebox.Synapse.Server as synapse_server
import Puzzlebox.Synapse.ThinkGear.Server as thinkgear_server
import Puzzlebox.Synapse.Muse.Client as muse_client
try:
	import Puzzlebox.Synapse.Muse.Protocol as muse_protocol
except Exception, e:
	print "ERROR: [Synapse:Muse:Server] Exception importing Muse.Protocol:",
	print e
	muse_protocol = None

#####################################################################
# Globals
#####################################################################

DEBUG = configuration.DEBUG

#COMMUNICATION_MODE = 'Emit Signal'
COMMUNICATION_MODE = 'Call Parent'

SERVER_INTERFACE = configuration.MUSE_SERVER_HOST
SERVER_PORT = configuration.MUSE_SERVER_PORT

DEFAULT_DEVICE_MODEL = 'InterAxon Muse'

EMULATE_THINKGEAR_FOR_MUSE = configuration.EMULATE_THINKGEAR_FOR_MUSE

CLIENT_NO_REPLY_WAIT = configuration.CLIENT_NO_REPLY_WAIT * 1000

FLASH_POLICY_FILE_REQUEST = configuration.FLASH_POLICY_FILE_REQUEST
FLASH_SOCKET_POLICY_FILE = configuration.FLASH_SOCKET_POLICY_FILE

DELIMITER = configuration.SYNAPSE_DELIMITER

MESSAGE_FREQUENCY_TIMER = 1 * 1000 # 1 Hz (1000 ms)

ENABLE_SIMULATE_HEADSET_DATA = configuration.THINKGEAR_ENABLE_SIMULATE_HEADSET_DATA

DEFAULT_AUTHORIZATION_MESSAGE = \
	{"isAuthorized": True}
		# Tells the client whether the server has authorized
		# access to the user's headset data. The value is
		# either true or false.

DEFAULT_PACKET = {}

#DEFAULT_RESPONSE_MESSAGE = DEFAULT_SIGNAL_LEVEL_MESSAGE
DEFAULT_RESPONSE_MESSAGE = DEFAULT_PACKET

#####################################################################
# Classes
#####################################################################

class puzzlebox_synapse_server_muse(thinkgear_server.puzzlebox_synapse_server_thinkgear):
	
	def __init__(self, log, \
		          server_interface=SERVER_INTERFACE, \
		          server_port=SERVER_PORT, \
		          device_model=None, \
		          device_address=SERVER_PORT, \
		          emulate_headset_data=ENABLE_SIMULATE_HEADSET_DATA, \
		          emulate_thinkgear=EMULATE_THINKGEAR_FOR_MUSE, \
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
		
		self.name = 'Synapse:Muse:Server'
		
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
		
		
		self.customDataHeaders = ['Concentration', \
		                          'Mellow', \
		                         ]
		
		
		self.configureEEG()
		
		self.configureNetwork()
	
	
	##################################################################
	
	def configureEEG(self):
		
		if self.server_interface == '*':
			self.server_interface = '127.0.0.1'
		
		if muse_protocol != None:
		
			# We call Muse.Client as Muse.Protocol in order
			# to run in a separate from Muse.Server
			#self.museClient = \
			self.protocol = \
			   muse_client.puzzlebox_synapse_client_muse( \
			      log=self.log, \
			      server_host=self.server_interface, \
			      server_port=self.device_address, \
			      DEBUG=DEBUG, \
			      parent=self)
			
			#self.museClient.start()
			self.protocol.start()
		
		
			#muse_protocol.start(host=self.server_interface, \
			                      #port=self.server_port, \
			                      #initialized=False, \
			                      #parent=self)
	
	
	##################################################################
	
	def processPacketMuse(self, packet):
		
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
					#self.parent.processPacketMuse(packet)
					self.parent.processPacketEEG(packet)
	
	
	##################################################################
	
	def emulateThinkGear(self, packet):
		
		#if ('museStatus' in packet.keys()):
			
			#if ('contactNumberOfQualityChannels' in packet['museStatus']):
				
				##poorSignalLevel = packet['museStatus']['wireless']
				#packet['poorSignalLevel'] = \
				   #(packet['museStatus']['contactNumberOfQualityChannels'] / 18.0) * 200
				#packet['poorSignalLevel'] = 200 - int(packet['poorSignalLevel'])
		
		
		#if ('expressiv' in packet.keys()):
			
			#if self.DEBUG > 2:
				#print "INFO [Synapse:Muse:Server] packet['expressiv']['currentAction']",
				#print packet['expressiv']['currentAction']
			
			#if ('currentAction' in packet['expressiv'].keys()):
				#if (packet['expressiv']['currentAction'] == 0x0002):
					#packet['blinkStrength'] = 255
		
		
		if ('concentration' in packet.keys()):
			
			packet['eSense'] = {}
			packet['eSense']['attention'] = packet['concentration']
			
		if ('relaxation' in packet.keys()):
			
			packet['eSense'] = {}
			packet['eSense']['meditation'] = packet['relaxation']
			
			
			#if ('concentration' in packe.keys()):
				##packet['eSense']['attention'] = int(packet['affectiv']['excitement'] * 100)
				#packet['eSense']['attention'] = int(packet['cognitiv']['currentActionPower'] * 100)
			#elif ('engagementBoredom' in packet['affectiv'].keys()):
				#packet['eSense']['attention'] = int(packet['affectiv']['engagementBoredom'] * 100)
			
			#if ('meditation' in packet['affectiv'].keys()):
				#packet['eSense']['meditation'] = int(packet['affectiv']['meditation'] * 100)
		
		
		return(packet)
	
	
	##################################################################
	
	def resetDevice(self):
		
		#if self.serial_device != None:
			#self.serial_device.exitThread()
		
		if self.protocol != None:
			#self.protocol.exitThread()
			self.stopMuseProtocol()
		
		self.configureEEG()
	
	
	##################################################################
	
	def processPacketForExport(self, packet={}, output={}):
		
		for header in self.customDataHeaders:
			output[header] = ''
		
		
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
				csv[timestamp]['timestamp'] = timestamp
				
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
			
			
			if 'museStatus' in packet.keys():
				if 'timeFromStart' in packet['museStatus'].keys():
					csv[timestamp]['Time From Start'] = packet['museStatus']['timeFromStart']
				if 'headsetOn' in packet['museStatus'].keys():
					csv[timestamp]['Headset On'] = packet['museStatus']['headsetOn']
				if 'Contact Number Of Quality Channels' in packet['museStatus'].keys():
					csv[timestamp]['Contact Number Of Quality Channels'] = packet['museStatus']['contactNumberOfQualityChannels']
				if 'Wireless' in packet['museStatus'].keys():
					csv[timestamp]['Wireless'] = packet['museStatus']['wireless']
			
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
		
		
		self.stopMuseProtocol()
		
		
		self.socket.close()
		
		if callThreadQuit:
			QtCore.QThread.quit(self)
		
		if self.parent == None:
			sys.exit()
	
	
	##################################################################
	
	def stopMuseProtocol(self):
		
		if muse_protocol != None:
			#muse_protocol.KEEP_RUNNING = False
			muse_protocol.keep_running = False
			
			print "muse_protocol:",
			print dir(muse_protocol)
			
			
			if 'CONNECTED' in dir(muse_protocol):
			
				count = 1
				while muse_protocol.CONNECTED:
					time.sleep(0.10)
					count = count + 1
					if count >= 10:
						break

