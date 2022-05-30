# -*- coding: utf-8 -*-
#main view
#Copyright (C) 2019 Yukio Nozawa <personal@nyanchangames.com>
#Copyright (C) 2019-2021 yamahubuki <itiro.ishino@gmail.com>

import os
import wx

import constants
import globalVars
import update
import menuItemsStore

from .base import *
from simpleDialog import *

from views import AuthorizeDialog
from views import globalKeyConfig
from views import settingsDialog
from views import SimpleInputDialog
from views import versionDialog

class MainView(BaseView):
	def __init__(self):
		super().__init__("mainView")
		self.log.debug("created")
		self.events=Events(self,self.identifier)
		title=constants.APP_NAME
		super().Initialize(
			title,
			self.app.config.getint(self.identifier,"sizeX",800,400),
			self.app.config.getint(self.identifier,"sizeY",600,300),
			self.app.config.getint(self.identifier,"positionX",50,0),
			self.app.config.getint(self.identifier,"positionY",50,0)
		)
		self.InstallMenuEvent(Menu(self.identifier),self.events.OnMenuSelect)
		self.hFrame.Bind(wx.EVT_MENU_OPEN, self.events.onMenuOpen)

class Menu(BaseMenu):
	def Apply(self,target):
		"""指定されたウィンドウに、メニューを適用する。"""
		events = self.parent.events

		#メニュー内容をいったんクリア
		self.hMenuBar=wx.MenuBar()

		#メニューの大項目を作る
		self.hFileMenu=wx.Menu()
		self.hOptionMenu=wx.Menu()
		self.hHelpMenu=wx.Menu()

		#ファイルメニュー
		self.RegisterMenuCommand(self.hFileMenu,{
			"START": self.parent.app.startServer,
			"STOP": self.parent.app.stopServer,
			"FILE_AUTH": events.auth,
			"SHOW": events.show,
			"HIDE": events.hide,
			"EXIT": events.close,
		})

		#オプションメニュー
		self.RegisterMenuCommand(self.hOptionMenu,{
			"OPTION_OPTION": events.option,
			"OPTION_KEY_CONFIG": events.keyConfig,
			"OPTION_AUTO_STARTUP": events.registerStartup,
		})

		#ヘルプメニュー
		self.RegisterMenuCommand(self.hHelpMenu,{
			"HELP_UPDATE": events.checkUpdate,
			"HELP_VERSIONINFO": events.version,
		})

		#メニューバーの生成
		self.hMenuBar.Append(self.hFileMenu,_("ファイル(&F))"))
		self.hMenuBar.Append(self.hOptionMenu,_("オプション(&O)"))
		self.hMenuBar.Append(self.hHelpMenu,_("ヘルプ(&H)"))
		target.SetMenuBar(self.hMenuBar)

