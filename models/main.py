import pandas as pd

from models.database import Database
from report import get_top7_tags_plt
Database.initialise(database="blog", user="root", password="root", host="localhost")
query = pd.read_sql_query("SELECT * FROM author", Database.get_connection())
top5_authors = query.sort_values('articles_counter', ascending=False).head(5)
print(top5_authors)
