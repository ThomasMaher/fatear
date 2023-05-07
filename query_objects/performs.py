from query_objects.query_object import QueryObject

class Performs(QueryObject):
    def __init__(self, conn):
        QueryObject.__init__(self, conn, 'performs', None)
        self.required_fields = ['artist_id', 'song_id']


    def create(self, form):
        result = self.validate(form)

        keys = ['artist_id', 'song_id']
        vals = [form[key] if form[key] != '' else None for key in keys]
        data = super().create(keys, vals, form)
        return data