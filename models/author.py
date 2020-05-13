from models.database import CursorFromConnectionPool


class Author:
    __id = 0

    @staticmethod
    def generate_id():
        Author.__id += 1
        return Author.__id

    def __init__(self, full_name, job_title, linkedin, contact, articles_counter):
        self.id = Author.generate_id()
        self.full_name = full_name
        self.job_title = job_title
        self.articles_counter = articles_counter
        self.linkedin = linkedin
        self.contact = contact

    def __repr__(self):
        return "<Author {0}>".format(self.id)

    def save_to_db(self):
        with CursorFromConnectionPool() as cursor:
            cursor.execute(
                '''INSERT INTO author (author_id, full_name, job_title, linkedin, contact, articles_counter)
                    VALUES (%s, %s, %s, %s, %s, %s)''',
                (self.id, self.full_name, self.job_title, self.linkedin, self.contact, self.articles_counter)
            )

    @staticmethod
    def get_max_id():
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT author_id FROM author ORDER BY author_id DESC LIMIT 1')
            try:
                max_id = cursor.fetchone()[0]
                return max_id
            except TypeError:
                return None

    @staticmethod
    def find_id_by_name(full_name):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT author_id FROM author WHERE full_name=%s', (full_name,))
            try:
                author_id = cursor.fetchone()[0]
                return author_id
            except TypeError:
                return None


    @classmethod
    def load_from_db_by_email(cls, email):
        with CursorFromConnectionPool() as cursor:
            # Note the (email,) to make it a tuple!
            cursor.execute('SELECT * FROM users WHERE email=%s', (email,))
            user_data = cursor.fetchone()
            return cls(email=user_data[1], first_name=user_data[2], last_name=user_data[3], id=user_data[0])
