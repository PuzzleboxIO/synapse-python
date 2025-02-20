#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright Puzzlebox Productions, LLC (2010-2016)
#
# This code is released under the GNU Affero Pulic License (AGPL) version 3
# For more information please refer to https://www.gnu.org/licenses/agpl.html

__changelog__ = """
Last Update: 2016.05.14
"""

import os, sys

#####################################################################
# General configuration
#####################################################################

DEBUG = 1

CONFIGURATION_FILE_PATH = 'puzzlebox_synapse_configuration.ini'

if (sys.platform != 'win32'):
	if not os.path.exists(CONFIGURATION_FILE_PATH):
		CONFIGURATION_FILE_PATH = \
			os.path.join('/etc/puzzlebox_synapse', CONFIGURATION_FILE_PATH)

ENABLE_QT = True
ENABLE_PYSIDE = True
#ENABLE_PYSIDE = False
ENABLE_HCITOOL = False

INTERFACE_CHART_STYLES = { \
	'attention': 'r-', \
	'meditation': 'b-', \
	'delta': 'g-', \
	'theta': 'y-', \
	'lowAlpha': 'c-', \
	'highAlpha': 'b-', \
	'lowBeta': 'r-', \
	'highBeta': 'm-', \
	'lowGamma': 'k-', \
	'highGamma': 'k-', \
	'excitement': 'r-', \
	'longTermExcitement': 'm-', \
	'frustration': 'y-', \
	'engagementBoredom': 'c-', \
	'cognitiv': 'k-', \
	'trendingGreen': 'g-', \
	'trendingBlack': 'k-', \
	'trendingRed': 'r-', \
	'FFT': 'g-', \
}

INTERFACE_TAB_POSITION = 'North'

#The following color abbreviations are supported:
#character 	color
#‘b’ 	blue
#‘g’ 	green
#‘r’ 	red
#‘c’ 	cyan
#‘m’ 	magenta
#‘y’ 	yellow
#‘k’ 	black
#‘w’ 	white

#The following format string characters are accepted to control the line style or marker:
#character 	description
#'-' 	solid line style
#'--' 	dashed line style
#'-.' 	dash-dot line style
#':' 	dotted line style
#'.' 	point marker
#',' 	pixel marker
#'o' 	circle marker
#'v' 	triangle_down marker
#'^' 	triangle_up marker
#'<' 	triangle_left marker
#'>' 	triangle_right marker
#'1' 	tri_down marker
#'2' 	tri_up marker
#'3' 	tri_left marker
#'4' 	tri_right marker
#'s' 	square marker
#'p' 	pentagon marker
#'*' 	star marker
#'h' 	hexagon1 marker
#'H' 	hexagon2 marker
#'+' 	plus marker
#'x' 	x marker
#'D' 	diamond marker
#'d' 	thin_diamond marker
#'|' 	vline marker
#'_' 	hline marker


#####################################################################
# Network addresses
#####################################################################

SYNAPSE_SERVER_INTERFACE = '' # listen on all of server's network interfaces
SYNAPSE_SERVER_HOST = '*'
SYNAPSE_SERVER_PORT = 13854

THINKGEAR_SERVER_INTERFACE = '' # listen on all of server's network interfaces
#THINKGEAR_SERVER_HOST = '127.0.0.1'
THINKGEAR_SERVER_HOST = '*'
THINKGEAR_SERVER_PORT = 13854

EMOTIV_SERVER_HOST = '127.0.0.1'
EMOTIV_SERVER_PORT_CONTROL_PANEL = 3008
EMOTIV_SERVER_PORT_EMOCOMPOSER = 1726

MUSE_SERVER_HOST = '127.0.0.1'
MUSE_SERVER_PORT = 5001

JIGSAW_HARDWARE_JOYSTICK_HOST = '127.0.0.1'
JIGSAW_HARDWARE_JOYSTICK_PORT = 51914

#####################################################################
# ThinkGear Device configuration
#####################################################################

DEFAULT_THINKGEAR_DEVICE_SERIAL_PORT_WINDOWS = 'COM2'
DEFAULT_THINKGEAR_DEVICE_SERIAL_PORT_LINUX = '/dev/rfcomm0'

if (sys.platform == 'win32'):
	THINKGEAR_DEVICE_SERIAL_PORT = DEFAULT_THINKGEAR_DEVICE_SERIAL_PORT_WINDOWS
else:
	THINKGEAR_DEVICE_SERIAL_PORT = DEFAULT_THINKGEAR_DEVICE_SERIAL_PORT_LINUX

# Use Bluetooth MAC address for Linux
THINKGEAR_DEVICE_BLUETOOTH_ADDRESS = ''
# THINKGEAR_DEVICE_BLUETOOTH_ADDRESS = '00:13:EF:xx:xx:xx' # Linux example

#THINKGEAR_DEVICE_ID = None

# Timeouts sent to PyBluez

