from flask import Flask, render_template, request, session, url_for, redirect, flash

from query_objects.artist import Artist
from query_objects.genre import Genre


# The list of available artists and genres appear often.
# Saving these lists to the session so they don't have to be retrieved repeatedly
def get_info(conn):
    if not session.get('artist_list'):
        artist_list = Artist(conn).select(['artist_name', 'artist_id']).group_by('artist_id').order_by('artist_name')
        session['artist_list'] = artist_list.retrieve(method='fetchall')['data']

    if not session.get('genre_list'):
        session['genre_list'] = Genre(conn).genre_list().retrieve(method='fetchall')['data']


# Need to refresh the list after certain actions (i.e. creating a song)
def empty_session_lists():
    session.pop('artist_list')
    session.pop('genre_list')


def reset_errors():
    if session.get('errors'):
        return session.pop('errors')

    return []


def rating_vals(rating):
    return {
        'one': 'checked' if rating == 1 else '',
        'two': 'checked' if rating == 2 else '',
        'three': 'checked' if rating == 3 else '',
        'four': 'checked' if rating == 4 else '',
        'five': 'checked' if rating == 5 else ''
    }