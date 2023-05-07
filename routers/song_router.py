from flask import render_template, request, url_for, redirect

from utils import get_info, reset_errors, rating_vals, empty_session_lists
from query_objects.song import Song
from query_objects.artist import Artist
from query_objects.genre import Genre
from query_objects.album import Album
from query_objects.song_rating import SongRating
from query_objects.song_review import SongReview


def song(conn, session, song_id):
    get_info(conn)
    errors = reset_errors()
    user = session.get('username')

    song = Song(conn).by_id()
    song_data = song.retrieve(inpt=[song_id])['data']

    if not song_data:
        session['errors'] = ['Song not found.']
        return redirect('/')

    song.with_artists().select(['artist_name', 'artists.artist_url', 'artists.artist_id']).group_by('artists.artist_id')
    artists = song.retrieve(inpt=[song_id], method='fetchall')['data']

    albums = Album(conn).with_songs().where('track.song_id = %s').group_by('albums.album_id').select('albums.*')
    albums = albums.retrieve(inpt=[song_id], method='fetchall')['data']

    genres = Genre(conn).where('song_id = %s').genre_list().retrieve(inpt=[song_id], method='fetchall')['data']

    average_rating = SongRating(conn).average_for(song_id)
    average_rating = 0 if average_rating is None else round(average_rating, 1)

    my_rating = SongRating(conn).where('song_id = %s AND username = %s')
    my_rating = my_rating.retrieve(inpt=[song_id, user], method='fetchone')['data']
    if not my_rating:
        my_rating = {'stars': 0}

    reviews = SongReview(conn).where('song_id = %s').order_by('review_date').set_direction('DESC')
    reviews = reviews.retrieve(inpt=[song_id], method='fetchall')['data']

    return render_template(
        'song.html',
        song_data=song_data,
        average_rating=average_rating,
        artists=artists,
        genres=genres,
        albums=albums,
        rating_vals=rating_vals(my_rating.get('stars')),
        reviews=reviews,
        user=user,
        errors=errors
    )

def song_rating(conn, session, song_id):
    user = session.get('username')

    if not user:
        session['errors'] = ['Log in to rate a song']
        return redirect(url_for('song', song_id=song_id))

    song = Song(conn).by_id().retrieve(inpt=[song_id])['data']
    if not song:
        session['errors'] = ['The song does not exist.']
        return redirect('/')

    if not request.form.get('stars'):
        session['errors'] = ['No rating was selected.']
        return redirect(url_for('song', song_id=song_id))

    existing_rating = SongRating(conn).where('username = %s AND song_id = %s').retrieve(inpt=[user, song_id])['data']
    if existing_rating:
        result = SongRating(conn).update_rating(user, song_id, request.form['stars'])
    else:
        result = SongRating(conn).create(request.form)

    if not result['SUCCESS']:
        session['errors'] = result['errors']

    return redirect(url_for('song', song_id=song_id))

def song_review(conn, session, song_id):
    user = session.get('username')

    if not user:
        session['errors'] = ['Log in to leave a review']
        return redirect(url_for('song', song_id=song_id))

    song = Song(conn).by_id().retrieve(inpt=[song_id])['data']
    if not song:
        session['errors'] = ['The song does not exist.']
        return redirect('/')

    if not request.form.get('review_text'):
        session['errors'] = ['Your review must include text.']
        return redirect(url_for('song', song_id=song_id))

    # Don't worry about existing form because there can be multiple per user/song_id based on timestamp
    result = SongReview(conn).create(request.form)

    if not result['SUCCESS']:
        session['errors'] = result['errors']

    return redirect(url_for('song', song_id=song_id))

def new_song(conn, session, artist_id):
    get_info(conn)
    user = session.get('username')

    if not user:
        session['errors'] = ['You must be logged in to create new records.']
        return redirect('/browse')

    if not artist_id:
        return redirect('/select_artist')

    artist = Artist(conn).where(f'artist_id = %s').retrieve(inpt=[artist_id], method='fetchone')['data']
    if not artist:
        return redirect('/select_artist')

    albums = Album(conn).with_artists().where(f'released.artist_id = %s').retrieve(inpt=[artist_id], method='fetchall')['data']
    genres = Genre(conn).genre_list().retrieve(method='fetchall')['data']
    return render_template('new_song.html', user=user, artist=artist, albums=albums, genres=genres)

def add_song(conn, session):
    get_info(conn)
    user = session.get('username')

    if not user:
        session['errors'] = ['You must be logged in to create new records.']
        return redirect('/browse')

    form = request.form
    result = Song(conn).create(form)
    if not result['SUCCESS'] or not result['data'] or not result['data']['song_id'] :
        artist_id = form['artist_id']
        artist = Artist(conn).where(f'artist_id = %s').retrieve(inpt=[artist_id], method='fetchone')['data']
        albums = Album(conn).with_artists().where(f'released.artist_id = %s').retrieve(inpt=[artist_id], method='fetchall')['data']
        genres = Genre(conn).genre_list().retrieve(method='fetchall')['data']
        return render_template('new_song.html', user=user, artist=artist, albums=albums, genres=genres, errors=result['errors'])

    # Clear the session because we want to reset the cache at this point
    empty_session_lists()
    return redirect(url_for('song', song_id=result['data']['song_id']))
