import json

import imapclient.exceptions
from imapclient import IMAPClient
from flask import Flask, render_template, jsonify, request

#FLASK
app = Flask(__name__)

mails = {}

@app.route('/')
def index():
    return render_template("index.html")


@app.route('/fetch_mails', methods=['GET'])
def fetch_mails():
    mails_arr = []
    print(len(mails))
    if len(mails) > 0:
        for mail in mails:
            mails_arr.append(mail)
        print(mails_arr)
        return jsonify(status=200, mails=mails_arr)
    else:
        return jsonify(status=404)

@app.route('/login', methods=['POST'])
def login():
    try:
        if mails.get(str(request.form['mail'])) is None:
            host = 'imap.gmail.com'
            server = IMAPClient(host=host, use_uid=True)
            mails[str(request.form['mail'])] = str(request.form['password'])
            server.login(str(request.form['mail']), str(request.form['password']))
            server.logout()
            return jsonify(status=204)
        else:
            return jsonify(status=409)

    except imapclient.exceptions.LoginError:
        print("ERROR")
        del mails[request.form['mail']]
        return jsonify(status=500)


@app.route("/delete_mail", methods = ['POST'])
def delete_mail():
    del mails[request.form['mail']]
    return jsonify(status=204)

app.run()