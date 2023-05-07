from query_objects.query_object import QueryObject

class Released(QueryObject):
    def __init__(self, conn):
        QueryObject.__init__(self, conn, 'released', None)
        self.required_fields = ['album_id', 'artist_id']


    def create(self, form):
        result = self.validate(form)

        keys = ['album_id', 'artist_id']
        vals = [form.get(key) if form.get(key) != '' else None for key in keys]
        data = super().create(keys, vals, form)
        return data