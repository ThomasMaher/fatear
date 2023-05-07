from query_objects.query_object import QueryObject
from query_objects.performs import Performs
from query_objects.album import Album
from query_objects.track import Track
from query_objects.released import Released
from query_objects.genre import Genre

class Song(QueryObject):
    def __init__(self, conn):
        QueryObject.__init__(self, conn, 'songs', 'song_id')
        self.required_fields = ['title']

    def with_artists(self):
        self.joins.append('LEFT JOIN performs on songs.song_id = performs.song_id')
        self.joins.append('JOIN artists on artists.artist_id = performs.artist_id')
        return self

    def with_albums(self):
        self.joins.append('LEFT JOIN track on track.song_id = songs.song_id')
        self.joins.append('JOIN albums on albums.album_id = track.album_id')

        return self

    def with_ratings(self):
        self.joins.append('LEFT JOIN song_ratings on song_ratings.song_id = songs.song_id')

        return self

    def song_data(self, song_id):
        selects = 'title, songs.release_date, song_url, artist_name, album_title, albums.release_date'
        avg_rating = '(SELECT AVG(stars) FROM song_ratings WHERE song_id = %s) as average_rating'
        query = f'SELECT {selects}, {avg_rating} FROM songs ' \
                'LEFT JOIN performs on songs.song_id = performs.song_id ' \
                'JOIN artists on artists.artist_id = performs.artist_id ' \
                'LEFT JOIN track on track.song_id = songs.song_id ' \
                'JOIN albums on albums.album_id = track.album_id ' \
                'LEFT JOIN song_ratings on song_ratings.song_id = songs.song_id ' \
                'WHERE songs.song_id = %s'

        cursor = self.conn.cursor()
        cursor.execute(query, (song_id, song_id))
        result = cursor.fetchall()
        cursor.close()

        return result

    def create(self, form):
        # Create record
        keys = ['title', 'song_length', 'release_date', 'song_url']
        vals = [form.get(key) if form.get(key) != '' else None for key in keys]
        data = super().create(keys, vals, form)
        if not data['SUCCESS']:
            return data

        # Tie to artist (required)
        form = form.to_dict()
        form['song_id'] = data['data']['song_id']
        perform = Performs(self.conn)
        result = perform.create(form)
        if not result['SUCCESS']:
            data['errors'].append(result['errors'])
            return data

        # Create genre record if one is chosen
        form['genre'] = form.get('genre_new') if form.get('genre_new') else form['genre']
        if form['genre'] != '0':
            genre = Genre(self.conn)
            result = genre.create(form)
            if not result['SUCCESS']:
                data['errors'].append(result['errors'])
                return data

        # Create album if new album entered
        if form.get('album_title'):
            form.pop('album_id')
            album = Album(self.conn)
            result = album.create(form)
            if not result['SUCCESS']:
                data['errors'].append(result['errors'])
                return data
            form['album_id'] = result['data']['album_id']

            # Tie album to artist
            released = Released(self.conn)
            result = released.create(form)
            if not result['SUCCESS']:
                data['errors'].append(result['errors'])
                return data

        # Tie new or existing album to song
        if form.get('album_id') != '0':
            track = Track(self.conn)
            result = track.create(form)
            if not result['SUCCESS']:
                data['errors'].append(result['errors'])
                return data

        return data

