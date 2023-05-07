from query_objects.query_object import QueryObject

class Artist(QueryObject):
    def __init__(self, conn):
        QueryObject.__init__(self, conn, 'artists', 'artist_id')
        self.required_fields = ['artist_name']

    def with_albums(self):
        self.joins.append('LEFT JOIN released on released.artist_id = artists.artist_id')
        self.joins.append('LEFT JOIN albums on albums.album_id = released.album_id')
        return self

    def create(self, form):
        keys = ['artist_name', 'fname', 'lname', 'artist_bio', 'artist_url']
        vals = [form.get(key) if form.get(key) != '' else None for key in keys]
        data = super().create(keys, vals, form)
        return data
