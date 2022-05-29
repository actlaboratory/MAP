# -*- coding: utf-8 -*-
# authorize dialog


import threading
import webbrowser
import wx

import errorCodes
import globalVars
import googleOAuthUtil
import views.ViewCreator

from views.baseDialog import *


class Dialog(BaseDialog):
	def __init__(self, fileName):
		super().__init__("authorizeDialog")
		self.web, self.pid = None, None
		self.authThread = None
		self.__isArrive = True
		self.__authStarted = False
		self.fileName = fileName

	def Initialize(self):
		super().Initialize(self.app.hMainView.hFrame,_("Googleアカウント認証"))
		self.InstallControls()
		return True

	def InstallControls(self):
		"""いろんなwidgetを設置する。"""

		self.creator=views.ViewCreator.ViewCreator(self.viewMode,self.panel,self.sizer,wx.VERTICAL, 20)
		self.static = self.creator.staticText(_("ブラウザを開いて認証手続きを行います。\r\nよろしいですか？"),wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_MIDDLE,-1,wx.ALIGN_LEFT)

		self.buttonCreator=views.ViewCreator.ViewCreator(self.viewMode,self.panel,self.sizer,wx.HORIZONTAL,20, style=wx.ALIGN_RIGHT)
		self.bStart=self.buttonCreator.okbutton(_("開始(&S)"), self.authorize)
		self.bCancel=self.buttonCreator.cancelbutton(_("キャンセル(&C)"), self.canceled)

	def authorize(self,evt):
		if self.__authStarted:
			self.wnd.EndModal(errorCodes.OK)
			return
		self.__authStarted = True
		self.static.SetLabel(_("認証を待機中..."))
		self.bStart.Disable()

		#認証プロセスの開始、認証用URL取得
		self.flow, url = googleOAuthUtil.MakeFlow()
		#ブラウザの表示
		globalVars.app.say(_("ブラウザを開いています..."))
		webbrowser.open(url)

		self.authThread = threading.Thread(target=self.__auth)
		self.authThread.start()

	def __auth(self):
		#ユーザの認証待ち
		status=errorCodes.WAITING_USER
		evt=threading.Event()
		while(status==errorCodes.WAITING_USER):
			if not self.__isArrive: return
			if status==errorCodes.WAITING_USER:
				status = googleOAuthUtil.getCredential(self.flow, self.fileName)
				if status == errorCodes.OK:
					wx.CallAfter(self.authOk)
					return
			wx.YieldIfNeeded()
			evt.wait(0.1)
		wx.CallAfter(self.wnd.EndModal, status)
	
	def canceled(self, events):
		self.__isArrive = False
		self.wnd.EndModal(errorCodes.CANCELED_BY_USER)


	def authOk(self):
		globalVars.app.say(_("認証が完了しました。ブラウザを閉じてください。"))
		if self.web != None and self.pid != None and self.web.Exists(self.pid): wx.Process.Kill(self.pid,wx.SIGTERM) # ブラウザの修了要請
		self.static.SetLabel(_("認証が完了しました。"))
		self.bCancel.Disable()
		self.bStart.SetLabel(_("完了(&F)"))
		self.bStart.Enable()
