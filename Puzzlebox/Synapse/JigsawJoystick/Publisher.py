# -*- coding: utf-8 -*-

"""
Copyright Puzzlebox Productions, LLC (2016)

Ported from Puzzlebox Synapse
http://puzzlebox.io

This code is released under the GNU Lesser Public License (LGPL) version 3
For more information please refer to https://www.gnu.org/licenses/lgpl.html

Author: Steve Castellotti <sc@puzzlebox.io>
"""

__changelog__ = """
Last Update: 2016.05.14
"""

#####################################################################
# Imports
#####################################################################

import time
import socket

try:
	import Puzzlebox.Synapse.Configuration as configuration
except:

	class Configuration():
		
		def __init__(self):
			
			self.DEBUG = 1
			
			self.ENABLE_QT = False
			self.ENABLE_PYSIDE = False
			
			self.server_host = configuration.JIGSAW_HARDWARE_JOYSTICK_HOST
			self.server_port = configuration.JIGSAW_HARDWARE_JOYSTICK_PORT
	
	
	configuration = Configuration()


if configuration.ENABLE_QT:
	if configuration.ENABLE_PYSIDE:
		try:
			import PySide
			from PySide import QtCore
			Thread = PySide.QtCore.QThread
		except Exception, e:
			if configuration.DEBUG:
				print "ERROR: Exception importing PySide:",
				print e
			configuration.ENABLE_PYSIDE = False
		else:
			if configuration.DEBUG:
				print "INFO: [Synapse:JigsawJoystick:Publisher] Using PySide module"
	
	if not configuration.ENABLE_PYSIDE:
		try:
			if configuration.DEBUG:
				print "INFO: [Synapse:JigsawJoystick:Publisher] Using PyQt4 module"
			from PyQt4 import QtCore
		except:
			configuration.ENABLE_QT = False


if not configuration.ENABLE_QT:
	import threading
	Thread = threading.Thread
	if configuration.DEBUG:
		print "INFO: [Synapse:JigsawJoystick:Publisher] Using 'threading' module"


#####################################################################
# Classes
#####################################################################

class puzzlebox_synapse_jigsaw_joystick_publisher(Thread):

	def __init__(self, log, \
		          server_host=configuration.JIGSAW_HARDWARE_JOYSTICK_HOST,
		          server_port=configuration.JIGSAW_HARDWARE_JOYSTICK_PORT,
		          DEBUG=configuration.DEBUG, \
		          parent=None):
		
		try:
			QtCore.QThread.__init__(self, parent)
		except:
			Thread.__init__ (self)
		
		self.log = log
		self.DEBUG = DEBUG
		self.parent = parent


		self.keep_running = True
		self.packet_queue = []


		self.server_host=server_host
		self.server_port=server_port
		
		
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		
		self.sock.settimeout(10)
		self.sock.connect((server_host, server_port))
	
	
	##################################################################
	
	def appendPacket(self, packet):
		
		self.packet_queue.append(packet)
	
	
	##################################################################
	
	def processPacketJoystick(self, packet):
		
		#if 'poorSignalLevel' in packet.keys():
			
			#metric_packet = {}
			#metric_packet['timestamp'] = packet['timestamp']
			#metric_packet['channel_0'] = packet['poorSignalLevel']
			
			#self.publishers['poorSignalLevel'].publish(
				#self.routing_keys['poorSignalLevel'],
				#[metric_packet])
			
			#if self.displayPacketCSV:
				#if self.DEBUG > 1:
					#displayCSV(metric_packet)
			
			
		if 'eSense' in packet.keys():
			
			if 'attention' in packet['eSense'].keys():
				
				self.publish_control_packet(packet['eSense']['attention'])
			
			
			#if 'meditation' in packet['eSense'].keys():
				
				#self.publishers['meditation'].publish(
					#self.routing_keys['meditation'], [{
						#'timestamp': packet['timestamp'], \
						#'channel_0': packet['eSense']['meditation']
					#}] )
	
	
	##################################################################
	
	def publish_control_packet(self, value):
		
		if self.DEBUG > 1:
			print "--> publish_control_packet:",
			print value
		
		packet = '\x20' + int2bytes(value)
		
		self.sock.send(packet)


##################################################################

	def run(self):
		
		while self.keep_running:
		
			while self.packet_queue != []:
				
				packet = self.packet_queue.pop(0)
				
				self.processPacketJoystick(packet)
			
			
			time.sleep(0.002)
	
	
	##################################################################
	
	def exitThread(self, callThreadQuit=True):
		
		self.sock.close()
		
		self.keep_running = False
		
		if callThreadQuit:
			if configuration.ENABLE_QT:
				Thread.quit(self)
			else:
				self.join()


##################################################################
# Functions
##################################################################

def int2bytes(i):
	h = int2hex(i)
	return hex2bytes(h)

def int2hex(i):
	return hex(i)

def hex2int(h):
	if len(h) > 1 and h[0:2] == '0x':
		h = h[2:]
	if len(h) % 2:
		h = "0" + h
	return int(h, 16)

def hex2bytes(h):
	if len(h) > 1 and h[0:2] == '0x':
		h = h[2:]
	if len(h) % 2:
		h = "0" + h
	return h.decode('hex')

def byte2int(b):
	return int(b.encode('hex'), 16)

