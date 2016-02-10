# -*- coding: utf-8 -*-

# Copyright Puzzlebox Productions, LLC (2010-2012)
#
# This code is released under the GNU Pulic License (GPL) version 2
# For more information please refer to http://www.gnu.org/copyleft/gpl.html

__changelog__ = """\
Last Update: 2012.06.29
"""

__todo__ = """
- exporting data columns twice (attention through mid gamma"
- undesirable data in control panel's debug window:
	Timestamp: 2012-06-29 07:53:59.336689 PDT
	poorSignalLevel: 200
- update configuration.ini file with settings entered into interface
"""

### IMPORTS ###
import os, sys, time

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
		print "INFO: [Synapse:Interface] Using PySide module"

if not configuration.ENABLE_PYSIDE:
	print "INFO: [Synapse:Interface] Using PyQt4 module"
	from PyQt4 import QtCore, QtGui, QtNetwork


try:
	from Interface_Plot import *
	MATPLOTLIB_AVAILABLE = True
except Exception, e:
	print "ERROR: Exception importing Interface_Plot:",
	print e
	MATPLOTLIB_AVAILABLE = False


if (sys.platform == 'win32'):
	#import _winreg as winreg
	#import itertools
	#import re
	#import serial
	DEFAULT_IMAGE_PATH = 'images'
elif (sys.platform == 'darwin'):
	DEFAULT_IMAGE_PATH = 'images'
else:
	import bluetooth
	DEFAULT_IMAGE_PATH = '/usr/share/puzzlebox_synapse/images'


try:
	import cPickle as pickle
except:
	import pickle


from Interface_Design import Ui_Form as Design

import Puzzlebox.Synapse.Device as synapse_device
import Puzzlebox.Synapse.Session as synapse_session
import Puzzlebox.Synapse.Client as synapse_client
import Puzzlebox.Synapse.ThinkGear.Server as thinkgear_server
import Puzzlebox.Synapse.Emotiv.Server as emotiv_server


#####################################################################
# Globals
#####################################################################

DEBUG = configuration.DEBUG

SYNAPSE_SERVER_HOST = configuration.SYNAPSE_SERVER_HOST
SYNAPSE_SERVER_PORT = configuration.SYNAPSE_SERVER_PORT

EMULATE_THINKGEAR_FOR_EMOTIV = configuration.EMULATE_THINKGEAR_FOR_EMOTIV

#THINKGEAR_EEG_POWER_BAND_ORDER = configuration.THINKGEAR_EEG_POWER_BAND_ORDER

THINKGEAR_EMULATION_MAX_ESENSE_VALUE = \
	configuration.THINKGEAR_EMULATION_MAX_ESENSE_VALUE
THINKGEAR_EMULATION_MAX_EEG_POWER_VALUE = \
	configuration.THINKGEAR_EMULATION_MAX_EEG_POWER_VALUE

PATH_TO_HCITOOL = '/usr/bin/hcitool'

#UPDATE_INTERFACE_VIA_TIMER = True # Alternative is to establish a
                                  ## ThinkGear Connect client which
                                  ## updates the interface on demand
                                  ## as packets are received

UPDATE_INTERFACE_VIA_TIMER = False

#INTERFACE_UPDATE_FREQUENCY = (1 / 512) * 1000 # ms (512 Hz)
INTERFACE_UPDATE_FREQUENCY = 1000 # ms

INTERFACE_RAW_EEG_UPDATE_FREQUENCY = 512

PACKET_MINIMUM_TIME_DIFFERENCE_THRESHOLD = 0.75


#####################################################################
# Classes
#####################################################################

