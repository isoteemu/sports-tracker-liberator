#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyKDE4.kdeui import KWallet
from PyQt4 import QtCore, QtGui

kwallet_folder = "Form Data"

def open_wallet():
	app = QtGui.QApplication([])
	wallet = KWallet.Wallet.openWallet(KWallet.Wallet.LocalWallet(), 0)
	if not wallet.hasFolder(kwallet_folder):
		wallet.createFolder(kwallet_folder)

	wallet.setFolder(kwallet_folder)
	return wallet

def get_auth(wallet):
	data = wallet.readMap('https://www.endomondo.com/access#signInForm')[1]
	email_key = QtCore.QString('email');
	password_key = QtCore.QString('password');

	return (str(data[email_key]),str(data[password_key]))
