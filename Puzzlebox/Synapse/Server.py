# -*- coding: utf-8 -*-

# Copyright Puzzlebox Productions, LLC (2010-2012)
#
# This code is released under the GNU Pulic License (GPL) version 2
# For more information please refer to http://www.gnu.org/copyleft/gpl.html

__changelog__ = """\
Last Update: 2012.03.30
"""

### IMPORTS ###

import os, sys, time

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
		print "INFO: [Synapse:Server] Using PySide module"

if not configuration.ENABLE_PYSIDE:
	print "INFO: [Synapse:Server] Using PyQt4 module"
	from PyQt4 import QtCore, QtGui, QtNetwork


#####################################################################
# Globals
#####################################################################

DEBUG = configuration.DEBUG

COMMUNICATION_MODE = 'Emit Signal'
#COMMUNICATION_MODE = 'Call Parent'

SERVER_INTERFACE = configuration.SYNAPSE_SERVER_INTERFACE
SERVER_PORT = configuration.SYNAPSE_SERVER_PORT
DEFAULT_DEVICE_MODEL = 'NeuroSky MindWave'
THINKGEAR_DEVICE_SERIAL_PORT = configuration.THINKGEAR_DEVICE_SERIAL_PORT

CLIENT_NO_REPLY_WAIT = configuration.CLIENT_NO_REPLY_WAIT * 1000

FLASH_POLICY_FILE_REQUEST = configuration.FLASH_POLICY_FILE_REQUEST
FLASH_SOCKET_POLICY_FILE = configuration.FLASH_SOCKET_POLICY_FILE

DELIMITER = configuration.SYNAPSE_DELIMITER

MESSAGE_FREQUENCY_TIMER = 1 * 1000 # 1 Hz (1000 ms)

ENABLE_SIMULATE_HEADSET_DATA = configuration.THINKGEAR_ENABLE_SIMULATE_HEADSET_DATA

DEFAULT_PACKET = {}
DEFAULT_RESPONSE_MESSAGE = DEFAULT_PACKET

#####################################################################
# Classes
#####################################################################

