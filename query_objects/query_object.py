import pymysql
class QueryObject:
    def __init__(self, conn, base, rec_id):
        self.conn = conn
        self.base = base
        self.id = rec_id
        self.selects = []
        self.joins = []
        self.conditions = []
        self.grouping = []
        self.ordering = []
        self.direction = 'ASC'
        self.limit = ''

    def retrieve(self, inpt=None, method='fetchone', query=None):
        if query is None:
            query = self.__build_query()

        print(f'QUERY: {query}')
        print(f'VALS: {inpt}')

        error = None
        data = None
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, inpt)
            func = getattr(cursor, method)
            data = func()
        except pymysql.Error as err:
            error = err

        cursor.close()
        return {'SUCCESS': error is None, 'errors': [error], 'data': data}

    def create(self, keys, vals, form):
        val_result = self.validate(form)
        if not val_result['SUCCESS']:
            return val_result

        placeholders = f"({', '.join(['%s' for k in keys])})"
        query_keys = f"({', '.join(keys)})"
        query = f'INSERT INTO {self.base} {query_keys} VALUES {placeholders}'
        print('QUERY: ' + query)
        print(vals)

        error = None
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, vals)
            self.conn.commit()
        except pymysql.Error as err:
            error = err

        if self.id:
            get_query = f"SELECT * FROM {self.base} ORDER BY {self.id} DESC LIMIT 1"
            print('QUERY: ' + get_query)
            cursor.execute(get_query)
            data = cursor.fetchone()
            cursor.close()
        else:
            data = None

        return {'SUCCESS': error is None, 'errors': [error], 'data': data}

    def where(self, conditions):
        if isinstance(conditions, list):
            for condition in conditions:
                self.conditions.append(condition)
        else:
            self.conditions.append(conditions)

        return self

    def group_by(self, groupings):
        if isinstance(groupings, list):
            for group in groupings:
                self.grouping.append(group)
        else:
            self.grouping.append(groupings)

        return self

    def order_by(self, orderings):
        if isinstance(orderings, list):
            for ordering in orderings:
                self.ordering.append(ordering)
        else:
            self.ordering.append(orderings)

        return self

    def set_direction(self, direction):
        self.direction = direction

        return self

    def set_limit(self, limit):
        self.limit = str(limit)

        return self

    def join(self, assignments):
        if isinstance(assignments, list):
            for assignment in assignments:
                self.joins.append(assignment)
        else:
            self.joins.append(assignments)

        return self

    def select(self, columns):
        if isinstance(columns, list):
            for column in columns:
                self.selects.append(column)
        else:
            self.selects.append(columns)

        return self

    def by_id(self):
        self.conditions.append(f'{self.base}.{self.id} = %s')

        return self

    def __build_query(self):
        select = '*' if not self.selects else ', '.join(self.selects)
        select = f'SELECT {select} FROM {self.base}'
        joins = f"{' '.join(self.joins)}"
        # Uses AND be default. For queries using ORs, these may need to be built manually or else carefully through with this interface
        _where = '' if not self.conditions else f"WHERE {' AND '.join(self.conditions)}"
        _group_by = '' if not self.grouping else f"GROUP BY {', '.join(self.grouping)}"
        _order_by = '' if not self.ordering else f"ORDER BY {', '.join(self.ordering)} {self.direction}"
        _limit = '' if not self.limit else f"LIMIT {self.limit}"
        query = ' '.join([select, joins, _where, _group_by, _order_by, _limit])
        print(query)

        return query

    def validate(self, form):
        print(f'Validating {self.base}')
        errors = []
        for req_key in self.required_fields:
            if not form.get(req_key):
                errors.append(f'{req_key} is required')

        return {'SUCCESS': len(errors) == 0, 'errors': errors, 'data': None}