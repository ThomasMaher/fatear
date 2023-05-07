from query_objects.query_object import QueryObject

class Track(QueryObject):
    def __init__(self, conn):
        QueryObject.__init__(self, conn, 'track', None)
        self.required_fields = ['album_id', 'song_id']


    def create(self, form):
        result = self.validate(form)

        keys = ['album_id', 'song_id']
        vals = [form.get(key) if form.get(key) != '' else None for key in keys]
        data = super().create(keys, vals, form)
        return data