from flask import render_template, request, redirect, url_for

from utils import reset_errors
from query_objects.user import User


def home(conn, session):
    user = session.get('username')
    errors = reset_errors()

    if user:
        feed = User(conn).feed_query(user)
        errors.extend(feed['errors'])
        return render_template('home.html', feed=feed['data'], user=user, errors=errors)
    else:
        return redirect('/browse')


def people(conn, session):
    user = session.get('username')
    errors = reset_errors()

    if user:
        follows = User(conn).follows(user)
        friend_requests = User(conn).friend_requests(user)
        friends = User(conn).friends(user)
        return render_template(
            'people.html',
            follows=follows,
            friend_requests=friend_requests,
            friends=friends,
            user=user,
            errors=errors
        )
    else:
        return redirect('/browse')


def friend_request(conn, session):
    user = session.get('username')

    if user:
        form = request.form
        result = {'SUCCESS': False}
        if form['f_request'] == 'Accept' and form['friend']:
            result = User(conn).accept_friend_request(user, form['friend'])
        elif form['f_request'] == 'Reject' and form['friend']:
            result = User(conn).remove_friend_request(user, form['friend'])
        elif form['f_request'] == 'Send Friend Request' and form['friend']:
            if user == form['friend']:
                result = {'SUCCESS': False, 'errors': ['Cannot send a friend request to yourself'], 'data': None}
            else:
                result = User(conn).create_friend_request(user, form['friend'])

        if not result['SUCCESS']:
            session['errors'] = result['errors']

        if form['f_request'] == 'Send Friend Request':
            return redirect(url_for('profile', username=form['friend']))

        return redirect('/people')
    else:
        session['errors'] = ['Log in to send friend requests']
        return redirect('/browse')


def follow(conn, session):
    user = session.get('username')

    if user:
        form = request.form
        result = User(conn).follow(user, form['friend'])

        if not result['SUCCESS']:
            session['errors'] = result['errors']

        return redirect(url_for('profile', username=form['friend']))
    else:
        session['errors'] = ['Log in to follow other uers']
        return redirect('/browse')


def profile(conn, session, username):
    user = session.get('username')
    errors=reset_errors()

    if user:
        observed_user = User(conn).by_id().retrieve(inpt=[username], method='fetchone')['data']
        is_friend = User(conn).is_friend(user, username)
        following = User(conn).following(user, username)
        return render_template(
            'profile.html',
            user=user,
            observed_user=observed_user,
            is_friend=is_friend,
            following=following,
            errors=errors
        )
    else:
        return redirect('/browse')