# -*- coding: utf-8 -*-

# Copyright Puzzlebox Productions, LLC (2015)
#
# This code is released under the GNU Pulic License (GPL) version 2
# For more information please refer to http://www.gnu.org/copyleft/gpl.html

__changelog__ = """\
Last Update: 2015.01.17
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
		print "INFO: [Synapse:Muse:Client] Using PySide module"

if not configuration.ENABLE_PYSIDE:
	print "INFO: [Synapse:Muse:Client] Using PyQt4 module"
	from PyQt4 import QtCore, QtGui, QtNetwork

try:
	import Puzzlebox.Synapse.Muse.Protocol as muse_protocol
except Exception, e:
	print "ERROR: [Synapse:Muse:Client] Exception importing Muse.Protocol:",
	print e
	muse_protocol = None

#####################################################################
# Globals
#####################################################################

DEBUG = configuration.DEBUG

SERVER_HOST = configuration.MUSE_SERVER_HOST
SERVER_PORT = configuration.MUSE_SERVER_PORT

#EVENT_TIMER_BASED_LOOP = True
#EVENT_TIMER_FREQUENCY = 0.25 * 1000 # 4 Hz

#####################################################################
# Classes
#####################################################################

class puzzlebox_synapse_client_muse(QtCore.QThread):
	
	def __init__(self, log, \
		          server_host=SERVER_HOST, \
		          server_port=SERVER_PORT, \
		          DEBUG=DEBUG, \
		          parent=None):
		
		QtCore.QThread.__init__(self,parent)
		
		self.log = log
		self.DEBUG = DEBUG
		self.parent=parent
		
		#self.server_host = server_host
		#self.server_port = server_port
		self.server_host = '127.0.0.1'
		self.server_port = 5002
		
		self.packet_count = 0
		self.bad_packets = 0
		
		self.name = "Synapse:Muse:Client"
		
		self.protocol = None
		
		#self.configureNetwork()
		
		#if EVENT_TIMER_BASED_LOOP:
			#self.eventTimer = QtCore.QTimer()
			#QtCore.QObject.connect(self.eventTimer, \
				                    #QtCore.SIGNAL("timeout()"), \
				                    #self.processEvent)
			#self.eventTimer.start(EVENT_TIMER_FREQUENCY)
	
	
	##################################################################
	
	#def processEvent(self):
		
		#muse_protocol.start(host=self.server_host, port=self.server_port, initialized=True, parent=self)
		
	
	##################################################################
	
	def configureNetwork(self):
		
		print "INFO: [Synapse:Muse:Client] Connecting to %s:%i" % \
		   (self.server_host, self.server_port)
		
		if muse_protocol != None:
			
			#muse_protocol.start(self.log, host=self.server_host, \
			                      #port=self.server_port, \
			                      #DEBUG=self.DEBUG, \
			                      #parent=self)
									 
			##print dir(muse_protocol.puzzlebox_synapse_protocol_muse)
			
			##muse_protocol.puzzlebox_synapse_protocol_muse.start()
			
			##muse_protocol.puzzlebox_synapse_protocol_muse.start(host=self.server_host, \
			                      ##port=self.server_port, \
			                      ##DEBUG=self.DEBUG, \
			                      ##parent=self)
				##muse_protocol.puzzlebox_synapse_protocol_muse( \
											##port=self.server_port, \
											##DEBUG=self.DEBUG, \
											##parent=self)

			self.protocol = muse_protocol.puzzlebox_synapse_protocol_muse(\
				self.log, \
				host=self.server_host, \
			                      port=self.server_port, \
			                      DEBUG=self.DEBUG, \
			                      parent=self)
			
			##self.plugin_session = self.parent.plugin_session # for Jigsaw compatability
			
			self.protocol.start()
			#self.protocol.run()
			#self.protocol.run(self.protocol)
			
			##self.protocol.start(host=self.server_host, \
			                      ##port=self.server_port, \
			                      ##DEBUG=self.DEBUG, \
			                      ##parent=self)
	
	
	##################################################################
	
	def processPacketMuse(self, packet):
		
		self.packet_count = self.packet_count + 1
		
		#print self.packet_count,
		#print packet
		
		# Pass GUI updating to Interface application or parent object
		if (self.parent != None):
			self.parent.processPacketMuse(packet)
	
	
	##################################################################
	
	def run(self):
		
		if self.DEBUG:
			print "<---- [%s] Main thread running" % self.name
		
		self.configureNetwork()
		
		self.exec_()
	
	
	##################################################################
	
	def stop(self):
		
		if muse_protocol != None:
			#muse_protocol.KEEP_RUNNING = False
			muse_protocol.keep_running = False
			
			count = 1
			while muse_protocol.CONNECTED:
				time.sleep(0.10)
				count = count + 1
				if count >= 10:
					break
	
	
	##################################################################
	
	def exitThread(self, callThreadQuit=True):
		
		self.stop()
		
		if callThreadQuit:
			QtCore.QThread.quit(self)

	def setPacketCount(self, count):
		self.packet_count = count
	
	def setBadPackets(self, count):
		self.bad_packets = count
		
	def resetSessionStartTime(self):
		pass