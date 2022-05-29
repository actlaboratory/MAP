# Taskbar Icon

import base64
import wx
import wx.adv

import constants
import globalVars
import views.icon_data

from io import BytesIO

from views.base import BaseMenu


class TaskbarIcon(wx.adv.TaskBarIcon):
	def __init__(self):
		super().__init__()

		data = base64.b64decode(views.icon_data.ICON_DATA)
		bitmap = wx.Image(BytesIO(data)).ConvertToBitmap()
		self.icon = wx.Icon()
		self.icon.CopyFromBitmap(bitmap)
		self.SetIcon(self.icon, constants.APP_NAME)
		self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.onDoubleClick)
		self.Bind(wx.adv.EVT_TASKBAR_LEFT_DCLICK, self.onDoubleClick)


	def CreatePopupMenu(self):
		bm = BaseMenu("mainView")
		menu = wx.Menu()
		menu.Bind(wx.EVT_MENU, globalVars.app.hMainView.events.OnMenuSelect)
		menu.Bind(wx.EVT_MENU_OPEN, globalVars.app.hMainView.events.onMenuOpen)
		bm.RegisterMenuCommand(menu, [
			"SHOW",
			"",
			"START",
			"STOP",
			"",
			"EXIT",
		])
		return menu

	def onDoubleClick(self, event):
		globalVars.app.hMainView.events.show()

	def setAlternateText(self, text=""):
		"""タスクバーアイコンに表示するテキストを変更する。「アプリ名 - 指定したテキスト」の形になる。

		:param text: アプリ名に続けて表示するテキスト
		:type text: str
		"""
		if text != "":
			text = " - " + text
		self.SetIcon(self.icon, constants.APP_NAME + text)
