# -*- coding: utf-8 -*-

# Copyright Puzzlebox Productions, LLC (2012)
#
# This code is released under the GNU Pulic License (GPL) version 2
# For more information please refer to http://www.gnu.org/copyleft/gpl.html

__changelog__ = """\
Last Update: 2012.04.05
"""

import time

import Puzzlebox.Synapse.Configuration as configuration

if configuration.ENABLE_PYSIDE:
	try:
		from PySide import QtCore, QtGui, QtNetwork
	except Exception, e:
		print "ERROR: Exception importing PySide:",
		print e
		configuration.ENABLE_PYSIDE = False
	else:
		print "INFO: [Synapse:Emotiv:Client] Using PySide module"

if not configuration.ENABLE_PYSIDE:
	print "INFO: [Synapse:Emotiv:Client] Using PyQt4 module"
	from PyQt4 import QtCore, QtGui, QtNetwork

try:
	import Puzzlebox.Synapse.Emotiv.Protocol as emotiv_protocol
except Exception, e:
	print "ERROR: [Synapse:Emotiv:Client] Exception importing Emotiv.Protocol:",
	print e
	emotiv_protocol = None

#####################################################################
# Globals
#####################################################################

DEBUG = configuration.DEBUG

SERVER_HOST = configuration.EMOTIV_SERVER_HOST
SERVER_PORT = configuration.EMOTIV_SERVER_PORT_CONTROL_PANEL
#SERVER_PORT = configuration.EMOTIV_SERVER_PORT_EMOCOMPOSER

#EVENT_TIMER_BASED_LOOP = True
#EVENT_TIMER_FREQUENCY = 0.25 * 1000 # 4 Hz

#####################################################################
# Classes
#####################################################################

class puzzlebox_synapse_client_emotiv(QtCore.QThread):
	
	def __init__(self, log, \
		          server_host=SERVER_HOST, \
		          server_port=SERVER_PORT, \
		          DEBUG=DEBUG, \
		          parent=None):
		
		QtCore.QThread.__init__(self,parent)
		
		self.log = log
		self.DEBUG = DEBUG
		self.parent=parent
		
		self.server_host = server_host
		self.server_port = server_port
		
		self.packet_count = 0
		self.bad_packets = 0
		
		self.name = "Synapse:Emotiv:Client"
		
		#self.configureNetwork()
		
		#if EVENT_TIMER_BASED_LOOP:
			#self.eventTimer = QtCore.QTimer()
			#QtCore.QObject.connect(self.eventTimer, \
				                    #QtCore.SIGNAL("timeout()"), \
				                    #self.processEvent)
			#self.eventTimer.start(EVENT_TIMER_FREQUENCY)
	
	
	##################################################################
	
	#def processEvent(self):
		
		#emotiv_protocol.start(host=self.server_host, port=self.server_port, initialized=True, parent=self)
		
	
	##################################################################
	
	def configureNetwork(self):
		
		print "INFO: [Synapse:Emotiv:Client] Connecting to %s:%i" % \
		   (self.server_host, self.server_port)
		
		if emotiv_protocol != None:
			
			emotiv_protocol.start(host=self.server_host, \
			                      port=self.server_port, \
			                      initialized=False, \
			                      parent=self)
	
	
	##################################################################
	
	def processPacketEmotiv(self, packet):
		
		self.packet_count = self.packet_count + 1
		
		# Pass GUI updating to Interface application or parent object
		if (self.parent != None):
			self.parent.processPacketEmotiv(packet)
	
	
	##################################################################
	
	def run(self):
		
		if self.DEBUG:
			print "<---- [%s] Main thread running" % self.name
		
		self.configureNetwork()
		
		self.exec_()
	
	
	##################################################################
	
	def stop(self):
		
		if emotiv_protocol != None:
			emotiv_protocol.KEEP_RUNNING = False
			
			count = 1
			while emotiv_protocol.CONNECTED:
				time.sleep(0.10)
				count = count + 1
				if count >= 10:
					break
	
	
	##################################################################
	
	def exitThread(self, callThreadQuit=True):
		
		self.stop()
		
		if callThreadQuit:
			QtCore.QThread.quit(self)

