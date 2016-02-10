# -*- coding: utf-8 -*-

# Copyright Puzzlebox Productions, LLC (2010-2014)
#
# This code is released under the GNU Pulic License (GPL) version 2
# For more information please refer to http://www.gnu.org/copyleft/gpl.html

__changelog__ = """\
Last Update: 2014.02.23
"""

__todo__ = """
"""

### IMPORTS ###
import os, sys, time

import Puzzlebox.Synapse.Configuration as configuration

if configuration.ENABLE_PYSIDE:
	try:
		import PySide as PyQt4
		from PySide import QtCore, QtGui
	except Exception, e:
		print "ERROR: [Synapse:Session] Exception importing PySide:",
		print e
		configuration.ENABLE_PYSIDE = False
	else:
		print "INFO: [Synapse:Session] Using PySide module"

if not configuration.ENABLE_PYSIDE:
	print "INFO: [Synapse:Session] Using PyQt4 module"
	from PyQt4 import QtCore, QtGui


try:
	import cPickle as pickle
except:
	import pickle


#####################################################################
# Globals
#####################################################################

DEBUG = configuration.DEBUG

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

PACKET_MINIMUM_TIME_DIFFERENCE_THRESHOLD = 0.75

#####################################################################
# Classes
#####################################################################

class puzzlebox_synapse_session(QtGui.QWidget):
	
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
		
		self.name = "Synapse:Session"
		
		
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
				print "WARNING: [Synapse:Session] User default path not found"
			self.homepath = os.getcwd()
	
	
	##################################################################
	
	def configureSettings(self):
		
		pass
	
	
	##################################################################
	
	def connectWidgets(self):
		
		pass
	
	
	##################################################################
	
	def updateProfileSessionStatus(self, source=None, target=None):
		
		session_time = self.calculateSessionTime()
		
		#if source == None:
			#if self.parent == None:
				#source = self
			#else:
				#source = self.parent
		
		#if target == None:
			#if self.parent == None:
				#target = self
			#else:
				#target = self.parent
		
		#target.textLabelSessionTime.setText(session_time)
		self.textLabelSessionTime.setText(session_time)
		
			#self.parent.packet_count)
			#self.synapseServer.protocol.packet_count)
		
		try:
			packet_count = self.parent.plugin_eeg.getPacketCount()
		except:
			try:
				packet_count = self.synapseServer.protocol.packet_count
			except:
				packet_count = 0
		
		self.textLabelPacketsReceived.setText( "%i" % packet_count)
		
		
		try:
			bad_packets = self.parent.plugin_eeg.getBadPackets()
		except:
			try:
				bad_packets = self.synapseServer.protocol.bad_packets
			except:
				bad_packets = 0
		
		self.textLabelPacketsDropped.setText( "%i" % bad_packets)
	
	
	##################################################################
	
	def calculateSessionTime(self):
		
		session_time = self.getSessionTime()
		
		session_time = time.time() - session_time
		session_time = int(session_time)
		session_time = self.convert_seconds_to_datetime(session_time)
		
		return (session_time)
	
	
	##################################################################
	
	def getSessionTime(self):
		
		return (self.synapseServer.session_start_timestamp)
	
	
	##################################################################
	
	def collectData(self, source=None, target=None):
		
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
		
		data = {}
		
		data['rawEeg'] = source.packets['rawEeg']
		data['signals'] = source.packets['signals']
		
		data['sessionTime'] = self.calculateSessionTime()
		
		data['profileName'] = str(target.lineEditSessionProfile.text())
		
		return(data)
	
	
	##################################################################
	
	def parseTimeStamp(self, timestamp, local_version=False, truncate_time_zone=False):
		
		try:
			decimal = '%f' % timestamp
			decimal = decimal.split('.')[1]
		except:
			decimal = '0'
		
		localtime = time.localtime(timestamp)
		
		if local_version:
			date = time.strftime('%x', localtime)
			localtime = time.strftime('%X', localtime)
		
		elif truncate_time_zone:
			date = time.strftime('%Y-%m-%d', localtime)
			localtime = time.strftime('%H:%M:%S', localtime)
			localtime = '%s.%s' % (localtime, decimal[:3])
		
		else:
			date = time.strftime('%Y-%m-%d', localtime)
			localtime = time.strftime('%H:%M:%S', localtime)
			localtime = '%s.%s %s' % (localtime, decimal, \
			               time.strftime('%Z', time.localtime(timestamp)))
		
		
		return(date, localtime)
	
	
	##################################################################
	
	def saveData(self, source=None, target=None, output_file=None, use_default=False):
		
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
		
		data = self.collectData(source=source, target=target)
		
		(date, localtime) = self.parseTimeStamp(time.time())
		
		default_filename = '%s %s.synapse' % (date, \
		                      target.lineEditSessionProfile.text())
		                      
		default_filename = os.path.join(self.homepath, default_filename)
		
		
		if output_file == None:
			
			# use_default controls whether or not a file is automatically saves using the
			# default name and path (as opposed to raising a GUI file selection menu)
			# whenever an explicit filepath is not defined
			if use_default:
					
					output_file = default_filename
			
			else:
			
				output_file = QtGui.QFileDialog.getSaveFileName(parent=target, \
				                 caption="Save Session Data to File", \
				                 directory=default_filename, \
				                 filter="Puzzlebox Synapse Data File (*.synapse)")
				
				# TODO 2014-02-09 Disabling due to failure with Puzzlebox Orbit
				# TODO 2014-02-23 Re-enabled due to failure to write files
				try:
					output_file = output_file[0]
				except:
					#output_file = ''
					# TODO 2014-02-23 Attempted compromise
					pass
					
		
		
		if output_file == '':
			return
		
		
		file = open(str(output_file), 'w')
		pickle.dump(data, file)
		file.close()
	
	
	##################################################################
	
	def exportData(self, parent=None, source=None, target=None, output_file=None, use_default=False):
		
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
			export_csv_raw = target.configuration.EXPORT_CSV_RAW_DATA
		except:
			export_csv_raw = False
		
		
		(date, localtime) = self.parseTimeStamp(time.time())
		
		default_filename = '%s %s.csv' % (date, \
		                      target.lineEditSessionProfile.text())
		
		default_filename = os.path.join(target.homepath, default_filename)
		
		
		if output_file == None:
			
			# use_default controls whether or not a file is automatically saves using the
			# default name and path (as opposed to raising a GUI file selection menu)
			# whenever an explicit filepath is not defined
			if use_default:
					
					output_file = default_filename
			
			else:
				output_file = QtGui.QFileDialog.getSaveFileName(parent=target, \
				                 caption="Export Session Data to File", \
				                 directory=default_filename, \
				                 filter="CSV File (*.csv);;Text File (*.txt)")
				
				# TODO 2014-02-09 Disabling due to failure with Puzzlebox Orbit
				# TODO 2014-02-23 Re-enabled due to failure to write files
				try:
					output_file = output_file[0]
				except:
					#output_file = ''
					# TODO 2014-02-23 Attempted compromise
					pass
		
		
		if output_file == '':
			return
		
		
		if str(output_file).endswith('.csv'):
			
			outputData = self.exportDataToCSV(parent=parent, source=source, target=target)
		
		
		else:
			
			try:
				outputData = self.textEditDebugConsole.toPlainText()
			except:
				outputData = self.exportDataToCSV(parent=parent, source=source, target=target)
		
		
		if self.DEBUG:
			print "Writing file:",
			print output_file
		
		
		file = open(os.path.join(str(output_file)), 'w')
		file.write(outputData)
		file.close()
		
		
		if export_csv_raw:
			
			output_file = output_file.replace('.csv', '-rawEeg.csv')
			
			outputData = self.exportRawDataToCSV(parent=parent, source=source, target=target)
			
			if outputData != None:
				
				file = open(str(output_file), 'w')
				file.write(outputData)
				file.close()
	
	
	##################################################################
	
	def exportDataToCSV(self, parent=None, source=None, target=None):
		
		# handle importing class from multiple sources
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
		
		
		#print source.name
		#print source.packets['signals']
		
		
		# NOTE: no need to scrub emulated data
		try:
			scrub_data = target.configuration.EXPORT_CSV_SCRUB_DATA
		except:
			scrub_data = False
		
		try:
			if self.parent.plugin_eeg.emulate_headset_data:
				scrub_data = False
		except:
			pass
		
		
		headers = 'Date,Time'
		
		
		customDataHeaders = []
		for header in parent.customDataHeaders:
			customDataHeaders.append(header)
		for plugin in parent.activePlugins:
			#print plugin.name
			for header in plugin.customDataHeaders:
				customDataHeaders.append(header)
		
		for each in customDataHeaders:
			headers = headers + ',%s' % each
		
		headers = headers + '\n'
		
		
		csv = {}
		
		
		for packet in source.packets['signals']:
			
			
			# NOTE: Move this to ThinkGear Server object
			#if 'rawEeg' in packet.keys():
				#continue
			
			
			if 'timestamp' not in packet.keys() and len(packet.keys()) == 1:
				if self.DEBUG:
					print "WARN: Skipping empty packet:",
					print packet
				# skip empty packets
				continue
			
			
			print "packet:",
			print packet
			
			timestamp = packet['timestamp']
			#(date, localtime) = self.parseTimeStamp(timestamp, \
										#truncate_time_zone=truncate_csv_timezone)
			(date, localtime) = source.parseTimeStamp(timestamp, \
										truncate_time_zone=truncate_csv_timezone)
			
			if timestamp not in csv.keys():
				
				#if 'blinkStrength' in packet.keys():
					## Skip any blink packets from log
					#continue
				
				
				#timestamp = packet['timestamp']
				##(date, localtime) = self.parseTimeStamp(timestamp, \
				                    ##truncate_time_zone=truncate_csv_timezone)
				#(date, localtime) = source.parseTimeStamp(timestamp, \
				                    #truncate_time_zone=truncate_csv_timezone)
				
				csv[timestamp] = {}
				csv[timestamp]['Date'] = date
				csv[timestamp]['Time'] = localtime
			
			
			for plugin in parent.activePlugins:
				if plugin.customDataHeaders != []:
					if self.DEBUG > 2:
						print "INFO: [Synapse:Session] Exporting:",
						print plugin.name
					try:
						csv[timestamp] = plugin.processPacketForExport(packet=packet, output=csv[timestamp])
						if self.DEBUG > 2:
							print "INFO [Synapse:Session]: Export Successful"
							print plugin.name
					except Exception, e:
						if self.DEBUG:
							print "ERROR: [Synapse:Session] Exception calling processPacketForExport on",
							print plugin.name
			
			
			for header in customDataHeaders:
				
				if 'custom' in packet.keys() and \
				   header in packet['custom'].keys():
					
					timestamp = packet['timestamp']
					(date, localtime) = source.parseTimeStamp(timestamp, \
					                       truncate_time_zone=truncate_csv_timezone)
					
					if timestamp not in csv.keys():
						csv[timestamp] = {}
						csv[timestamp]['Date'] = date
						csv[timestamp]['Time'] = localtime
						if self.DEBUG:
							print "WARN: Unmatched custom packet:",
							print packet
					
					csv[timestamp][header] = packet['custom'][header]
		
		
		if scrub_data:
			csv = self.scrubData(csv, truncate_csv_timezone, source=source)
		
		
		output = headers
		
		timestamps = csv.keys()
		timestamps.sort()
		
		for timestamp in timestamps:
			
			row = '%s,%s' % \
			      (csv[timestamp]['Date'], \
			       csv[timestamp]['Time'])
			
			for header in customDataHeaders:
				if header in csv[timestamp].keys():
					row = row + ',%s' % csv[timestamp][header]
				else:
					#row = row + ','
					row = ''
					if self.DEBUG > 1:
						print "WARN: empty signals packet:",
						print csv[timestamp]
					break
			
			if row != '':
				row = row + '\n'
			
			output = output + row
		
		
		return(output)
	
	
	##################################################################
	
	def exportRawDataToCSV(self, parent=None, source=None, target=None):
		
		# handle importing class from multiple sources
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
		
		
		if source.packets['rawEeg'] == []:
			return(None)
		
		
		headers = 'Date,Time,Raw EEG'
		headers = headers + '\n'
		
		csv = {}
		
		for packet in source.packets['rawEeg']:
			
			# NOTE: Move this to ThinkGear Server object
			if 'rawEeg' in packet.keys():
				
				if packet['timestamp'] not in csv.keys():
					
					timestamp = packet['timestamp']
					
					(date, localtime) = source.parseTimeStamp(timestamp, \
					                    truncate_time_zone=truncate_csv_timezone)
					
					csv[timestamp] = {}
					csv[timestamp]['Date'] = date
					csv[timestamp]['Time'] = localtime
					csv[timestamp]['rawEeg'] = packet['rawEeg']
		
		
		output = headers
		
		timestamps = csv.keys()
		
		# Don't sort timestamps in order to better preserve the original raw signal
		#timestamps.sort()
		
		for timestamp in timestamps:
			
			row = '%s,%s,%s' % \
			      (csv[timestamp]['Date'], \
			       csv[timestamp]['Time'], \
			       csv[timestamp]['rawEeg'])
			
			row = row + '\n'
			
			output = output + row
		
		
		return(output)
	
	
	#################################################################
	
	def scrubData(self, csv, truncate_csv_timezone=False, source=None):
		
		# If there are missing packets, repeat a given packet once per missing
		# second until there is a gap between 1 and 2 seconds, in which case
		# produce a final duplicate packet at the mid-point between the packets
		
		if self.DEBUG:
			print "INFO: Scrubbing Data"
		
		if source == None:
			if self.parent == None:
				source = self
			else:
				source = self.parent
		
		last_time = None
		last_recorded_time = None
		
		output = {}
		
		csv_keys = csv.keys()
		csv_keys.sort()
		
		for key in csv_keys:
			
			timestamp = key
			
			if last_time == None:
				# First entry in log
				last_time = timestamp
				last_recorded_time = timestamp
				#output[key] = csv[key]
				if key not in output.keys():
					output[key] = DEFAULT_PACKET.copy()
				output[key].update(csv[key])
				continue
			
			else:
				
				#time_difference = timestamp - last_time
				#time_difference = timestamp - last_recorded_time
				time_difference = abs(timestamp - last_recorded_time)
				
				if (time_difference <= 1) and \
				   (time_difference >= PACKET_MINIMUM_TIME_DIFFERENCE_THRESHOLD):
					# Skip packets within the correct time threshold
					last_time = timestamp
					last_recorded_time = timestamp
					#output[key] = csv[key]
					if key not in output.keys():
						output[key] = DEFAULT_PACKET.copy()
					output[key].update(csv[key])
					
					#print "<=1 and >=min"
					continue
				
				else:
					
					if self.DEBUG > 1:
						print "time_difference:",
						print time_difference
						print "timestamp:",
						print source.parseTimeStamp(timestamp)[-1].split(' ')[0]
						print "last_time:",
						print source.parseTimeStamp(last_time)[-1].split(' ')[0]
						print "last_recorded_time:",
						print source.parseTimeStamp(last_recorded_time)[-1].split(' ')[0]
					
					
					#new_packet = csv[key].copy()
					if key not in output.keys():
						new_packet = DEFAULT_PACKET.copy()
					new_packet.update(csv[key])
					
					if time_difference >= 2:
						
						##new_time = last_time + 1
						#new_time = last_recorded_time + 1
						
						count = int(time_difference)
						while count >= 1:
							#new_packet = csv[key].copy()
							if key not in output.keys():
								new_packet = DEFAULT_PACKET.copy()
							new_packet.update(csv[key])
							
							new_time = last_recorded_time + 1
							(date, formatted_new_time) = source.parseTimeStamp(new_time, \
							 truncate_time_zone=truncate_csv_timezone)
							new_packet['Time'] = formatted_new_time
							last_recorded_time = new_time
							last_time = timestamp
							if key not in output.keys():
								output[new_time] = new_packet
							else:
								output[new_time].update(new_packet)
							count = count - 1
						continue
					
						#print ">=2"
					
					
					elif time_difference < PACKET_MINIMUM_TIME_DIFFERENCE_THRESHOLD:
						# Spread out "bunched up" packets
						#new_time = last_time + 1
						new_time = last_recorded_time + 1
						#new_time = last_recorded_time
						#print "<min"
					
					
					elif (time_difference < 2) and (time_difference > 1):
						
						#new_time = last_time + ((last_time - timestamp) / 2)
						#new_time = last_recorded_time + ((last_recorded_time - timestamp) / 2)
						#new_time = last_time + 1
						#new_time = last_recorded_time + 1
						new_time = last_recorded_time
						#print "<2"
					
					
					(date, formatted_new_time) = source.parseTimeStamp(new_time, \
					   truncate_time_zone=truncate_csv_timezone)
					
					new_packet['Time'] = formatted_new_time
					
					#last_time = new_time
					last_recorded_time = new_time
					#last_time = timestamp
					last_time = new_time
					try:
						output[new_time].update(new_packet)
					except Exception, e:
						output[new_time] = new_packet
						#print e
					
					if self.DEBUG > 1:
						print "WARN: Scrubbing new packet:",
						print new_packet
						print
		
		
		return(output)
	
	
	##################################################################
	
	def resetData(self, source=None):
		
		if source == None:
			if self.parent == None:
				source = self
			else:
				source = self.parent
		
		source.packets['rawEeg'] = []
		source.packets['signals'] = []
		
		if self.synapseServer != None:
			self.synapseServer.protocol.resetSessionStartTime()
		else:
			self.resetSessionStartTime()
		
		if self.synapseServer != None:
			source.synapseServer.protocol.packet_count = 0
			source.synapseServer.protocol.bad_packets = 0
		else:
			source.packet_count = 0
			source.bad_packets = 0
		
		self.updateProfileSessionStatus()
		
		try:
			source.textEditDebugConsole.setText("")
		except:
			pass
	
	
	#####################################################################
	
	def resetSessionStartTime(self, source=None):
		
		self.session_start_timestamp = time.time()
		
		
	#####################################################################
	
	def convert_seconds_to_datetime(self, duration):
		
		duration_hours = duration / (60 * 60)
		duration_minutes = (duration - (duration_hours * (60 * 60))) / 60
		duration_seconds = (duration - (duration_hours * (60 * 60)) - (duration_minutes * 60))
		
		duration_hours = '%i' % duration_hours
		if (len(duration_hours) == 1):
			duration_hours = "0%s" % duration_hours
		
		duration_minutes = '%i' % duration_minutes
		if (len(duration_minutes) == 1):
			duration_minutes = "0%s" % duration_minutes
		
		duration_seconds = '%i' % duration_seconds
		if (len(duration_seconds) == 1):
			duration_seconds = "0%s" % duration_seconds
		
		datetime = '%s:%s:%s' % (duration_hours, duration_minutes, duration_seconds)
		
		return(datetime)

