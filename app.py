# -*- coding: utf-8 -*-
#Application Main

import sys
import threading
import win32api
import win32event
import winerror

import AppBase
import constants
import globalVars

import pipe
import proxyUtil
import update

class Main(AppBase.MainBase):
	def __init__(self):
		super().__init__()

	def OnInit(self):
		#多重起動防止
		globalVars.mutex = win32event.CreateMutex(None, 1, constants.APP_FULL_NAME)
		if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
			globalVars.mutex = None
			pipe.sendPipe()
			return False
		else:
			pipe.startServer()
			return True

	def initialize(self):
		self.setGlobalVars()

		# プロキシの設定を適用
		self.proxyEnviron = proxyUtil.virtualProxyEnviron()
		self.setProxyEnviron()

		# スレッドで例外が起きてもsys.exceptHookが呼ばれるようにする
		self.installThreadExcepthook()

		# アップデートを実行
		if self.config.getboolean("general", "update"):
			globalVars.update.update(True)

		# start daemon
		self.startRunner()

		# メインビュー
		from views import main
		self.hMainView=main.MainView()

		# タスクバーアイコンの準備
		import views.tbIcon
		self.tb = views.tbIcon.TaskbarIcon()

		#自動起動or画面の表示
		if self.config.getboolean("general","auto_start_server",False):
			self.startServer()
		else:
			self.hMainView.Show()
		return True

	def setProxyEnviron(self):
		if self.config.getboolean("proxy", "usemanualsetting", False) == True:
			self.proxyEnviron.set_environ(self.config["proxy"]["server"], self.config.getint("proxy", "port", 8080, 0, 65535))
		else:
			self.proxyEnviron.set_environ()

	def setGlobalVars(self):
		globalVars.update = update.update()

	def installThreadExcepthook(self):
		_init = threading.Thread.__init__

		def init(self, *args, **kwargs):
			_init(self, *args, **kwargs)
			_run = self.run

			def run(*args, **kwargs):
				try:
					_run(*args, **kwargs)
				except:
					sys.excepthook(*sys.exc_info())
			self.run = run

		threading.Thread.__init__ = init

	def OnExit(self):
		#設定の保存やリソースの開放など、終了前に行いたい処理があれば記述できる
		#ビューへのアクセスや終了の抑制はできないので注意。

		self._releaseMutex()
		pipe.stopServer()

		self.stopRunner()

		# アップデート
		globalVars.update.runUpdate()

		#戻り値は無視される
		return 0

	def _releaseMutex(self):
		if globalVars.mutex != None:
			try: win32event.ReleaseMutex(globalVars.mutex)
			except Exception as e:
				return
			globalVars.mutex = None
			self.log.info("mutex object released.")

	def startRunner(self):
		"""
			ソフト開始時の起動処理
		"""
		import runner
		globalVars.event = threading.Event()
		globalVars.runnerThread = runner.O2popRunner()
		globalVars.runnerThread.start()

	def startServer(self, event=None):
		globalVars.event.set()

	def stopServer(self, event=None):
		import o2pop
		o2pop.task_cancel(globalVars.loop, globalVars.task)

	def stopRunner(self):
		"""
			ソフト終了時の停止処理
		"""
		import o2pop
		globalVars.runnerThread.exitFlag = True
		if globalVars.runnerThread.isRunning:
			o2pop.task_cancel(globalVars.loop, globalVars.task)
		else:
			globalVars.event.set()
		globalVars.runnerThread.join()


	def __del__(self):
		self._releaseMutex()
		pipe.stopServer()

