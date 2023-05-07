from query_objects.query_object import QueryObject
from datetime import datetime

class AlbumReview(QueryObject):
    def __init__(self, conn):
        QueryObject.__init__(self, conn, 'album_reviews', None)
        self.required_fields = ['username', 'album_id', 'review_text', 'review_date']

    def create(self, form):
        form = form.to_dict()
        form['review_date'] = datetime.today()
        keys = ['username', 'album_id', 'review_text', 'review_date']
        vals = [form.get(key) if form.get(key) != '' else None for key in keys]
        data = super().create(keys, vals, form)
        return data
