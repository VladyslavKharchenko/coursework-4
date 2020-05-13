from models.database import CursorFromConnectionPool


class Article:
    __id = 0

    @staticmethod
    def generate_id():
        Article.__id += 1
        return Article.__id

    def __init__(self, title, url, text, publication_date, author, tag):
        self.id = Article.generate_id()
        self.title = title
        self.url = url
        self.text = text
        self.publication_date = publication_date
        self.author = author
        self.tag = tag

    def __repr__(self):
        return "<Article >".format(self.id)

    def save_to_db(self):
        with CursorFromConnectionPool() as cursor:
            cursor.execute(
                '''INSERT INTO article (article_id, title, url, text, publication_date, author_id, tag)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                (self.id, self.title, self.url, self.text, self.publication_date, self.author, self.tag)
            )

    @staticmethod
    def find_last_date():
        with CursorFromConnectionPool() as cursor:
            cursor.execute(
                '''SELECT publication_date FROM article ORDER BY publication_date DESC LIMIT 1'''
            )
            last_date = cursor.fetchone()[0]
            return last_date

    @staticmethod
    def find(title, author_id, tag):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('''
            SELECT EXISTS(
            SELECT title, author_id, tag
            FROM article
            WHERE title=%s AND author_id=%s AND tag=%s
            )''', (title, author_id, tag))
            exists = cursor.fetchone()[0]
            return exists

    @staticmethod
    def get_max_id():
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT article_id FROM article ORDER BY article_id DESC LIMIT 1')
            try:
                max_id = cursor.fetchone()[0]
                return max_id
            except TypeError:
                return None