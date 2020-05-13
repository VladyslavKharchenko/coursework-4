import shlex  # Lexical analysis of shell-style syntaxes
import subprocess
import os
import logging
import pandas as pd
from matplotlib import pyplot as plt

from models.author import Author
from models.database import Database, CursorFromConnectionPool

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s', )

file_handler = logging.FileHandler('gd_blog_parser.log')  # to log into file as well as to console
logging.getLogger().addHandler(file_handler)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
file_handler.setFormatter(formatter)


def run_command(command):
    process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
    while True:
        output = process.stdout.readline().decode()
        if output == '' and process.poll() is not None:  # poll() reads a line from the stdout (None if still running)
            break
        if output:
            print(output.strip())
    rc = process.poll()  # returns 'return code' cuz process is completed
    return rc


def get_top7_tags_plt(csv_path=None):
    def top_7_tags():
        Database.initialise(database="blog", user="root", password="root", host="localhost")
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT DISTINCT tag, count(*) '
                           'FROM article GROUP BY tag '
                           'ORDER BY count DESC LIMIT 7')
            raw_result = cursor.fetchall()
            result = dict(raw_result)
            for k in result.keys():
                if k == 'Machine Learning and Artificial Intelligence':
                    result['ML & AI'] = result.pop('Machine Learning and Artificial Intelligence')
                elif k == 'Sentiment analysis of tweets':
                    result['SA of tweets'] = result.pop('Sentiment analysis of tweets')
                elif k == 'Data science toolkit':
                    result['Data Science TK'] = result.pop('Data science toolkit')
            return result

    top_7_tags = top_7_tags()
    top_7_tags = {k: v for k, v in sorted(
        top_7_tags.items(), key=lambda item: item[1], reverse=True)}  # sort tags by counter, descending

    x = range(7)
    plt.figure(figsize=(9, 5))
    rects = plt.bar(x, top_7_tags.values())
    plt.xticks(x, top_7_tags.values(), rotation='horizontal')
    plt.yticks([], [])
    plt.title('Tags')
    plt.xlabel('Articles counter')

    def autolabel(rects):
        """Attach a text label above each bar in *rects*, displaying its title."""
        for rect, key in zip(rects, top_7_tags.keys()):
            height = rect.get_height()
            plt.annotate('{}'.format(key),
                         xy=(rect.get_x() + rect.get_width() / 2, height),
                         xytext=(0, 3),  # 3 points vertical offset
                         textcoords="offset points",
                         ha='center', va='bottom')

    autolabel(rects)
    plt.tight_layout()
    return plt


def get_top5_articles_df():
    query = pd.read_sql_query("SELECT * FROM article", Database.get_connection())
    top5_articles = query.sort_values('publication_date', ascending=False).drop_duplicates('url').head(5)
    return top5_articles


def get_top5_authors_df(csv_path=None):
    query = pd.read_sql_query("SELECT * FROM author", Database.get_connection())
    top5_authors = query.sort_values('articles_counter', ascending=False).head(5)
    return top5_authors


def df_to_str(df):
    df_for_file = df.to_string(index=False, na_rep='')  # dataframe as non-truncated string (for file)
    df_for_console = '\n\n' + df.to_string(index=False, na_rep='', max_colwidth=20) + '\n'
    '''dataframe as truncated string with newline characters for prettier console output'''
    return df_for_console, df_for_file


def generate_report(plt, art_cons, auth_cons, art_file, auth_file):
    logging.info('Generating the report . . .')
    plt.savefig('top7tags.png', dpi=100)
    logging.info('To continue close pop-up window')
    plt.show()
    logging.info('Top-5 Authors (based on articles counter)')
    logging.info(auth_cons)
    logging.info('Top-5 New Articles (based on publish data)')
    logging.info(art_cons)
    logging.info('Short-form reports displayed above in the console.\n'
                 '\t\t\t\tLong-form reports saved to the current directory:\n'
                 '\t\t\t\t\t\t-> top5articles.txt\n'
                 '\t\t\t\t\t\t-> top5authors.txt\n'
                 '\t\t\t\t\t\t-> top7tags.png\n')

    with open('top5authors.txt', mode='w', newline='', encoding='utf-8') as f:  # writing
        f.writelines(auth_file)

    with open('top5articles.txt', mode='w', newline='', encoding='utf-8') as f:
        f.writelines(art_file)


if __name__ == "__main__":
    logging.info('Script started')
    logging.info('Checking if data already exists . . .')
    return_code = run_command('scrapy crawl blog_scraper --nolog')  # scrape all info from scratch and save data
    if return_code is 0:
        logging.info('Getting data for the report . . .')
        plt = get_top7_tags_plt()
        top5_articles_df = get_top5_articles_df()
        top5_authors_df = get_top5_authors_df()
        art_cons, art_file = df_to_str(top5_articles_df)
        auth_cons, auth_file = df_to_str(top5_authors_df)
        generate_report(plt, art_cons, auth_cons, art_file, auth_file)
    else:
        logging.fatal('Script execution has been stopped because of error')
