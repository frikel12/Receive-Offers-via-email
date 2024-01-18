from flask import render_template, url_for, request, redirect, session
import MySQLdb.cursors
import re
import MySQLdb
from config import app

app.secret_key='youssefrikel12'

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'db': 'webscraping',
}


@app.route('/')
def index():
    return render_template('base.html')


def connect_to_database():
    return MySQLdb.connect(**db_config)


def close_database_connection(connection, cursor):
    cursor.close()
    connection.close()


@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        connection = connect_to_database()
        cursor = connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s AND password = %s', (email, password,))
        user = cursor.fetchone()

        close_database_connection(connection, cursor)

        if user:
            session['loggedin'] = True
            session['id'] = user['id']
            session['email'] = user['email']
            return redirect(url_for('keywords'))
        else:
            msg = 'Incorrect email / password!'

    return render_template('login.html', msg=msg)


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        email = request.form['email']
        password = request.form['password']
        confirmpass = request.form['confirmpass']

        connection = connect_to_database()
        cursor = connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        account = cursor.fetchone()

        if not email or not password or not nom or not prenom:
            msg = 'Remplir tous les champs!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Adresse email non valide!'
        elif password != confirmpass:
            msg = 'les deux mots de pass ne sont pas identiques'
        elif account:
            msg = 'Compte déjà existant!'
        else:
            cursor.execute('INSERT INTO users(nom, prenom, email, password) VALUES (%s, %s, %s, %s)',
                           (nom, prenom, email, password))
            connection.commit()
            msg = 'INSCRIPTION REUSSI'

        close_database_connection(connection, cursor)

    return render_template('register.html', msg=msg)


@app.route('/user/keywords', methods=['GET', 'POST'])
def keywords():

    connection = connect_to_database()
    cursor = connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(f"SELECT * FROM keywords where user_id = {session['id']}")
    data = cursor.fetchall()

    cursor.execute(f"SELECT receive_email FROM users where id = {session['id']}")
    msg = cursor.fetchone()
    close_database_connection(connection, cursor)

    return render_template('keywords.html', data=data, msg=msg)


@app.route('/user/keywords/addkeyword', methods=['GET', 'POST'])
def addkeyword():
    if request.method == 'POST':
        keyword = request.form['keyword']
        if keyword:
            connection = connect_to_database()
            cursor = connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('INSERT INTO keywords(name, user_id) VALUES (%s, %s)',
                           (keyword, session['id']))
            connection.commit()
            close_database_connection(connection, cursor)
    return redirect(url_for('keywords'))


@app.route('/user/keywords/delete/<id>')
def deletekeyword(id):
    connection = connect_to_database()
    cursor = connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(f"DELETE FROM keywords where id = {id}")
    connection.commit()
    close_database_connection(connection, cursor)

    return redirect(url_for('keywords'))


@app.route('/user/keywords/receivemail', methods=['GET', 'POST'])
def receivemail():
    if request.method == 'POST':
        connection = connect_to_database()
        cursor = connection.cursor(MySQLdb.cursors.DictCursor)

        cursor.execute(f"SELECT * FROM users WHERE id = {session['id']}")
        account = cursor.fetchone()
        if account['receive_email'] == 0:
            cursor.execute(f"UPDATE users SET receive_email=1 WHERE id={session['id']}")
        else:
            cursor.execute(f"UPDATE users SET receive_email=0 WHERE id={session['id']}")

        connection.commit()
        close_database_connection(connection, cursor)

    return redirect(url_for('keywords'))


####################################################################################
## email configuration ##

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from data.data import get_data, get_keywords, get_top10, get_email_by_id
from flask_mail import Mail, Message
from config import mail


def sendoffers2():
    with app.app_context():
        posts = get_data()
        keywords = get_keywords()
        similarity = get_top10(posts, keywords)
        sender = 'yousseffrikel7@gmail.com'
        for k, v in similarity.items():
            receiver = get_email_by_id(k)
            send_email(sender, receiver, data=v)

        print("email sent")


def send_email(sender, receiver, data):
    send = sender
    receive = receiver
    mail_message = Message(
        'Nouveaux Offres',
        sender=send,
        recipients=[receive])
    # mail_message.body = "This is a test"
    mail_message.html = render_template("email.html", data=data)
    mail.send(mail_message)


scheduler = BackgroundScheduler()

# Schedule the cron job to run every day at 9:30 AM
scheduler.add_job(
    func=sendoffers2,
    trigger=CronTrigger(hour=21, minute=42),
)

# Start the scheduler
scheduler.start()


if __name__ == "__main__":
    app.run(debug=True, port=5123)





