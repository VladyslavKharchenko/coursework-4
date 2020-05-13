import models
from models.author import Author
from models.database import Database
from models.article import Article

Database.initialise(database="blog", user="root", password="root", host="localhost")

# CTO = Author('Victoria Livschitz','Founder and EVP of Customer Success', linkedin='asd', contact=None, articles_counter=15)
# CEO = Author('Someone else', 'who', linkedin=None, contact='AAAA', articles_counter=3)
# a = Author('ABCD', None, linkedin='rtrw', contact='AAAA', articles_counter=6)
# b = Author('ABCDa', 'lel', linkedin=None, contact='', articles_counter=0)
# CTO.save_to_db()
# CEO.save_to_db()
# a.save_to_db()
# b.save_to_db()
id = Author.find_id_by_name('Aleksey Romanov')
print(id)
# user = User('jose@schoolofcode.me', 'Jose', 'Salvatierra')
#
# user.save_to_db()
#
# user_from_db = User.load_from_db_by_email('jose@schoolofcode.me')
#
# print(user_from_db)