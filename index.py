import email
import imapclient.exceptions
from imapclient import IMAPClient
from flask import Flask, render_template, jsonify, request
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# FLASK
app = Flask(__name__)

mails = {}
contacts = {}

host = 'imap.gmail.com'


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/fetch_mails', methods=['GET'])
def fetch_mails():
    mails_arr = []
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
            server = IMAPClient(host=host, use_uid=True)
            mails[str(request.form['mail'])] = str(request.form['password'])
            contacts[str(request.form['mail'])] = []
            server.login(str(request.form['mail']), str(request.form['password']))
            server.logout()
            return jsonify(status=204)
        else:
            return jsonify(status=409)

    except imapclient.exceptions.LoginError:
        print("ERROR")
        del mails[request.form['mail']]
        return jsonify(status=500)


@app.route("/delete_mail", methods=['POST'])
def delete_mail():
    del mails[request.form['mail']]
    return jsonify(status=204)


@app.route("/get_inbox", methods=['POST'])
def get_inbox():
    mail = request.form['mail']
    password = mails.get(mail)
    mails_inbox = {}
    try:
        server = IMAPClient(host=host, use_uid=True)
        server.login(str(mail), str(password))
        server.select_folder(request.form['folder'])
        messages = server.search('ALL')
        index = 0
        for uid, message_data in server.fetch(messages, 'RFC822').items():
            email_message = email.message_from_bytes(message_data[b'RFC822'])
            if email_message.is_multipart():
                for part in email_message.get_payload():
                    mails_inbox[index] = {
                        "from": email_message.get("From"),
                        "subject": email_message.get("Subject"),
                        "payload": part.get_payload()
                    }
            index += 1
        return jsonify(status=200, mails=mails_inbox)

    except imapclient.exceptions.LoginError:
        print("ERROR")
        del mails[request.form['mail']]
        return jsonify(status=500)


@app.route("/fetch_contacts", methods=['POST'])
def fetch_contacts():
    contacts_arr = []
    if len(contacts[request.form['mail']]) > 0:
        print("Hay contactos")
        for contact in contacts[request.form['mail']]:
            contacts_arr.append(contact)
        print(contacts_arr)
        return jsonify(status=200, contacts=contacts_arr)
    else:
        print("No hay contactos")
        return jsonify(status=404)


@app.route("/add_contact", methods=['POST'])
def add_contact():
    if request.form['contact'] not in contacts[request.form['mail']]:
        contacts[request.form['mail']].append(request.form['contact'])
        print(contacts)
        return jsonify(status=204)
    else:
        return jsonify(status=404)


@app.route("/send_mail", methods=['POST'])
def send_mail():
    user = request.form['from']
    to = request.form['to']
    subject = request.form['subject']
    body = request.form['body']

    msg = MIMEMultipart()

    msg['From'], msg['to'], msg['subject'] = user, to, subject
    body = MIMEText(body)

    msg.attach(body)

    server = smtplib.SMTP('smtp.gmail.com: 587')
    server.starttls()
    server.login(user, mails[user])

    server.sendmail(msg["From"], msg["to"], msg.as_string())
    server.quit()
    return jsonify(status=204)


app.run()