class puzzlebox_synapse_interface(synapse_device.puzzlebox_synapse_device, \
                                  synapse_session.puzzlebox_synapse_session, \
                                  Design):
	
	def __init__(self, log, \
	             DEBUG=DEBUG, \
	             parent=None, \
	             embedded_mode=False):
		
		self.log = log
		self.DEBUG = DEBUG
		self.parent=parent
		self.embedded_mode=embedded_mode
		
		if self.parent == None:
			QtGui.QWidget.__init__(self, parent)
			self.setupUi(self)
		
			self.configureSettings()
			self.connectWidgets()
		
		self.name = "Synapse:Interface"
		
		self.synapseServer = None
		self.synapseClient = None
		#self.thinkgearConnectClient = None
		#self.emotivClient = None
		
		self.session_start_timestamp = time.time()
		self.plugin_session = self # for compatability with Puzzlebox Jigsaw
		
		self.maxEEGPower = THINKGEAR_EMULATION_MAX_EEG_POWER_VALUE
		
		self.debug_console_buffer = ''
		
		self.packets = {}
		self.packets['rawEeg'] = []
		self.packets['signals'] = []
		
		self.customDataHeaders = []
		
		self.session_start_timestamp = time.time()
		self.packet_count = 0
		self.bad_packets = 0
		
		if UPDATE_INTERFACE_VIA_TIMER:
			self.updateInterfaceTimer = QtCore.QTimer()
			QtCore.QObject.connect(self.updateInterfaceTimer, \
				                    QtCore.SIGNAL("timeout()"), \
				                    self.updateInterface)
		
		
		
		self.activePlugins = [self]
	
	
	##################################################################
	
	def configureSettings(self):
		
		# Synapse Interface
		image_path = "puzzlebox.ico"
		if not os.path.exists(image_path):
			image_path = os.path.join(DEFAULT_IMAGE_PATH, image_path)
		
		if os.path.exists(image_path):
			icon = QtGui.QIcon()
			icon.addPixmap(QtGui.QPixmap(image_path), \
				            QtGui.QIcon.Normal, \
				            QtGui.QIcon.Off)
			self.setWindowIcon(icon)
		
		image_path = "puzzlebox_logo.png"
		if not os.path.exists(image_path):
			image_path = os.path.join(DEFAULT_IMAGE_PATH, image_path)
		if os.path.exists(image_path):
			self.labelPuzzleboxIcon.setPixmap(QtGui.QPixmap(image_path))
		
		
		if (sys.platform == 'win32'):
			self.homepath = os.path.join( \
			   os.environ['HOMEDRIVE'], \
			   os.environ['HOMEPATH'], \
			   'Desktop')
		elif (sys.platform == 'darwin'):
			desktop = os.path.join(os.environ['HOME'], 'Documents')
			if os.path.exists(desktop):
				self.homepath = desktop
			else:
				self.homepath = os.environ['HOME']
		else:
			desktop = os.path.join(os.environ['HOME'], 'Desktop')
			if os.path.exists(desktop):
				self.homepath = desktop
			else:
				self.homepath = os.environ['HOME']
		
		
		if not os.path.exists(self.homepath):
			if self.DEBUG:
				print "DEBUG: User default path not found"
			self.homepath = os.getcwd()
		
		
		if configuration.INTERFACE_TAB_POSITION == 'South':
			self.tabWidget.setTabPosition(QtGui.QTabWidget.South)
		else:
			self.tabWidget.setTabPosition(QtGui.QTabWidget.North)
		
		
		# EEG Devices
		self.updateDevices()
		
		
		# Connect Server
		self.textLabelBluetoothStatus.setText("Status: Disconnected")
		
		# Display Host for ThinkGear Connect Socket Server
		self.lineEditSynapseHost.setText(SYNAPSE_SERVER_HOST)
		
		# Display Port for ThinkGear Connect Socket Server
		self.lineEditSynapsePort.setText('%i' % SYNAPSE_SERVER_PORT)
		
		
		# ThinkgGear Progress Bars
		self.progressBarEEGDelta.setMaximum(THINKGEAR_EMULATION_MAX_EEG_POWER_VALUE)
		self.progressBarEEGTheta.setMaximum(THINKGEAR_EMULATION_MAX_EEG_POWER_VALUE)
		self.progressBarEEGLowAlpha.setMaximum(THINKGEAR_EMULATION_MAX_EEG_POWER_VALUE)
		self.progressBarEEGHighAlpha.setMaximum(THINKGEAR_EMULATION_MAX_EEG_POWER_VALUE)
		self.progressBarEEGLowBeta.setMaximum(THINKGEAR_EMULATION_MAX_EEG_POWER_VALUE)
		self.progressBarEEGHighBeta.setMaximum(THINKGEAR_EMULATION_MAX_EEG_POWER_VALUE)
		self.progressBarEEGLowGamma.setMaximum(THINKGEAR_EMULATION_MAX_EEG_POWER_VALUE)
		self.progressBarEEGMidGamma.setMaximum(THINKGEAR_EMULATION_MAX_EEG_POWER_VALUE)
		
		self.progressBarAttention.setMaximum(THINKGEAR_EMULATION_MAX_ESENSE_VALUE)
		self.progressBarMeditation.setMaximum(THINKGEAR_EMULATION_MAX_ESENSE_VALUE)
		
		self.progressBarSignalContactQuality.setMaximum(200)
		
		
		if MATPLOTLIB_AVAILABLE:
			self.rawEEGMatplot = rawEEGMatplotlibCanvas( \
			                        self.tabEEGSignals, \
			                        width=8, \
			                        height=4, \
			                        dpi=100, \
			                        title='Raw EEG Waves')
			self.chartEEGMatplot = chartEEGMatplotlibCanvas( \
			                        self.tabCharts, \
			                        width=8, \
			                        height=4, \
			                        dpi=100, \
			                        title='EEG Brain Signals')
		
		else:
			self.tabWidget.removeTab(self.tabWidget.indexOf(self.tabEEGSignals))
			self.tabWidget.removeTab(self.tabWidget.indexOf(self.tabCharts))
	
	
	##################################################################
	
	def connectWidgets(self):
		
		self.connect(self.comboBoxEEGHeadsetModel, \
		             QtCore.SIGNAL("currentIndexChanged(int)"), \
		             self.updateDevices)
		
		self.connect(self.pushButtonBluetoothSearch, \
		             QtCore.SIGNAL("clicked()"), \
		             self.updateDevices)
		
		self.connect(self.pushButtonSynapseServer, \
		             QtCore.SIGNAL("clicked()"), \
		             self.startSynapseServer)
		
		self.connect(self.pushButtonSave, \
		             QtCore.SIGNAL("clicked()"), \
		             self.saveData)
		
		self.connect(self.pushButtonExport, \
		             QtCore.SIGNAL("clicked()"), \
		             self.exportData)
		
		self.connect(self.pushButtonReset, \
		             QtCore.SIGNAL("clicked()"), \
		             self.resetData)
	
	
	##################################################################
	
	def updateInterface(self):
		
		if not self.synapseServer.emulate_headset_data:
			#self.processPacketThinkGear( \
			self.processPacketEEG( \
				self.synapseServer.protocol.data_packet)
	
	
	##################################################################
	
	def updateDevices(self):
		
		if (self.parent != None):
			source = self.parent
		else:
			source = self
		
		model = source.comboBoxEEGHeadsetModel.currentText()
		
		devices = self.searchForDevices()
		
		source.comboBoxDeviceSelect.clear()
		
		if (model == 'NeuroSky MindWave' or \
		    model == 'NeuroSky MindSet' or \
		    model == 'NeuroSky MindWave Mobile'):
			
			devices.insert(0, 'ThinkGear Emulator')
		
		elif (model == 'Emotiv EPOC'):
			
			devices = []
			devices.append('Emotiv Control Panel')
			devices.append('EmoComposer')
		
		
		for device in devices:
			source.comboBoxDeviceSelect.addItem(device)
	
	
	##################################################################
	
	def startSynapseServer(self):
		
		eeg_headset_model = str(self.comboBoxEEGHeadsetModel.currentText())
		#device_address = str(self.comboBoxDeviceSelect.currentText())
		server_interface = str(self.lineEditSynapseHost.text())
		server_port = int(self.lineEditSynapsePort.text())
		
		
		if ((eeg_headset_model == 'NeuroSky MindWave Mobile') or \
		    (eeg_headset_model == 'NeuroSky MindWave') or \
		    (eeg_headset_model == 'NeuroSky MindSet')):
			
			self.startThinkGearConnectService()
		
		elif (eeg_headset_model == 'Emotiv EPOC'):
			
			self.startEmotivService()
		
		
		if UPDATE_INTERFACE_VIA_TIMER:
			self.updateInterfaceTimer.start(INTERFACE_UPDATE_FREQUENCY)
		
		else:
			self.synapseClient = \
				synapse_client.puzzlebox_synapse_client( \
					self.log, \
					server_host=server_interface, \
					server_port=server_port, \
					DEBUG=0, \
					parent=self)
			
			self.synapseClient.start()
		
		
		device_selection = self.comboBoxDeviceSelect.currentText()
		self.textLabelBluetoothStatus.setText("Status: Connected")
		self.pushButtonBluetoothSearch.setEnabled(False)
		self.comboBoxDeviceSelect.setEnabled(False)
		self.comboBoxEEGHeadsetModel.setEnabled(False)
		
		self.lineEditSynapseHost.setEnabled(False)
		self.lineEditSynapsePort.setEnabled(False)
		
		self.pushButtonSynapseServer.setText('Stop')
		
		self.progressBarEEGDelta.setValue(0)
		self.progressBarEEGTheta.setValue(0)
		self.progressBarEEGLowAlpha.setValue(0)
		self.progressBarEEGHighAlpha.setValue(0)
		self.progressBarEEGLowBeta.setValue(0)
		self.progressBarEEGHighBeta.setValue(0)
		self.progressBarEEGLowGamma.setValue(0)
		self.progressBarEEGMidGamma.setValue(0)
		
		self.progressBarAttention.setValue(0)
		self.progressBarMeditation.setValue(0)
		
		
		self.disconnect(self.pushButtonSynapseServer, \
			             QtCore.SIGNAL("clicked()"), \
			             self.startSynapseServer)
		
		self.connect(self.pushButtonSynapseServer, \
			          QtCore.SIGNAL("clicked()"), \
			          self.stopSynapseServer)
	
	
	##################################################################
	
	def stopSynapseServer(self):
		
		eeg_headset_model = str(self.comboBoxEEGHeadsetModel.currentText())
		#device_address = str(self.comboBoxDeviceSelect.currentText())
		
		if ((eeg_headset_model == 'NeuroSky MindWave Mobile') or \
		    (eeg_headset_model == 'NeuroSky MindWave') or \
		    (eeg_headset_model == 'NeuroSky MindSet')):
			
			self.stopThinkGearConnectService()
		
		elif (eeg_headset_model == 'Emotiv EPOC'):
			
			self.stopEmotivService()
		
		
		if UPDATE_INTERFACE_VIA_TIMER:
			self.updateInterfaceTimer.stop()
		else:
			try:
				self.synapseClient.exitThread()
				#self.synapseClient.disconnectFromHost()
			except Exception, e:
				if self.DEBUG:
					print "Call failed to self.synapseClient.exitThread():",
					#print "Call failed to self.synapseClient.disconnectFromHost():",
					print e
			
			try:
				self.synapseServer.exitThread()
			except Exception, e:
				if self.DEBUG:
					print "Call failed to self.synapseServer.exitThread():",
					print e
		
		
		self.disconnect(self.pushButtonSynapseServer, \
		                QtCore.SIGNAL("clicked()"), \
		                self.stopSynapseServer)
		
		self.connect(self.pushButtonSynapseServer, \
			          QtCore.SIGNAL("clicked()"), \
			          self.startSynapseServer)
		
		self.lineEditSynapseHost.setEnabled(True)
		self.lineEditSynapsePort.setEnabled(True)
		
		self.pushButtonSynapseServer.setText('Start')
		
		self.pushButtonBluetoothSearch.setEnabled(True)
		
		self.pushButtonSynapseServer.setChecked(False)
		
		self.textLabelBluetoothStatus.setText("Status: Disconnected")
		
		self.pushButtonBluetoothSearch.setEnabled(True)
		
		self.comboBoxDeviceSelect.setEnabled(True)
		self.comboBoxEEGHeadsetModel.setEnabled(True)
		
		
		self.progressBarEEGDelta.setValue(0)
		self.progressBarEEGTheta.setValue(0)
		self.progressBarEEGLowAlpha.setValue(0)
		self.progressBarEEGHighAlpha.setValue(0)
		self.progressBarEEGLowBeta.setValue(0)
		self.progressBarEEGHighBeta.setValue(0)
		self.progressBarEEGLowGamma.setValue(0)
		self.progressBarEEGMidGamma.setValue(0)
		
		self.progressBarAttention.setValue(0)
		self.progressBarMeditation.setValue(0)
		
		self.progressBarSignalContactQuality.setValue(0)
		
		self.maxEEGPower = THINKGEAR_EMULATION_MAX_EEG_POWER_VALUE
		
		# In case the user connects to a MindSet, then disconnects
		# and re-connects to a MindSet Emulator,
		# we need to reset the max power values
		self.progressBarEEGDelta.setMaximum(self.maxEEGPower)
		self.progressBarEEGTheta.setMaximum(self.maxEEGPower)
		self.progressBarEEGLowAlpha.setMaximum(self.maxEEGPower)
		self.progressBarEEGHighAlpha.setMaximum(self.maxEEGPower)
		self.progressBarEEGLowBeta.setMaximum(self.maxEEGPower)
		self.progressBarEEGHighBeta.setMaximum(self.maxEEGPower)
		self.progressBarEEGLowGamma.setMaximum(self.maxEEGPower)
		self.progressBarEEGMidGamma.setMaximum(self.maxEEGPower)
	
	
	##################################################################
	
	def startThinkGearConnectService(self):
		
		eeg_headset_model = str(self.comboBoxEEGHeadsetModel.currentText())
		device_address = str(self.comboBoxDeviceSelect.currentText())
		server_interface = str(self.lineEditSynapseHost.text())
		server_port = int(self.lineEditSynapsePort.text())
		emulate_headset_data = (device_address == 'ThinkGear Emulator')
		
		
		self.synapseServer = \
			thinkgear_server.puzzlebox_synapse_server_thinkgear( \
				self.log, \
				server_interface=server_interface, \
				server_port=server_port, \
				device_model=eeg_headset_model, \
				device_address=device_address, \
				emulate_headset_data=emulate_headset_data, \
				DEBUG=DEBUG, \
				parent=self)
		
		for header in self.synapseServer.customDataHeaders:
			if header not in self.customDataHeaders:
				self.customDataHeaders.append(header)
		
		self.synapseServer.start()
	
	
	##################################################################
	
	def stopThinkGearConnectService(self):
		
		for header in self.synapseServer.customDataHeaders:
			if header in self.customDataHeaders:
				
				index = self.customDataHeaders.index(header)
				
				del(self.customDataHeaders[index])
	
	
	##################################################################
	
	def startEmotivService(self):
		
		device_address = str(self.comboBoxDeviceSelect.currentText())
		
		if device_address == 'Emotiv Control Panel':
			device_address = configuration.EMOTIV_SERVER_PORT_CONTROL_PANEL
		else:
			device_address = configuration.EMOTIV_SERVER_PORT_EMOCOMPOSER
		
		
		server_interface = str(self.lineEditSynapseHost.text())
		server_port = int(self.lineEditSynapsePort.text())
		eeg_headset_model = str(self.comboBoxEEGHeadsetModel.currentText())
		emulate_headset_data = (device_address == 'ThinkGear Emulator')
		
		
		self.synapseServer = \
			emotiv_server.puzzlebox_synapse_server_emotiv( \
				self.log, \
				server_interface=server_interface, \
				server_port=server_port, \
				device_model=eeg_headset_model, \
				device_address=device_address, \
				emulate_headset_data=emulate_headset_data, \
				DEBUG=DEBUG, \
				parent=self)
		
		for header in self.synapseServer.customDataHeaders:
			if header not in self.customDataHeaders:
				self.customDataHeaders.append(header)
		
		self.synapseServer.start()
		
		
		self.progressBarEEGDelta.setEnabled(False)
		self.progressBarEEGTheta.setEnabled(False)
		self.progressBarEEGLowAlpha.setEnabled(False)
		self.progressBarEEGHighAlpha.setEnabled(False)
		self.progressBarEEGLowBeta.setEnabled(False)
		self.progressBarEEGHighBeta.setEnabled(False)
		self.progressBarEEGLowGamma.setEnabled(False)
		self.progressBarEEGMidGamma.setEnabled(False)
		
		#self.progressBarAttention.setEnabled(False)
		#self.progressBarMeditation.setEnabled(False)
	
	
	##################################################################
	
	def stopEmotivService(self):
		
		#self.emotivClient.stop()
		
		self.progressBarEEGDelta.setEnabled(True)
		self.progressBarEEGTheta.setEnabled(True)
		self.progressBarEEGLowAlpha.setEnabled(True)
		self.progressBarEEGHighAlpha.setEnabled(True)
		self.progressBarEEGLowBeta.setEnabled(True)
		self.progressBarEEGHighBeta.setEnabled(True)
		self.progressBarEEGLowGamma.setEnabled(True)
		self.progressBarEEGMidGamma.setEnabled(True)
		
		#self.progressBarAttention.setEnabled(True)
		#self.progressBarMeditation.setEnabled(True)
	
		for header in self.synapseServer.customDataHeaders:
			if header in self.customDataHeaders:
				del(self.customDataHeaders[header])
	
	
	##################################################################
	
	def processPacketEEG(self, packet):
		
		self.processPacketThinkGear(packet)
		self.processPacketEmotiv(packet)
		
		
		#if ((self.synapseServer.protocol != None) and
		if (self.tabWidget.currentIndex() == \
		    self.tabWidget.indexOf(self.tabControlPanel)):
			
			self.updateProfileSessionStatus()
	
	
	##################################################################
	
	def processPacketThinkGear(self, packet):
		
		#if self.DEBUG > 2:
			#print packet
		
		
		if ('rawEeg' in packet.keys()):
			self.packets['rawEeg'].append(packet['rawEeg'])
			value = packet['rawEeg']
			if MATPLOTLIB_AVAILABLE and \
				(self.tabWidget.currentIndex() == \
				 self.tabWidget.indexOf(self.tabEEGSignals)):
				self.rawEEGMatplot.update_figure(value)
			return
		else:
			# NOTE: This is also logging Emotiv packets to 'signals'
			self.packets['signals'].append(packet)
		
		
		if ('poorSignalLevel' in packet.keys()):
			value = 200 - packet['poorSignalLevel']
			self.progressBarSignalContactQuality.setValue(value)
			self.textEditDebugConsole.append("")
			try:
				(date, localtime) = self.parseTimeStamp(packet['timestamp'])
				self.textEditDebugConsole.append("Timestamp: %s %s" % (date, localtime))
			except:
				pass
			self.textEditDebugConsole.append("poorSignalLevel: %i" % \
			                                 packet['poorSignalLevel'])
		
		
		if ('eSense' in packet.keys()):
			
			if ('attention' in packet['eSense'].keys()):
				value = packet['eSense']['attention']
				self.progressBarAttention.setValue(value)
				self.textEditDebugConsole.append("eSense attention: %i" % value)
			
			if ('meditation' in packet['eSense'].keys()):
				value = packet['eSense']['meditation']
				self.progressBarMeditation.setValue(value)
				self.textEditDebugConsole.append("eSense meditation: %i" % value)
			
			
			if MATPLOTLIB_AVAILABLE:
				self.chartEEGMatplot.update_values('eSense', packet['eSense'])
				if (self.tabWidget.currentIndex() == \
				    self.tabWidget.indexOf(self.tabCharts)):
					self.chartEEGMatplot.update_figure('eSense', packet['eSense'])
		
		
		if ('eegPower' in packet.keys()):
			
			# If we are not emulating packets we'll set the maximum EEG Power value
			# threshold to the default (or maximum value found within this packet)
			if not self.synapseServer.emulate_headset_data:
				self.maxEEGPower = THINKGEAR_EMULATION_MAX_EEG_POWER_VALUE
			
			for value in packet['eegPower'].keys():
				if packet['eegPower'][value] > self.maxEEGPower:
					self.maxEEGPower = packet['eegPower'][value]
			
			
			if ('delta' in packet['eegPower'].keys()):
				value = packet['eegPower']['delta']
				self.progressBarEEGDelta.setMaximum(self.maxEEGPower)
				self.progressBarEEGDelta.setValue(value)
				self.textEditDebugConsole.append("delta: %i" % value)
			
			if ('theta' in packet['eegPower'].keys()):
				value = packet['eegPower']['theta']
				self.progressBarEEGTheta.setMaximum(self.maxEEGPower)
				self.progressBarEEGTheta.setValue(value)
				self.textEditDebugConsole.append("theta: %i" % value)
			
			if ('lowAlpha' in packet['eegPower'].keys()):
				value = packet['eegPower']['lowAlpha']
				self.progressBarEEGLowAlpha.setMaximum(self.maxEEGPower)
				self.progressBarEEGLowAlpha.setValue(value)
				self.textEditDebugConsole.append("lowAlpha: %i" % value)
			
			if ('highAlpha' in packet['eegPower'].keys()):
				value = packet['eegPower']['highAlpha']
				self.progressBarEEGHighAlpha.setMaximum(self.maxEEGPower)
				self.progressBarEEGHighAlpha.setValue(value)
				self.textEditDebugConsole.append("highAlpha: %i" % value)
			
			if ('lowBeta' in packet['eegPower'].keys()):
				value = packet['eegPower']['lowBeta']
				self.progressBarEEGLowBeta.setMaximum(self.maxEEGPower)
				self.progressBarEEGLowBeta.setValue(value)
				self.textEditDebugConsole.append("lowBeta: %i" % value)
			
			if ('highBeta' in packet['eegPower'].keys()):
				value = packet['eegPower']['highBeta']
				self.progressBarEEGHighBeta.setMaximum(self.maxEEGPower)
				self.progressBarEEGHighBeta.setValue(value)
				self.textEditDebugConsole.append("highBeta: %i" % value)
			
			if ('lowGamma' in packet['eegPower'].keys()):
				value = packet['eegPower']['lowGamma']
				self.progressBarEEGLowGamma.setMaximum(self.maxEEGPower)
				self.progressBarEEGLowGamma.setValue(value)
				self.textEditDebugConsole.append("lowGamma: %i" % value)
			
			if ('highGamma' in packet['eegPower'].keys()):
				value = packet['eegPower']['highGamma']
				self.progressBarEEGMidGamma.setMaximum(self.maxEEGPower)
				self.progressBarEEGMidGamma.setValue(value)
				self.textEditDebugConsole.append("highGamma: %i" % value)
			
			
			if MATPLOTLIB_AVAILABLE:
				self.chartEEGMatplot.update_values('eegPower', packet['eegPower'])
				if (self.tabWidget.currentIndex() == \
				    self.tabWidget.indexOf(self.tabCharts)):
					self.chartEEGMatplot.update_figure('eegPower', packet['eegPower'])
	
	
	##################################################################
	
	def processPacketEmotiv(self, packet):
		
		if self.DEBUG > 2:
			print "INFO [Synapse:Interface] Emotiv packet received:"
			print packet
		
		
		if ('emotivStatus' in packet.keys()):
			
			if ('timeFromStart' in packet['emotivStatus']):
				if not configuration.EMULATE_THINKGEAR_FOR_EMOTIV:
					self.textEditDebugConsole.append("")
					try:
						(date, localtime) = self.parseTimeStamp(packet['timestamp'])
						self.textEditDebugConsole.append("Timestamp: %s %s" % (date, localtime))
					except:
						pass
				self.textEditDebugConsole.append("timeFromStart: %f" % \
				                                  packet['emotivStatus']['timeFromStart'])
			
			if ('headsetOn' in packet['emotivStatus']):
				self.textEditDebugConsole.append("headsetOn: %s" % \
				                                  bool(packet['emotivStatus']['headsetOn']))
			
			if ('contactNumberOfQualityChannels' in packet['emotivStatus']):
				self.textEditDebugConsole.append("contactNumberOfQualityChannels: %i" % \
				                                  packet['emotivStatus']['contactNumberOfQualityChannels'])
			
			if ('wireless' in packet['emotivStatus']):
				self.textEditDebugConsole.append("wireless: %i" % \
				                                  packet['emotivStatus']['wireless'])
		
		
		if ('affectiv' in packet.keys()):
			
			if ('excitement' in packet['affectiv']):
				self.textEditDebugConsole.append("excitement: %.2f" % \
				                                  packet['affectiv']['excitement'])
			
			if ('longTermExcitement' in packet['affectiv']):
				self.textEditDebugConsole.append("longTermExcitement: %.2f" % \
				                                  packet['affectiv']['longTermExcitement'])
			
			if ('meditation' in packet['affectiv']):
				self.textEditDebugConsole.append("meditation: %.2f" % \
				                                  packet['affectiv']['meditation'])
			
			if ('frustration' in packet['affectiv']):
				self.textEditDebugConsole.append("frustration: %.2f" % \
				                                  packet['affectiv']['frustration'])
			
			if ('engagementBoredom' in packet['affectiv']):
				self.textEditDebugConsole.append("engagementBoredom: %.2f" % \
				                                  packet['affectiv']['engagementBoredom'])
		
		
		if ('cognitiv' in packet.keys()):
			
			if ('currentAction' in packet['cognitiv']):
				self.textEditDebugConsole.append("currentAction: %i" % \
				                                  packet['cognitiv']['currentAction'])
			
			if ('currentActionPower' in packet['cognitiv']):
				self.textEditDebugConsole.append("currentActionPower: %.2f" % \
				                                  packet['cognitiv']['currentActionPower'])
	
	
	
	##################################################################
	
	def setPacketCount(self, value):
		
		self.packet_count = value
	
	
	##################################################################
	
	def setBadPackets(self, value):
		
		self.bad_packets = value
	
	
	##################################################################
	
	def incrementPacketCount(self):
		
		self.packet_count += 1
	
	
	##################################################################
	
	def incrementBadPackets(self):
		
		self.bad_packets += 1
	
	
	##################################################################
	
	def getPacketCount(self):
		
		return (self.packet_count)
	
	
	##################################################################
	
	def getBadPackets(self):
		
		return (self.bad_packets)
	
	
	##################################################################
	
	def getSessionTime(self):
		
		return (self.session_start_timestamp)
	
	
	##################################################################
	
	def resetSessionStartTime(self):
	
		#self.synapseServer.protocol.resetSessionStartTime()
		#self.resetSessionStartTime()
		self.session_start_timestamp = time.time()
	
	
	##################################################################
	
	def processPacketForExport(self, packet={}, output={}):
		
		if self.synapseServer != None:
			output = self.synapseServer.processPacketForExport(packet, output)
		
		return(output)
	
	
	##################################################################
	
	def stop(self):
		
		if UPDATE_INTERFACE_VIA_TIMER:
			self.updateInterfaceTimer.stop()
		else:
			if self.synapseClient != None:
				self.synapseClient.exitThread()
			#if self.thinkgearConnectClient != None:
				#self.thinkgearConnectClient.exitThread()
			#if self.emotivClient != None:
				#self.emotivClient.exitThread()
		
		if self.synapseServer != None:
			self.synapseServer.exitThread()
	
	
	##################################################################
	
	def closeEvent(self, event):
		
		quit_message = "Are you sure you want to exit the program?"
		
		reply = QtGui.QMessageBox.question( \
		           self, \
		          'Message', \
		           quit_message, \
		           QtGui.QMessageBox.Yes, \
		           QtGui.QMessageBox.No)
		
		if reply == QtGui.QMessageBox.Yes:
			
			self.stop()
			
			event.accept()
		
		else:
			event.ignore()

