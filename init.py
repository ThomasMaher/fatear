from flask import render_template, request, session, url_for, redirect
import pymysql.cursors

from query_objects.song import Song

from routers import song_router, album_router, artist_router, user_router, auth_router

from utils import get_info, reset_errors

# I am purposefully not commits app.py because I wanted a file to store that DB password in
# To run the app, create an app.py file which initializes Flask and sets the DB password and secret key
from app import app, DB_PW

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port=3306,
                       user='root',
                       password=DB_PW,
                       db='fatear2',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)


@app.context_processor
def view_helper_funcs():
    def val_selected(val, current_selection):
        if str(val) == str(current_selection):
            return 'selected'
        elif val == '0' and current_selection == None:
            return 'selected'
        else:
            return None

    def search_inpt_val(inpt, val):
        if inpt and inpt.get(val):
            return inpt.get(val)

    def not_none(val, default=''):
        return default if val is None else val

    def entity_url(content):
        if content['entity_type'] == 'album':
            return url_for('albums', album_id=content['entity_id'])
        else:
            return url_for('song', song_id=content['entity_id'])

    def display_name(user):
        first = user['fname'] if user['fname'] else ''
        last = user['lname'] if user['lname'] else ''
        return first + ' ' + last

    return dict(
        val_selected=val_selected,
        search_inpt_val=search_inpt_val,
        not_none=not_none,
        entity_url=entity_url,
        display_name=display_name
    )

# ___ User Routes ___
@app.route('/')
def home():
    return user_router.home(conn, session)

@app.route('/people')
def people():
    return(user_router.people(conn, session))

@app.route('/friend_request', methods=['POST'])
def friend_request():
    return user_router.friend_request(conn, session)
@app.route('/follow', methods=['POST'])
def follow():
    return user_router.follow(conn, session)
@app.route('/profile/<username>', methods=['GET'])
def profile(username):
    return user_router.profile(conn, session, username)


# ___ Song Routes ___
@app.route('/song/<int:song_id>')
def song(song_id):
    return song_router.song(conn, session, song_id)

@app.route('/song_rating/<int:song_id>', methods=['POST'])
def song_rating(song_id):
    return song_router.song_rating(conn, session, song_id)

@app.route('/song_review/<int:song_id>', methods=['POST'])
def song_review(song_id):
    return song_router.song_review(conn, session, song_id)

@app.route('/new_song/<int:artist_id>', methods=['GET'])
def new_song(artist_id):
    return song_router.new_song(conn, session, artist_id)

@app.route('/add_song', methods=['POST'])
def add_song():
    return song_router.add_song(conn, session)



# ___ Album Routes ___
@app.route('/albums/<int:album_id>', methods=['GET'])
def albums(album_id):
    return album_router.albums(conn, session, album_id)

@app.route('/album_rating/<int:album_id>', methods=['POST'])
def album_rating(album_id):
    return album_router.album_rating(conn, session, album_id)

@app.route('/album_review/<int:album_id>', methods=['POST'])
def album_review(album_id):
    return album_router.album_review(conn, session, album_id)



# ___ Artist Routes ___
@app.route('/artists/<int:artist_id>', methods=['GET'])
def artists(artist_id):
    return artist_router.artists(conn, session, artist_id)

@app.route('/select_artist', methods=['GET', 'POST'])
def select_artist():
    return artist_router.select_artist(conn, session)

@app.route('/fan', methods=['POST'])
def fan():
    return artist_router.fan(conn, session)



# ___ Browse Routes ___
@app.route('/clear_browse', methods=['GET'])
def clear_browse():
    return redirect('/browse')

@app.route('/browse', methods=['GET'])
def browse():
    get_info(conn)
    user = session.get('username')
    errors = reset_errors()

    song_query = Song(conn).with_artists().with_albums()
    vals = []
    usr_input = request.args
    if user:
        song_query.join('LEFT JOIN song_ratings on song_ratings.song_id = songs.song_id AND song_ratings.username = %s')
        vals.append(user)

    if usr_input:
        search_text = usr_input.get('search_val')
        genre = usr_input.get('genre')
        artist = usr_input.get('artist')
        stars = usr_input.get('stars')
        order_by = 'artists.artist_name, albums.album_title, songs.title'
        if search_text:
            song_query.where('(songs.title LIKE %s OR album_title LIKE %s OR artist_name LIKE %s)')
            vals += [f'%{search_text}%', f'%{search_text}%', f'%{search_text}%']

        if genre != '0':
            sub_query = '(SELECT song_id FROM song_genres WHERE genre = %s)'
            song_query.where(f'songs.song_id IN {sub_query}')
            vals.append(genre)

        if artist != '0':
            song_query.where('artists.artist_id = %s')
            vals.append(artist)

        if stars != '0':
            sub_query = '(SELECT song_id FROM song_ratings group by song_id HAVING AVG(stars) >= %s)'
            song_query.where(f'songs.song_id IN {sub_query}')
            vals.append(stars)

        song_query.order_by(order_by).set_direction('DESC')
        result = song_query.retrieve(inpt=vals, method='fetchall')
        header = 'Search Results'
    else:
        song_query.order_by('songs.release_date').set_direction('DESC').set_limit(5)
        result = song_query.retrieve(inpt=vals, method='fetchall')
        header = 'Recently Added Songs'

    if result['SUCCESS']:
        songs = result['data']
    else:
        songs = []
        errors = result['errors']

    return render_template(
        'browse.html',
        songs=songs,
        user=user,
        header=header,
        on_browse=True,
        usr_input=usr_input,
        errors=errors
    )

# ___ Authentication Routes ___
@app.route('/login')
def login():
    return render_template('login.html', user=None)

@app.route('/register')
def register():
    return render_template('register.html', user=None)

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    return auth_router.loginAuth(conn, session)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    return auth_router.registerAuth(conn, session)

@app.route('/logout')
def logout():
    user = session.get('username')
    if user:
        session.pop('username')

    return redirect('/')


if __name__ == "__main__":
    app.run('127.0.0.1', 3000, debug = True)
