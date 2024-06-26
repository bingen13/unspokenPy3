# -*- coding: utf-8 -*-
# Copyright (C) 2020 - Sean: mailto:s.tostoyevski@gmail.com
# GitHub: https://github.com/SeanTolstoyevski
# This project is licensed under the MIT license. You are free to do whatever you want as long as you accept your liability.

# : NVDA's modules
import addonHandler
import config
import globalPluginHandler
import NVDAObjects
import speech
import ui
import gui
import wx
# : 3rd party module
from .camlorn_audio import *
from .setting import UnspokenSettingDialog
from .soundtheme import *

AUDIO_WIDTH = 10.0  # Width of the audio display.
AUDIO_DEPTH = 5.0  # Distance of listener from display.

confspec = {
	"active": "boolean(default=true)",
	"soundtheme": "string(default='default theme')"
}

addonHandler.initTranslation()


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	scriptCategory = _("Unspoken")

	def __init__(self, *args, **kwargs):
		super(GlobalPlugin, self).__init__(*args, **kwargs)
		self.unspokenSetting = gui.mainFrame.sysTrayIcon.preferencesMenu.Append(
			id=wx.ID_ANY, item="unspoken  setting")	
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.showSetting, self.unspokenSetting)
		config.conf.spec["unspokenpy3"] = confspec
		init_camlorn_audio()
		loadSoundTheme(config.conf["unspokenpy3"]["soundtheme"])
		

		self._NVDA_getSpeechTextForProperties = speech.speech.getPropertiesSpeech
		speech.speech.getPropertiesSpeech = self._hook_getSpeechTextForProperties

		self._previous_mouse_object = None

	def _hook_getSpeechTextForProperties(self, reason=NVDAObjects.controlTypes.OutputReason.QUERY, *args, **kwargs):
		role = kwargs.get('role', None)
		if role:
			if config.conf["unspokenpy3"]["active"] and \
					'role' in kwargs and role in sounds:
				kwargs['_role'] = kwargs['role']
				del kwargs['role']
		return self._NVDA_getSpeechTextForProperties(reason, *args, **kwargs)


	def  showSetting(self, evt):
		dlg= UnspokenSettingDialog(gui.mainFrame)
		dlg.ShowModal()

	def play_object(self, obj):
		global AUDIO_WIDTH, AUDIO_DEPTH
		role = obj.role
		if role in sounds:
			desktop = NVDAObjects.api.getDesktopObject()
			desktop_max_x = desktop.location[2]
			desktop_max_y = desktop.location[3]
			desktop_aspect = float(desktop_max_y) / float(desktop_max_x)
			if obj.location != None:
				obj_x = obj.location[0] + (obj.location[2] / 2.0)
				obj_y = obj.location[1] + (obj.location[3] / 2.0)
			else:
				obj_x = desktop_max_x / 2.0
				obj_y = desktop_max_y / 2.0
			position_x = (obj_x / desktop_max_x) * \
				(AUDIO_WIDTH * 2) - AUDIO_WIDTH
			position_y = (obj_y / desktop_max_y) * (desktop_aspect *
													AUDIO_WIDTH * 2) - (desktop_aspect * AUDIO_WIDTH)
			position_y *= -1
			sounds[role].set_position(position_x, position_y, AUDIO_DEPTH * -1)
			sounds[role].play()

	def event_becomeNavigatorObject(self, obj, nextHandler, isFocus=False):
		if config.conf["unspokenpy3"]["active"]:
			self.play_object(obj)
		else:
			pass
		nextHandler()

	def event_mouseMove(self, obj, nextHandler, x, y):
		if obj != self._previous_mouse_object:
			self._previous_mouse_object = obj
			if config.conf["unspokenpy3"]["active"]:
				self.play_object(obj)
		nextHandler()

	def script_changeActivate(self, gesture):
		if config.conf["unspokenpy3"]["active"]:
			speech.cancelSpeech()
			ui.message(_("Disable Unspoken"))
			config.conf["unspokenpy3"]["active"] = False
		elif config.conf["unspokenpy3"]["active"] == False:
			speech.cancelSpeech()
			ui.message(_("Enable Unspoken"))
			config.conf["unspokenpy3"]["active"] = True
		else:
			pass

	script_changeActivate.__doc__ = _(
		"Changes the active  / deactive  mode of Unspoken.")
	__gestures = {
		"kb:control+shift+u": "changeActivate",
	}

	def terminate(self, *args, **kwargs):
		super().terminate(*args, **kwargs)
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.showSetting, self.unspokenSetting)
