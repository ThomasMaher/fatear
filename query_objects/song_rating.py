from query_objects.query_object import QueryObject
from datetime import datetime

class SongRating(QueryObject):
    def __init__(self, conn):
        QueryObject.__init__(self, conn, 'song_ratings', None)
        self.required_fields = ['username', 'song_id', 'stars', 'rating_date']

    def average_for(self, song_id):
        query = 'SELECT AVG(stars) as average from song_ratings where song_id = %s'
        cursor = self.conn.cursor()
        cursor.execute(query, (song_id))
        result = cursor.fetchone()
        cursor.close()

        return result['average']

    def update_rating(self, user, song_id, stars):
        cursor = self.conn.cursor()
        error = None
        try:
            query = 'UPDATE song_ratings SET stars = %s WHERE username = %s AND song_id = %s'
            cursor.execute(query, [stars, user, song_id])
            self.conn.commit()
        except Exception as err:
            error = err

        return {'SUCCESS': error is None, 'errors': [error], 'data': None}

    def create(self, form):
        form = form.to_dict()
        form['rating_date'] = datetime.now()
        keys = ['username', 'song_id', 'stars', 'rating_date']
        vals = [form.get(key) if form.get(key) != '' else None for key in keys]
        data = super().create(keys, vals, form)
        return data
