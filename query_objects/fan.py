from query_objects.query_object import QueryObject

class Fan(QueryObject):
    def __init__(self, conn):
        QueryObject.__init__(self, conn, 'fan', None)
        self.required_fields = ['artist_id', 'username']

    def is_fan(self, username, artist_id):
        query = 'SELECT * FROM fan WHERE username = %s AND artist_id = %s'
        result = self.retrieve(inpt=[username, artist_id], query=query)

        return True if result['data'] else False

    def create(self, form):
        keys = ['artist_id', 'username']
        vals = [form.get(key) if form.get(key) != '' else None for key in keys]
        data = super().create(keys, vals, form)
        return data
