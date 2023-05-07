from query_objects.query_object import QueryObject

class Genre(QueryObject):
    def __init__(self, conn):
        QueryObject.__init__(self, conn, 'song_genres', 'genre')
        self.required_fields = ['genre']

    def genre_list(self):
        return self.select('genre').group_by('genre').order_by('genre')

    def create(self, form):
        keys = ['genre', 'song_id']
        vals = [form.get(key) if form.get(key) != '' else None for key in keys]
        data = super().create(keys, vals, form)
        return data
