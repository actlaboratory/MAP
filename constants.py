# -*- coding: utf-8 -*-
#constant values
#Copyright (C) 20XX anonimous <anonimous@sample.com>

import wx

#アプリケーション基本情報
APP_FULL_NAME = "Mail Authorization Proxy"#アプリケーションの完全な名前
APP_NAME="MAP"#アプリケーションの名前
APP_ICON = None
APP_VERSION="0.1.0"
APP_LAST_RELEASE_DATE="2022-05-31"
APP_COPYRIGHT_YEAR="2022"
APP_LICENSE="MIT License"
APP_DEVELOPERS="yamahubuki, ACT Laboratory"
APP_DEVELOPERS_URL="https://actlab.org/"
APP_DETAILS_URL="https://actlab.org/software/MAP"
APP_COPYRIGHT_MESSAGE = "Copyright (c) %s %s All lights reserved." % (APP_COPYRIGHT_YEAR, APP_DEVELOPERS)

SUPPORTING_LANGUAGE={"ja-JP": "日本語","en-US": "English"}

#各種ファイル名
LOG_PREFIX="app"
LOG_FILE_NAME="map.log"
SETTING_FILE_NAME="settings.ini"
KEYMAP_FILE_NAME="keymap.ini"



#フォントの設定可能サイズ範囲
FONT_MIN_SIZE=5
FONT_MAX_SIZE=35

#３ステートチェックボックスの状態定数
NOT_CHECKED=wx.CHK_UNCHECKED
HALF_CHECKED=wx.CHK_UNDETERMINED
FULL_CHECKED=wx.CHK_CHECKED

#build関連定数
BASE_PACKAGE_URL = "https://github.com/actlaboratory/MAP/releases/download/0.1.0/MAP-0.1.0.zip"
PACKAGE_CONTAIN_ITEMS = ()#パッケージに含めたいファイルやfolderがあれば指定
NEED_HOOKS = ()#pyinstallerのhookを追加したい場合は指定
STARTUP_FILE = "MAP.py"#起動用ファイルを指定
UPDATER_URL = "https://github.com/actlaboratory/updater/releases/download/1.0.0/updater.zip"

# update情報
UPDATE_URL = "https://actlab.org/api/checkUpdate"
UPDATER_VERSION = "1.0.0"
UPDATER_WAKE_WORD = "hello"


#google認証関連
GOOGLE_DIR = ".credential"
GOOGLE_FILE_NAME = "credential.json"
GOOGLE_CLIENT_ID = "893602291074-2te09ggtgd8gnvra4ilt7q28h87nofna.apps.googleusercontent.com"
GOOGLE_NEED_SCOPES = ['https://mail.google.com/']
GOOGLE_CALLBACK_URL = "http://localhost:8088"
GOOGLE_CLIENT_SECRET = '{"installed":{"client_id":"893602291074-2te09ggtgd8gnvra4ilt7q28h87nofna.apps.googleusercontent.com","project_id":"actlab-map","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"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","redirect_uris":["urn:ietf:wg:oauth:2.0:oob","http://localhost"]}}'
GOOGLE_CLIENT_SECRET_STR = "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"


PIPE_NAME= "actlab_map"
