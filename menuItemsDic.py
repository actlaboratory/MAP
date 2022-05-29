
import re

def getValueString(ref_id):
	""" ナビキーとダイアログ文字列を消去した文字列を取り出し """
	dicVal = dic[ref_id]
	s = re.sub("\.\.\.$", "", dicVal)
	s = re.sub("\(&.\)$", "", s)
	return re.sub("&", "", s)

dic={
	"FILE_AUTH":_("アカウントを追加(&A)"),

	"OPTION_OPTION":_("オプション(&O)")+"...",
	"OPTION_KEY_CONFIG":_("ショートカットキーの設定(&K)")+"...",
	"OPTION_AUTO_STARTUP":_("Windows起動時の自動起動を有効化(&W)"),

	"HELP_UPDATE":_("最新バージョンを確認(&U)")+"...",
	"HELP_VERSIONINFO":_("バージョン情報(&V)")+"...",

	# タスクトレイ項目
	"START":_("起動(&R)"),
	"STOP":_("停止(&S)"),
	"SHOW":_("メインウィンドウを開く(&O)"),
	"HIDE":_("メインウィンドウを隠す(&H)"),
	"EXIT":_("終了(&X)"),
}
