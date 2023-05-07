from flask import render_template, request, url_for, redirect

from utils import get_info, reset_errors, rating_vals
from query_objects.genre import Genre
from query_objects.album import Album
from query_objects.album_rating import AlbumRating
from query_objects.album_review import AlbumReview

def albums(conn, session, album_id):
    get_info(conn)
    user = session.get('username')
    errors = reset_errors()

    data = Album(conn).by_id().with_songs().retrieve(inpt=[album_id], method='fetchall')['data']
    if not data:
        session['errors'] = ['Album not found.']
        return redirect('/')

    album = data[0]
    tracks = data
    print(tracks)

    artists = Album(conn).by_id().with_artists().select(['artists.artist_id', 'artists.artist_name'])
    artists = artists.retrieve(inpt=[album_id], method='fetchall')['data']

    song_ids = [track['song_id'] for track in tracks]
    genres = Genre(conn).where('song_id IN %s').select('genre').group_by('genre')
    genres = genres.retrieve(inpt=[song_ids], method='fetchall')['data']

    average_rating = AlbumRating(conn).average_for(album_id)
    average_rating = 0 if average_rating is None else round(average_rating, 1)

    my_rating = AlbumRating(conn).where('album_id = %s AND username = %s')
    my_rating = my_rating.retrieve(inpt=[album_id, user], method='fetchone')['data']
    if not my_rating:
        my_rating = {'stars': 0}

    reviews = AlbumReview(conn).where('album_id = %s').order_by('review_date').set_direction('DESC')
    reviews = reviews.retrieve(inpt=[album_id], method='fetchall')['data']

    return render_template(
        'album.html',
        user=user,
        album=album,
        tracks=tracks,
        artists=artists,
        average_rating=average_rating,
        reviews=reviews,
        rating_vals=rating_vals(my_rating.get('stars')),
        genres=genres,
        errors=errors
    )


def album_rating(conn, session, album_id):
    user = session.get('username')

    if not user:
        session['errors'] = ['Log in to rate an album.']
        return redirect(url_for('albums', album_id=album_id))

    album = Album(conn).by_id().retrieve(inpt=[album_id])['data']
    if not album:
        session['errors'] = ['The album does not exist.']
        return redirect('/')

    if not request.form.get('stars'):
        session['errors'] = ['No rating was selected.']
        return redirect(url_for('albums', album_id=album_id))

    existing_rating = AlbumRating(conn).where('username = %s AND album_id = %s').retrieve(inpt=[user, album_id])['data']
    if existing_rating:
        result = AlbumRating(conn).update_rating(user, album_id, request.form['stars'])
    else:
        result = AlbumRating(conn).create(request.form)

    if not result['SUCCESS']:
        session['errors'] = result['errors']

    return redirect(url_for('albums', album_id=album_id))


def album_review(conn, session, album_id):
    user = session.get('username')

    if not user:
        session['errors'] = ['Log in to leave a review']
        return redirect(url_for('albums', album_id=album_id))

    album = Album(conn).by_id().retrieve(inpt=[album_id])['data']
    if not album:
        session['errors'] = ['The album does not exist.']
        return redirect('/')

    if not request.form.get('review_text'):
        session['errors'] = ['Your review must include text.']
        return redirect(url_for('albums', album_id=album_id))

    # Don't worry about existing form because there can be multiple per user/album_id based on timestamp
    result = AlbumReview(conn).create(request.form)

    if not result['SUCCESS']:
        session['errors'] = result['errors']

    return redirect(url_for('albums', album_id=album_id))