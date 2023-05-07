from flask import render_template, request, url_for, redirect

from utils import get_info, reset_errors
from query_objects.artist import Artist
from query_objects.fan import Fan

def artists(conn, session, artist_id):
    get_info(conn)
    user = session.get('username')
    errors = reset_errors()

    data = Artist(conn).by_id().with_albums().retrieve(inpt=[artist_id], method='fetchall')['data']
    if not data:
        session['errors'] = ['Artist not found.']
        return redirect('/')

    is_fan = Fan(conn).is_fan(user, artist_id)
    print(is_fan)
    return render_template('artist.html', user=user, artist=data[0], albums=data, is_fan=is_fan, errors=errors)

def select_artist(conn, session):
    user = session.get('username')

    if not user:
        session['errors'] = ['You must be logged in to create new music.']
        return redirect('/browse')

    if request.method == 'GET':
        artists = Artist(conn).retrieve(method='fetchall')['data']
        return render_template('select_artist.html', user=user, artists=artists)

    if request.method == 'POST':
        if request.form['artist_id'] and request.form['artist_id'] != '0':
            return redirect(url_for('new_song', artist_id=request.form['artist_id']))

        result = Artist(conn).create(request.form)
        if not result['SUCCESS']:
            return render_template('select_artist.html', errors=result['errors'])
        elif result['data'] is not None and result['data']['artist_id']:
            return redirect(url_for('new_song', artist_id=result['data']['artist_id']))

        return render_template('select_artist.html', errors=['The request could not be completed'])


def fan(conn, session):
    user = session.get('username')
    form = request.form

    if not user:
        session['errors'] = ['Log in to follow artists']
        return redirect(url_for('artists', artist_id=form['artist_id']))

    result = Fan(conn).create(form)

    if not result['SUCCESS']:
        session['errors'] = result['errors']

    return redirect(url_for('artists', artist_id=form['artist_id']))