#THINKGEAR_BLUETOOTH_SEARCH = True
THINKGEAR_BLUETOOTH_SEARCH = False
THINKGEAR_BLUETOOTH_DISCOVER_DEVICES_TIMEOUT = 8 # default 8
THINKGEAR_BLUETOOTH_LOOKUP_NAME_TIMEOUT = 10 # default 10


#####################################################################
# Synapse Server configuration
#####################################################################

CLIENT_NO_REPLY_WAIT = 5 # how many seconds before considering a component dead

SYNAPSE_DELIMITER = '\r'

#####################################################################
# ThinkGear Connect configuration
#####################################################################

THINKGEAR_DELIMITER = '\r'

#THINKGEAR_CONFIGURATION_PARAMETERS = {"enableRawOutput": False, "format": "Json"}
THINKGEAR_CONFIGURATION_PARAMETERS = {"enableRawOutput": True, "format": "Json"}

ENABLE_THINKGEAR_AUTHORIZATION = False

THINKGEAR_AUTHORIZATION_REQUEST = { \
        "appName": "Puzzlebox Brainstorms", \
        "appKey": "2e285d7bd5565c0ea73e7e265c73f0691d932408"
        }

THINKGEAR_EEG_POWER_BAND_ORDER = ['delta', \
                                  'theta', \
                                  'lowAlpha', \
                                  'highAlpha', \
                                  'lowBeta', \
                                  'highBeta', \
                                  'lowGamma', \
                                  'highGamma']

THINKGEAR_EMULATION_MAX_ESENSE_VALUE = 100
THINKGEAR_EMULATION_MAX_EEG_POWER_VALUE = 16384

THINKGEAR_ATTENTION_MULTIPLIER = 1.0
THINKGEAR_MEDITATION_MULTIPLIER = 0.8
THINKGEAR_MEDITATION_PLOT_OFFSET = 5

THINKGEAR_EEG_POWER_MULTIPLIERS = { \
	'delta': 1.0, \
	'theta': 1.0, \
	'lowAlpha': 1.0, \
	'highAlpha': 1.0, \
	'lowBeta': 1.0, \
	'highBeta': 1.0, \
	'lowGamma': 1.0, \
	'highGamma': 1.0, \
}


#####################################################################
# ThinkGear Connect Server Emulator configuration
#####################################################################

THINKGEAR_ENABLE_SIMULATE_HEADSET_DATA = True

THINKGEAR_BLINK_FREQUENCY_TIMER = 6 # blink every 6 seconds
                                    # (6 seconds is listed by Wikipedia
                                    # as being the average number of times
                                    # an adult blinks in a laboratory setting)

THINKGEAR_DEFAULT_SAMPLE_WAVELENGTH = 30 # number of seconds from 0 to max
                                         # and back to 0 for any given
                                         # detection value below


#####################################################################
# Emotiv configuration
#####################################################################

EMULATE_THINKGEAR_FOR_EMOTIV = True


#####################################################################
# Muse configuration
#####################################################################

EMULATE_THINKGEAR_FOR_MUSE = True


#####################################################################
# Flash socket policy handling
#####################################################################

FLASH_POLICY_FILE_REQUEST = \
        '<policy-file-request/>%c' % 0 # NULL byte termination
FLASH_SOCKET_POLICY_FILE = '''<?xml version="1.0"?>
<!DOCTYPE cross-domain-policy SYSTEM "http://www.macromedia.com/xml/dtds/cross-domain-policy.dtd">
<cross-domain-policy>
   <site-control permitted-cross-domain-policies="all" />
   <allow-access-from domain="*" to-ports="%i" />
</cross-domain-policy>%c''' % (THINKGEAR_SERVER_PORT, 0)


#####################################################################
# Rabbit MQ
#####################################################################

RABBITMQ_HOST = 'localhost'
RABBITMQ_USERNAME = 'guest'
RABBITMQ_PASSWORD = 'guest'
PUBLISHER_USERNAME = 'user_0'
PUBLISHER_DEVICE = 'neurosky'
PUBLISHER_METRIC = 'mindwave'


#####################################################################
# Cloudbrain
#####################################################################

ENABLE_CLOUDBRAIN = False


#####################################################################
# Jigsaw Joystick
#####################################################################

ENABLE_JIGSAW_JOYSTICK = True


#####################################################################
# Configuration File Parser
#####################################################################

if os.path.exists(CONFIGURATION_FILE_PATH):
	
	file = open(CONFIGURATION_FILE_PATH, 'r')
	
	for line in file.readlines():
		line = line.strip()
		if len(line) == 0:
			continue
		if line[0] == '#':
			continue
		if line.find('=') == -1:
			continue
		if (line == "THINKGEAR_DEVICE_SERIAL_PORT = ''"):
			# use operating system default if device not set manually
			continue
		try:
			exec line
		except:
			if DEBUG:
				print "Error recognizing configuration option:",
				print line

