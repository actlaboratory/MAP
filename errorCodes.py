﻿# -*- coding: utf-8 -*-
#error codes

OK=0				#成功(エラーなし)
NOT_SUPPORTED=1		#サポートされていない呼び出し
FILE_NOT_FOUND=2
PARSING_FAILED=3
ACCESS_DENIED=4
CANCELED_BY_USER=5
WAITING_USER=6		#ユーザの操作待ち
GOOGLE_ERROR=7
NOT_AUTHORIZED=8#グーグルで認証していない
IO_ERROR=9

#アップデータ関連
CONNECT_TIMEOUT = 12
UPDATER_NEED_UPDATE = 200	# アップデートが必要
UPDATER_LATEST = 204		# アップデートが無い
UPDATER_VISIT_SITE = 205	# ブラウザでのサイトアクセス要求
UPDATER_BAD_PARAM = 400		# パラメーターが不正
UPDATER_NOT_FOUND = 404		# アプリケーションが存在しない
UNKNOWN=99999
