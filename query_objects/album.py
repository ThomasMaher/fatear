from query_objects.query_object import QueryObject

class Album(QueryObject):
    def __init__(self, conn):
        QueryObject.__init__(self, conn, 'albums', 'album_id')
        self.required_fields = ['album_title']


    def with_artists(self):
        self.joins.append('LEFT JOIN released on albums.album_id = released.album_id')
        self.joins.append('LEFT JOIN artists on artists.artist_id = released.artist_id')
        return self

    def with_songs(self):
        self.joins.append('LEFT JOIN track on albums.album_id = track.album_id')
        self.joins.append('LEFT JOIN songs on songs.song_id = track.song_id')
        return self


    def create(self, form):
        keys = ['album_title', 'release_date', 'track_num']
        vals = [form.get(key) if form.get(key) != '' else None for key in keys]
        data = super().create(keys, vals, form)
        return data