class Events(BaseEvents):
	#メインウィンドウ表示
	def show(self,event=None):
		self.parent.hFrame.Show()
		self.parent.hPanel.SetFocus()

	def option(self,event):
		d = settingsDialog.Dialog()
		d.Initialize()
		d.Show()

	def keyConfig(self,event):
		if self.setKeymap(self.parent.identifier,_("ショートカットキーの設定"),filter=keymap.KeyFilter().SetDefault(False,False)):
			#ショートカットキーの変更適用とメニューバーの再描画
			self.parent.menu.InitShortcut()
			self.parent.menu.ApplyShortcut(self.parent.hFrame)
			self.parent.menu.Apply(self.parent.hFrame)

	def checkUpdate(self,event):
		update.checkUpdate()

	def version(self,event):
		d = versionDialog.dialog()
		d.Initialize()
		r = d.Show()

	def close(self,event):
		self.parent.hFrame.Close(True)

	def OnExit(self, event):
		if event.CanVeto():
			# Alt+F4が押された
			if globalVars.app.config.getboolean("general", "minimizeOnExit", True) and globalVars.runnerThread.isRunning:
				# 設定ONかつ起動中なら最小化のみ
				self.hide()
				return

		globalVars.app.tb.Destroy()

		# ソフトウェア終了
		super().OnExit(event)

	def hide(self, event=None):
		self.parent.hFrame.Hide()

	def setKeymap(self, identifier,ttl, keymap=None,filter=None):
		if keymap:
			try:
				keys=keymap.map[identifier.upper()]
			except KeyError:
				keys={}
		else:
			try:
				keys=self.parent.menu.keymap.map[identifier.upper()]
			except KeyError:
				keys={}
		keyData={}
		menuData={}
		for refName in defaultKeymap.defaultKeymap[identifier].keys():
			title=menuItemsDic.getValueString(refName)
			if refName in keys:
				keyData[title]=keys[refName]
			else:
				keyData[title]=_("なし")
			menuData[title]=refName

		d=globalKeyConfig.Dialog(keyData,menuData,[],filter)
		d.Initialize(ttl)
		if d.Show()==wx.ID_CANCEL: return False

		keyData,menuData=d.GetValue()

		#キーマップの既存設定を置き換える
		newMap=ConfigManager.ConfigManager()
		newMap.read(constants.KEYMAP_FILE_NAME)
		for name,key in keyData.items():
			if key!=_("なし"):
				newMap[identifier.upper()][menuData[name]]=key
			else:
				newMap[identifier.upper()][menuData[name]]=""
		newMap.write()
		return True

	def auth(self,event):
		d = SimpleInputDialog.Dialog(
				_("メールアドレスの入力"),
				_("Gmailのサーバを通じて送受信したいメールアドレスを入力してください。\nなお、最新モードで受信したい場合であっても、ここでrecent:をつけて入力しないでください。"),
				self.parent.hFrame,
				"^(([a-zA-Z0-9][._\\-?+]?)+[a-zA-Z0-9]@([a-zA-Z0-9][._\\-?+]?)+[a-zA-Z0-9]\\.[a-zA-Z0-9]+)$"
			)
		d.Initialize()
		d.Show()

		authorizeDialog = AuthorizeDialog.Dialog(d.GetValue())
		authorizeDialog.Initialize()
		status = authorizeDialog.Show()

		if status==errorCodes.OK:
			dialog(_("認証結果"),_("認証に成功しました。"), self.parent.hFrame)
		elif status == errorCodes.CANCELED_BY_USER:
			dialog(_("認証結果"),_("キャンセルしました。"), self.parent.hFrame)
		elif status==errorCodes.IO_ERROR:
			dialog(_("認証結果"),_("認証に成功しましたが、ファイルの保存に失敗しました。ディレクトリのアクセス権限などを確認してください。"),self.parent.hFrame)
		elif status==errorCodes.CANCELED:
			dialog(_("認証結果"),_("ブラウザが閉じられたため、認証をキャンセルしました。"),self.parent.hFrame)
		elif status==errorCodes.NOT_AUTHORIZED:
			dialog(_("認証結果"),_("認証が拒否されました。"),self.parent.hFrame)
		else:
			dialog(_("エラー"),_("不明なエラーが発生しました。"),self.parent.hFrame)
		return

	def registerStartup(self, event):
		target = os.path.join(
			os.environ["appdata"],
			"Microsoft",
			"Windows",
			"Start Menu",
			"Programs",
			"Startup",
			"%s.lnk" %constants.APP_NAME
		)
		if os.path.exists(target):
			d = yesNoDialog(_("確認"), _("Windows起動時の自動起動はすでに設定されています。設定を解除しますか？"))
			if d == wx.ID_YES:
				os.remove(target)
				dialog(_("完了"), _("Windows起動時の自動起動を無効化しました。"))
			return
		ws = win32com.client.Dispatch("wscript.shell")
		shortCut = ws.CreateShortcut(target)
		shortCut.TargetPath = globalVars.app.getAppPath()
		shortCut.Save()
		dialog(_("完了"), _("Windows起動時の自動起動を設定しました。"))

	def onMenuOpen(self, event):
		menu = event.GetMenu()
		if not menu:
			event.Skip()
		for item in menu.GetMenuItems():
			if item.GetId()	 == menuItemsStore.getRef("START"):
				item.Enable(not globalVars.runnerThread.isRunning)
			if item.GetId() == menuItemsStore.getRef("STOP"):
				item.Enable(globalVars.runnerThread.isRunning)
			if item.GetId() == menuItemsStore.getRef("SHOW"):
				item.Enable(not self.parent.hFrame.IsShown())
			if item.GetId() == menuItemsStore.getRef("HIDE"):
				item.Enable(self.parent.hFrame.IsShown())
		event.Skip()
