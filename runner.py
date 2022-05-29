# -*- coding: utf-8 -*-
# o2pop runner
#Copyright (C) 2022 yamahubuki <itiro.ishino@gmail.com>

import threading

import globalVars
import o2pop


class O2popRunner(threading.Thread):
	def __init__(self):
		self.exitFlag = False
		self.isRunning = False
		super().__init__()

	def run(self):
		while True:
			globalVars.event.wait()
			if self.exitFlag:
				break

			self.isRunning = True
			o2pop.run_main(o2pop.main(self))
			self.isRunning = False

			if self.exitFlag:
				break

			globalVars.event.clear()