class puzzlebox_synapse_server(QtCore.QThread):
	
	def __init__(self, log, \
		          server_interface=SERVER_INTERFACE, \
		          server_port=SERVER_PORT, \
		          device_model=DEFAULT_DEVICE_MODEL, \
		          device_address=THINKGEAR_DEVICE_SERIAL_PORT, \
		          emulate_headset_data=ENABLE_SIMULATE_HEADSET_DATA, \
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
		
		self.connection_timestamp = time.time()
		self.session_start_timestamp = time.time()
		
		self.connections = []
		self.packet_queue = []
		
		self.connect(self, \
		             QtCore.SIGNAL("sendPacket()"), \
		             self.sendPacketQueue)
		
		
		self.configureNetwork()
	
	
	##################################################################
	
	def configureNetwork(self):
	
		#self.blockSize = 0
		self.socket = QtNetwork.QTcpServer()
		self.socket.name = 'Synapse:Server'
		
		if self.DEBUG:
			print "<---- [%s] Initializing server on %s:%i" % \
			   (self.socket.name, self.server_interface, self.server_port)
		
		
		if ((self.server_interface == '') or \
			 (self.server_interface == '*')):
			address=QtNetwork.QHostAddress.Any
		else:
			#address=self.server_interface
			address=QtNetwork.QHostAddress(self.server_interface)
		
		
		result = self.socket.listen(address, self.server_port)
		
		
		if not result:
			try:
				QtGui.QMessageBox.information( \
				self.parent, \
				self.socket.name, \
				"Unable to start the server on %s:%i" % \
				(self.server_interface, self.server_port))
			except:
				pass
			
			if self.DEBUG:
				print "ERROR [%s] Unable to start the server:" % self.socket.name,
				print self.socket.errorString()
			
			self.socket.close()
			return
		
		
		self.socket.newConnection.connect(self.processConnection)
		#self.socket.error.connect(self.displayError)
	
	
	##################################################################
	
	def deleteDisconnected(self):
		
		connection_index = 0
		
		for connection in self.connections:
			
			try:
			
				if ((connection.state() != QtNetwork.QAbstractSocket.ConnectingState) and \
					(connection.state() != QtNetwork.QAbstractSocket.ConnectedState)):
					
					if self.DEBUG:
						print "- - [%s] Deleting disconnected socket" % self.socket.name
					
					connection.deleteLater()
					# Delete references to disconnected sockets
					del (self.connections[connection_index])
			
			except:
				# Delete references to sockets throwing exceptions
				del (self.connections[connection_index])
			
			connection_index += 1
	
	
	##################################################################
	
	def processConnection(self):
		
		clientConnection = self.socket.nextPendingConnection()
		clientConnection.disconnected.connect(self.deleteDisconnected)
		
		self.connections.append(clientConnection)
		
		self.clientConnection = clientConnection
		
		# the next connected client to enter the readyRead state
		# will be processed first
		clientConnection.readyRead.connect(self.processClientConnection)
	
	
	##################################################################
	
	def processClientConnection(self):
		
		clientConnection = self.clientConnection
		
		socket_buffer = clientConnection.readAll()
		
		for packet in socket_buffer.split(DELIMITER):
			
			data_to_process = None
			
			if packet != '':
				
				try:
					data_to_process = json.loads(packet.data())
				
				except Exception, e:
					
					# Special socket handling for Flash applications
					if (packet == FLASH_POLICY_FILE_REQUEST):
						
						if self.DEBUG:
							print "--> [%s] Flash policy file requested" % self.socket.name
						
						data_to_process = packet.data()
					
					
					else:
						
						if self.DEBUG:
							print "--> [%s] Partial data received (or error:" % self.socket.name,
							print e
							print ")."
							
							print "packet data:",
							print packet.data()
				
				
				else:
					
					if self.DEBUG:
						print "--> [%s] Received:" % self.socket.name,
						print data_to_process
				
				
				if (data_to_process != None):
					
					response = self.processData(data_to_process)
					
					if (response != None):
						
						self.sendResponse(clientConnection, response)
	
	
	##################################################################
	
	def sendResponse(self, connection, response, disconnect_after_sending=False):
		
		# Special socket handling for Flash applications
		if (response == FLASH_SOCKET_POLICY_FILE):
			data = response
		else:
			data = json.dumps(response)
			data = data + DELIMITER
		
		if connection.waitForConnected(CLIENT_NO_REPLY_WAIT):
			
			if self.DEBUG > 1:
				print "<-- [%s] Sending:" % self.socket.name,
				print data
			
			connection.write(data)
			
			connection.waitForBytesWritten(CLIENT_NO_REPLY_WAIT)
			
			if disconnect_after_sending:
				connection.disconnectFromHost()
	
	
	##################################################################
	
	def emitSendPacketSignal(self):
		
		self.emit(QtCore.SIGNAL("sendPacket()"))
	
	
	##################################################################
	
	def sendPacketQueue(self):
		
		if self.connections != []:
			
			while (len(self.packet_queue) > 0):
				
				packet = self.packet_queue[0]
				del self.packet_queue[0]
				
				for connection in self.connections:
					
					if connection.state() == QtNetwork.QAbstractSocket.ConnectedState:
						
						self.sendResponse(connection, packet)
	
	
	##################################################################
	
	def processData(self, data):
		
		response = None
		
		# Special socket handling for Flash applications
		if (data == FLASH_POLICY_FILE_REQUEST):
			
			response = FLASH_SOCKET_POLICY_FILE
		
		
		return(response)
	
	
	##################################################################
	
	def updateSessionStartTime(self, session_start_timestamp):
		
		self.session_start_timestamp = session_start_timestamp
	
	
	##################################################################
	
	def run(self):
		
		if self.DEBUG:
			print "<---- [%s] Main thread running" % self.socket.name
		
		
		self.exec_()
	
	
	##################################################################
	
	def exitThread(self, callThreadQuit=True):
		
		
		for server in self.protocolServers:
			server.exitThread()
		
		self.socket.close()
		
		if callThreadQuit:
			QtCore.QThread.quit(self)
		
		if self.parent == None:
			sys.exit()
	
	
	##################################################################
	
	def stop(self):
		
		self.exitThread()

