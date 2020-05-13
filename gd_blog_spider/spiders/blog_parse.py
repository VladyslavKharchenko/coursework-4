import csv
import logging
from datetime import datetime, timedelta
from scrapy.spiders import CrawlSpider
from bs4 import BeautifulSoup

from models.author import Author
from models.article import Article
from models.database import Database

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s', )

file_handler = logging.FileHandler('gd_blog_parser.log')
logging.getLogger().addHandler(file_handler)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
file_handler.setFormatter(formatter)

from_scratch = None


class GDBlogCrawler(CrawlSpider):
    """This spider is used when no data exists"""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        logging.getLogger('scrapy').setLevel(logging.WARNING)

    name = 'blog_scraper'
    allowed_domains = ['blog.griddynamics.com']
    start_urls = [
        'https://blog.griddynamics.com/all-authors/'
    ]
    output_articles = 'Article'
    output_authors = 'Author'
    author_counter = 1  # for console output of parsing process, e.g. 'parsing [1/2] articles'
    authors_len = 0  # same as above
    new_authors_len = 0
    new_articles_len = 0
    articles_len = 0  # same as above
    all_articles = []

    def parse_author(self, response):
        """Function to parse each author and extract data to .csv file"""
        if from_scratch:
            logging.info('Parsing author page [{current}/{all}] -> {url}'.format(current=self.author_counter,
                                                                                 all=self.authors_len,
                                                                                 url=response.url))
        self.author_counter += 1
        author_info = response.css('div.modalbg')
        for field in author_info:
            full_name = field.css('div.authorcard.popup > div.row > div.titlewrp > h3::text').get()
            job_title = field.css('div.authorcard.popup > div.row > div.titlewrp > p.jobtitle::text').get()
            author_articles = field.css('div.authorcard.popup > div.postsrow > div.row > a::attr(href)').getall()
            articles_counter = len(author_articles)
            raw_urls = field.css('div.authorcard.popup > div.row > div.imgwrp > ul.socicons.mb15')
            all_urls = raw_urls.css('a::attr(href)').getall()
            linkedin = None
            contact = None
            for url in all_urls:
                if 'linkedin' in url:
                    linkedin = url
                else:
                    contact = url
            if from_scratch:
                author = Author(full_name, job_title, linkedin, contact, articles_counter)
                author.save_to_db()
            else:
                if Author.find_id_by_name(full_name) is None:
                    author = Author(full_name, job_title, linkedin, contact, articles_counter)
                    author.id = Author.get_max_id() + 1
                    logging.info('Found new author, id = {}! Saving . . .'.format(author.id))
                    self.new_authors_len += 1
                    author.save_to_db()
            for article in author_articles:
                GDBlogCrawler.all_articles.append(article)
            if self.author_counter > self.authors_len:
                logging.info('Looking for a new articles . . .')
                for article_url in GDBlogCrawler.all_articles:
                    yield response.follow(article_url, self.parse_article)  # parsing each article

    def parse_article(self, response, write_to_csv=True):
        """Function to parse each article and extract data to .csv file"""
        self.articles_len += 1
        if from_scratch:
            logging.info('Parsing article page -> {url}'.format(url=response.url))
        search_results = response.css('div#woe')
        for article in search_results:
            title = str(article.css('div.container > div#wrap > h2.mb30::text').get()) \
                .replace('\r', '').replace('\n', ' ')
            url = response.url
            text_raw_with_tags = article.css('section.postbody > div.container > p').getall()
            text = ''
            for row in text_raw_with_tags:
                soup_raw = BeautifulSoup(row, features='lxml')
                text += soup_raw.get_text().strip()  # getting rid of html tags
                if len(text) > 160:
                    text = text[:161].replace('\r', '').replace('\n', ' ')
            publication_date_as_str = article.css('div.authwrp > div.sdate::text').get()[9:21]
            publication_date = datetime.strptime(publication_date_as_str, '%b %d, %Y').date()
            authors_raw = article.css('div.authwrp > div.author.authors > div.sauthor '
                                      '> span > a.goauthor > span.name::text').getall()
            authors = []
            for author in authors_raw:
                temp = author.strip()
                if temp is not '':
                    authors.append(temp)
            tags = response.css('div.post-tags > a.tag-link::text').getall()

            def find_and_insert(_tag, _author):
                _author_id = Author.find_id_by_name(_author)
                _article = Article(title, url, text, publication_date, _author_id, _tag)
                if Article.find(title, _author_id, _tag):
                    return
                if not from_scratch:
                    self.new_articles_len += 1
                    _article.id = Article.get_max_id() + 1
                _article.save_to_db()

            if len(tags) > len(authors):
                for tag in tags:
                    for author in authors:
                        find_and_insert(tag, author)
            else:
                for author in authors:
                    for tag in tags:
                        find_and_insert(tag, author)

    def parse(self, response):
        """Function to parse /all-authors/ page and get url to each author page"""
        globals()['from_scratch'] = not Database.initialise(
            database="blog", user="root", password="root", host="localhost")
        if globals()['from_scratch']:
            logging.info('Getting urls to authors pages -> {url}'.format(url=response.url))
            logging.info('Urls collected. Starting iteration process . . .')
        else:
            logging.info('Looking for a new authors . . .')
        authors_list = response.css('div.postsrow > div.row.viewmore > a.viewauthor::attr(href)').getall()
        counter = 0
        for author in authors_list:
            counter += 1
            yield response.follow(author, self.parse_author)
        lost_authors = ('/author/ezra/',
                        '/author/anton/',
                        '/author/pavel-vasilyev/')
        # these authors exists, but they are not displayed at /all-authors/ page
        for url in lost_authors:
            counter += 1
            yield response.follow(url, self.parse_author)
        self.authors_len = counter - 1

    def close(self, reason):
        """Function to explicitly close spider"""
        if not from_scratch:
            self.authors_len = self.new_authors_len
            self.articles_len = self.new_articles_len
        logging.info('Spider closed. '
                     '{authors_len} Author(s) extracted to "{authors_table}" table, '
                     '{articles_len} Article(s) extracted to "{articles_table}" table.'
                     .format(authors_len=self.authors_len,
                             authors_table=Database.default_schema + '.' + self.output_authors,
                             articles_len=self.articles_len,
                             articles_table=Database.default_schema + '.' + self.output_articles))
