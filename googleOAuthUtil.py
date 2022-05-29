#Google credential manager
#Copyright (C) 2020 guredora <contact@guredora.com>
import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import constants
import errorCodes

import google.auth.transport.requests

def get( fileName, need_refresh=False):
	#ディレクトリがなければ作る
	if not os.path.exists(constants.GOOGLE_DIR):
		os.makedirs(constants.GOOGLE_DIR)

	#ファイルがあれば読み込む
	print(getCredentialPath(fileName))
	if os.path.isfile(getCredentialPath(fileName)):
		print("find")
		try:
			credential=Credentials.from_authorized_user_file(getCredentialPath(fileName),scopes=constants.GOOGLE_NEED_SCOPES)
			print(credential)
			if need_refresh:
				refresh(credential)
			return credential
		except ValueError:
			pass
	return None

def MakeFlow():
	#ディレクトリがなければ作る
	if not os.path.exists(constants.GOOGLE_DIR):
		os.makedirs(constants.GOOGLE_DIR)

	flow = InstalledAppFlow.from_client_config(
		json.loads(constants.GOOGLE_CLIENT_SECRET),
		scopes=constants.GOOGLE_NEED_SCOPES
	)
	url = flow.prepare_run_local_server(
		host='localhost',
		port=8080, 
		authorization_prompt_message='',			#標準出力への表示は不要
		success_message=_("googleでの認証手続きが完了しました。このブラウザを閉じ、処理結果を確認してください。<script>window.close();</script>"),
		open_browser=False
	)
	return flow, url

def getCredential(flow, fileName):
	credential=flow.run_local_server()
	if credential==None:
		return errorCodes.WAITING_USER
	if credential==False:
		return errorCodes.NOT_AUTHORIZED
	try:
		with open(getCredentialPath(fileName), mode="w") as f:
			f.write(credential.to_json())
	except BaseException as e:
		return errorCodes.IO_ERROR
	return errorCodes.OK

def refresh(credential):
	request = google.auth.transport.requests.Request()
	credential.refresh(request)

def Authorize(credential):
	if credential.expired:
		refresh(credential)
	header = {}
	credential.apply(header)
	return header

def getCredentialPath(fileName):
	return os.path.join(constants.GOOGLE_DIR, fileName)
