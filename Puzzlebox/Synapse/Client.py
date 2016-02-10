# -*- coding: utf-8 -*-

# Copyright Puzzlebox Productions, LLC (2010-2012)
#
# This code is released under the GNU Pulic License (GPL) version 2
# For more information please refer to http://www.gnu.org/copyleft/gpl.html

__changelog__ = """\
Last Update: 2012.05.06
"""

import os, sys,time
#import signal
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
		print "INFO: [Synapse:Client] Using PySide module"

if not configuration.ENABLE_PYSIDE:
	print "INFO: [Synapse:Client] Using PyQt4 module"
	from PyQt4 import QtCore, QtGui, QtNetwork


#####################################################################
# Globals
#####################################################################

DEBUG = configuration.DEBUG

SERVER_HOST = configuration.SYNAPSE_SERVER_HOST
SERVER_PORT = configuration.SYNAPSE_SERVER_PORT

CLIENT_NO_REPLY_WAIT = configuration.CLIENT_NO_REPLY_WAIT * 1000

DELIMITER = configuration.SYNAPSE_DELIMITER

THINKGEAR_CONFIGURATION_PARAMETERS = configuration.THINKGEAR_CONFIGURATION_PARAMETERS

ENABLE_THINKGEAR_AUTHORIZATION = configuration.ENABLE_THINKGEAR_AUTHORIZATION
AUTHORIZATION_REQUEST = configuration.THINKGEAR_AUTHORIZATION_REQUEST

#####################################################################
# Classes
#####################################################################

class puzzlebox_synapse_client(QtCore.QThread):
	
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
		
		self.is_authorized = True
		
		self.configureNetwork()
	
	
	##################################################################
	
	def configureNetwork(self):
	
		#self.blockSize = 0
		self.socket = QtNetwork.QTcpSocket()
		self.socket.name = 'Synapse:Client'
		
		if self.server_host == '*':
			self.server_host = '127.0.0.1'
		
		self.server_host=QtNetwork.QHostAddress(self.server_host)
		
		self.socket.readyRead.connect(self.printReply)
		self.socket.error.connect(self.displayError)
		
		# Perform ThinkGear authorization if enabled
		if ENABLE_THINKGEAR_AUTHORIZATION:
			self.sendCommand(AUTHORIZATION_REQUEST)
			self.socket.waitForReadyRead()
			self.socket.disconnectFromHost()
		
		self.sendCommand(THINKGEAR_CONFIGURATION_PARAMETERS)
	
	
	##################################################################
	
	def printReply(self):
		
		socket_buffer = self.socket.readAll()
		
		for packet in socket_buffer.split(DELIMITER):
			
			if packet != '':
				
				try:
					
					data = json.loads(packet.data())
				
				
				except Exception, e:
					
					if self.DEBUG:
						print "ERROR [%s]: Exception parsing packet:" % self.socket.name,
						print packet.data()
						print "ERROR [%s]: Data packet" % self.socket.name,
						print e
					
					continue
				
				
				else:
					
					if self.DEBUG > 1:
						print "--> [%s] Received:" % self.socket.name,
						print data
					
					#self.processPacketThinkGear(data)
					self.processPacketEEG(data)
	
	
	##################################################################
	
	def displayError(self, socketError):
		
		if self.DEBUG:
			if ((socketError != QtNetwork.QAbstractSocket.RemoteHostClosedError) and \
				 (socketError != QtNetwork.QAbstractSocket.SocketTimeoutError)):
				print "ERROR [%s]:" % self.socket.name,
				print self.socket.errorString()
		
		
		if (self.parent != None):
		
			if ((socketError == QtNetwork.QAbstractSocket.RemoteHostClosedError) or \
				 (socketError != QtNetwork.QAbstractSocket.SocketTimeoutError)):
				pass
			
			elif socketError == QtNetwork.QAbstractSocket.HostNotFoundError:
				try:
					QtGui.QMessageBox.information(self.parent, \
					                              self.socket.name, \
					   "The server host was not found. Please check the host name and "
					   "port settings.")
				except:
					pass
				
				if self.DEBUG:
					print "The server host was not found. ",
					print "Please check the host name and ",
					print "port settings."

			
			elif socketError == QtNetwork.QAbstractSocket.ConnectionRefusedError:
				try:
					QtGui.QMessageBox.information(self.parent, \
					                           self.socket.name,
					   "The server connection was refused by the peer. Make sure the "
					   "server is running, and check that the host name "
					   "and port settings are correct.")
				except:
					pass
				
				if self.DEBUG:
					print "The server connection was refused by the peer. ",
					print "Make sure the ",
					print "server is running, and check that the host name ",
					print "and port settings are correct."

			
			else:
