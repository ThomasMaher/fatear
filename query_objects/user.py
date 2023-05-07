from query_objects.query_object import QueryObject
from datetime import datetime, date, timedelta
import pymysql

THIRTY_DAYS_AGO = timedelta(days=30)

class User(QueryObject):
    def __init__(self, conn):
        QueryObject.__init__(self, conn, 'users', 'username')
        self.required_fields = ['username', 'password', 'lastLogin']
        self.users_of_interest = None

    def users_of_interest_query(self, username):
        query = 'SELECT DISTINCT(username) FROM users as followed ' \
                'JOIN friend ON ' \
                '(friend.user1 = %s AND friend.user2 = followed.username) ' \
                'OR (friend.user2 = %s AND friend.user1 = followed.username) ' \
                'WHERE accept_status = TRUE ' \
                'UNION ' \
                'SELECT DISTINCT(username) FROM users as followed ' \
                'JOIN follows ON follows.follows = followed.username '\
                'WHERE follows.follower = %s' \

        #Why do i get multiple results?
        results = self.retrieve(inpt=[username, username, username], method='fetchall', query=query)
        if not results['SUCCESS'] or not results['data']:
            return []
        self.users_of_interest = [rec['username'] for rec in results['data']]
        return self.users_of_interest

    def check_users_of_interest(self, username):
        if self.users_of_interest is None:
            return self.users_of_interest_query(username)

        return self.users_of_interest

    def feed_query(self, username):
        users_of_interest = self.check_users_of_interest(username)

        if users_of_interest:
            query = 'select username, album_title as title, albums.album_id as entity_id, review_text as body, ' \
                    '"review" as post_type, review_date as post_date, "album" as entity_type from album_reviews ' \
                    'JOIN albums on albums.album_id = album_reviews.album_id ' \
                    'where username IN %s '\
                    'UNION ' \
                    'select username, title, songs.song_id as entity_id, review_text as body, "review" as post_type, ' \
                    'review_date as post_date, "song" as entity_type from song_reviews ' \
                    'JOIN songs on songs.song_id = song_reviews.song_id ' \
                    'where username IN %s ' \
                    'UNION ' \
                    'select username, title, songs.song_id as entity_id, stars as body, "rating" as post_type, ' \
                    'rating_date as post_date, "song" as entity_type from song_ratings ' \
                    'JOIN songs on songs.song_id = song_ratings.song_id ' \
                    'where username IN %s ' \
                    'UNION ' \
                    'select username, album_title as title, albums.album_id as entity_id, stars as body, "rating" as post_type, ' \
                    'rating_date as post_date, "album" as entity_type from album_ratings ' \
                    'JOIN albums on albums.album_id = album_ratings.album_id ' \
                    'where username IN %s ' \
                    'UNION ' \
                    'select username, songs.title as title, songs.song_id as entity_id, artists.artist_name as body, ' \
                    '"new_song" as post_type, songs.release_date as post_date, "song" as entity_type FROM fan ' \
                    'JOIN artists on artists.artist_id = fan.artist_id ' \
                    'JOIN performs on performs.artist_id = fan.artist_id ' \
                    'JOIN songs on songs.song_id = performs.song_id ' \
                    'WHERE fan.username = %s AND songs.release_date is not NULL and songs.release_date > %s ' \
                    'order by post_date DESC'

            d = date.today()-THIRTY_DAYS_AGO
            feed = self.retrieve(
                inpt=[users_of_interest, users_of_interest, users_of_interest, users_of_interest, username, d],
                method='fetchall',
                query=query)
            return feed
        else:
            query = 'select username, songs.title as title, songs.song_id as entity_id, artists.artist_name as body, ' \
                    '"new_song" as post_type, songs.release_date as post_date, "song" as entity_type FROM fan ' \
                    'JOIN artists on artists.artist_id = fan.artist_id ' \
                    'JOIN performs on performs.artist_id = fan.artist_id ' \
                    'JOIN songs on songs.song_id = performs.song_id ' \
                    'WHERE fan.username = %s AND songs.release_date is not NULL and songs.release_date > %s ' \
                    'order by post_date DESC'
            d = date.today() - THIRTY_DAYS_AGO
            feed = self.retrieve(
                inpt=[username, d],
                method='fetchall',
                query=query)
            return feed

    def friend_requests(self, user):
        self.select('sender.*, friend.created_at')
        self.join('JOIN friend ON friend.user1 = users.username OR friend.user2 = users.username')
        self.join('JOIN users AS sender ON sender.username <> users.username '
                  'AND (friend.user1 = sender.username OR friend.user2 = sender.username)')
        self.where('users.username = %s AND friend.requested_by <> %s AND accept_status = FALSE')
        return self.retrieve(inpt=[user, user], method='fetchall')['data']

    def follow(self, user, friend):
        query = 'INSERT INTO follows (follower, follows, created_at) values (%s, %s, %s)'
        vals = [user, friend, datetime.now()]

        print('QUERY: ' + query)
        print(vals)

        error = None
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, vals)
            self.conn.commit()
        except pymysql.Error as err:
            error = err

        cursor.close()
        return {'SUCCESS': error is None, 'errors': [error], 'data': None}


    def friends(self, user):
        self.select('user_friend.*, friend.created_at')
        self.join('JOIN friend ON friend.user1 = users.username OR friend.user2 = users.username')
        self.join(
            'JOIN users AS user_friend ON user_friend.username <> users.username '
            'AND (friend.user1 = user_friend.username OR friend.user2 = user_friend.username)'
        )
        self.where('users.username = %s AND accept_status = TRUE')
        return self.retrieve(inpt=[user], method='fetchall')['data']

    def follows(self, user):
        self.select('followed.*, follows.created_at')
        self.join('JOIN follows ON follows.follower = users.username')
        self.join('JOIN users as followed on followed.username = follows.follows')
        self.where('users.username = %s')
        return self.retrieve(inpt=[user], method='fetchall')['data']

    def accept_friend_request(self, user, friend):
        query = 'UPDATE friend SET accept_status = TRUE WHERE requested_by = %s AND (user1 = %s OR user2 = %s)'

        cursor = self.conn.cursor()
        print(f'QUERY: {query}')
        print(f'VALS: {[friend, user, user]}')
        error = None
        try:
            cursor.execute(query, [friend, user, user])
            self.conn.commit()
        except pymysql.Error as err:
            error = err

        cursor.close()
        return {'SUCCESS': error is None, 'errors': [error], 'data': None}

    def remove_friend_request(self, user, friend):
        query = 'DELETE FROM friend WHERE requested_by = %s AND (user1 = %s OR user2 = %s)'

        cursor = self.conn.cursor()
        print(f'QUERY: {query}')
        print(f'VALS: {[friend, user, user]}')
        error = None
        try:
            cursor.execute(query, [friend, user, user])
            self.conn.commit()
        except pymysql.Error as err:
            error = err

        cursor.close()
        return {'SUCCESS': error is None, 'errors': [error], 'data': None}

    def create_friend_request(self, user, friend):
        query = 'INSERT INTO friend (user1, user2, accept_status, requested_by) VALUES (%s, %s, %s, %s)'
        vals = [user, friend, False, user]

        cursor = self.conn.cursor()
        print(f'QUERY: {query}')
        print(f'VALS: {vals}')
        error = None
        try:
            cursor.execute(query, vals)
            self.conn.commit()
        except pymysql.Error as err:
            error = err
            print(error)

        cursor.close()
        return {'SUCCESS': error is None, 'errors': [error], 'data': None}

    def is_friend(self, user, friend):
        query = 'select * from friend ' \
                'where user1 IN %s AND user2 IN %s ' # Since someone can't be friends with themselves, this works

        friendship = self.retrieve(inpt=[[user, friend], [user, friend]], query=query)
        return True if friendship['data'] else False

    def following(self, user, other_user):
        query = 'SELECT * FROM follows where follows.follower = %s AND follows.follows = %s'
        follows = self.retrieve(inpt=[user, other_user], query=query)

        return True if follows['data'] else False

    def create(self, form):
        form = form.to_dict()
        form['lastLogin'] = datetime.now()

        keys = ['username', 'fname', 'lname', 'password', 'lastLogin']
        vals = [form.get(key) if form.get(key) != '' else None for key in keys]
        data = super().create(keys, vals, form)
        return data
