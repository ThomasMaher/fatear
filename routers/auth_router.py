from flask import render_template, request, url_for, redirect
import bcrypt
import utils

def register(conn, session):
    return render_template('register.html')

def loginAuth(conn, session):
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM users WHERE username = %s'
    cursor.execute(query, (username))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    result = None
    try:
        result = bcrypt.checkpw(password.encode('utf-8'), data['password'].encode('utf-8'))
    except:
        error = 'Invalid login or username'

    if(data and result):
        # Clear the session because we want to reset the cache at this point
        utils.empty_session_lists()
        session['username'] = username
        return redirect('/')
    else:
        # returns an error message to the html page
        if not error:
            error = 'Invalid login or username'
        return render_template('login.html', error=error, user=None)


def registerAuth(conn, session):
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM users WHERE username = %s'
    cursor.execute(query, (username))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error, user=None)
    else:
        salt = bcrypt.gensalt()
        pw = bcrypt.hashpw(password.encode('utf-8'), salt)
        ins = 'INSERT INTO users (username, password) VALUES(%s, %s)'
        cursor.execute(ins, (username, pw))
        conn.commit()
        cursor.close()

        # Clear the session because we want to reset the cache at this point
        utils.empty_session_lists()
        session['username'] = username
        return redirect('/')