##				try:
##					QtGui.QMessageBox.information(self.parent, \
##					                           self.socket.name, \
##					   "The following error occurred: %s." % \
##					   self.socket.errorString())
##				except:
##					pass
				
				if self.DEBUG:
					print "The following error occurred: %s." % \
						self.socket.errorString()
	
	
	##################################################################
	
	def sendCommand(self, command):
		
		if self.DEBUG:
			print "<-- [%s] Sending:" % self.socket.name,
			print command
		
		self.socket.abort()
		self.socket.connectToHost(self.server_host, self.server_port)
		
		data = json.dumps(command)
		
		self.socket.waitForConnected(CLIENT_NO_REPLY_WAIT)
		
		self.socket.write(data)
		
		try:
			self.socket.waitForBytesWritten(CLIENT_NO_REPLY_WAIT)
		except Exception, e:
			print "ERROR [%s]: Exception:" % self.socket.name,
			print e
	
	
	##################################################################
	
	#def processPacketThinkGear(self, packet):
	def processPacketEEG(self, packet):
		
		# ThinkGear Connect server does not provide a timestamp in its JSON protocol
		if ('timestamp' not in packet.keys()):
			packet['timestamp'] = time.time()
		
		if ('isAuthorized' in packet.keys()):
			self.isAuthorized = packet['isAuthorized']
		
		# Pass GUI updating to Client Interface application
		if (self.parent != None):
			#self.parent.processPacketThinkGear(packet)
			self.parent.processPacketEEG(packet)
		
	
	##################################################################
	
	def disconnectFromHost(self):
		
		self.socket.disconnectFromHost()
	
	
	##################################################################
	
	def run(self):
		
		if self.DEBUG:
			print "<---- [%s] Main thread running" % self.socket.name
		
		self.exec_()
	
	
	##################################################################
	
	def stop(self):
		
		try:
			self.disconnectFromHost()
		except:
			pass
	
	
	##################################################################
	
	def exitThread(self, callThreadQuit=True):
		
		self.stop()
		
		if callThreadQuit:
			QtCore.QThread.quit(self)


#####################################################################
# Command line class
#####################################################################

class puzzlebox_synapse_client_console(puzzlebox_synapse_client):
	
	def __init__(self, log, \
		          command_parameters, \
		          server_host=SERVER_HOST, \
		          server_port=SERVER_PORT, \
		          DEBUG=DEBUG):
		
		self.log = log
		self.DEBUG = DEBUG
		self.parent = None
		
		self.command_parameters = command_parameters
		self.server_host = server_host
		self.server_port = server_port
		
		self.configureNetwork()
		
		self.execute_command_line()
	
	
	##################################################################
	
	def execute_command_line(self):
		
		(command) = self.parse_command_line(self.command_parameters)
		
		if (command != None):
		
			self.sendCommand(command)
			
			self.socket.waitForReadyRead(CLIENT_NO_REPLY_WAIT)
	
	
	##################################################################
	
	def parse_command_line(self, command_parameters):
		
		command = None
		
		for each in command_parameters:
			if each.startswith("--command="):
				command = each[ len("--command="): ]
		
		
		return(command)

