from django.db import models

import re
from datetime import datetime
from datetime import timedelta

from bs4 import BeautifulSoup


class Post(models.Model):

    s3_object_id = models.TextField(default=None)
    data_id = models.TextField(default=None)
    company_name = models.TextField(default=None)
    raw_title = models.TextField(default=None)
    created_date = models.DateTimeField(auto_now=True)
    post_date = models.DateTimeField(auto_now=False, default=None)

    @staticmethod
    def create_posts(post_data, filename):
        if post_data:
            for item in post_data:
                post = Post(data_id=item.get('data_id'),
                            raw_title=item.get('raw_title'),
                            post_date=item.get('post_date'),
                            s3_object_id=filename,
                            company_name=item.get('company_name'))
                post.save()

    @staticmethod
    def scrape_feed(filename, file_content):
        soup = BeautifulSoup(file_content, 'html.parser')
        feed = soup.find('div', id='organization-feed')
        data_ids = Post.get_post_ids(feed)
        raw_titles = Post.get_post_title(feed)
        post_dates = Post.get_post_date(feed)
        company_name = Post.get_name(filename)
        return Post.consolidate_data(data_ids, raw_titles, post_dates, company_name)

    @staticmethod
    def consolidate_data(data_ids, raw_titles, post_dates, company_name):
        zip_data = list(zip(data_ids, raw_titles, post_dates))

        data = []
        for d in zip_data:
            temp = {}
            temp['company_name'] = company_name
            temp['data_id'] = d[0]
            temp['raw_title'] = d[1]
            temp['post_date'] = d[2]
            data.append(temp)
        return data

    @staticmethod
    def multiple_replace(adict, text):
        regex = re.compile("|".join(map(re.escape, adict.keys())))
        return regex.sub(lambda match: adict[match.group(0)], text)

    @staticmethod
    def get_post_title(file):
        divs = file.find_all('div', class_='feed-shared-update-v2__description')
        raw_titles = [div.text.strip().replace('\n', '') for div in divs]

        replace_dict = {'#hashtag': '#',
                        'hashtag#': '#',
                        'see more': '',
                        '...see more': ''}

        return [Post.multiple_replace(replace_dict, title) for title in raw_titles]

    @staticmethod
    def get_post_ids(file):
        divs = file.find_all(attrs={'data-id': True})
        raw_post_ids = [div['data-id'] for div in divs]

        promotion_regex = re.compile(r'l2mPromotion')
        for raw_post_id in raw_post_ids:
            if re.search(promotion_regex, raw_post_id):
                raw_post_ids.remove(raw_post_id)
        return [x.strip('urn:li:activity:') for x in raw_post_ids]

    @staticmethod
    def get_post_date(file):
        divs = file.find_all('span', class_='feed-shared-actor__sub-description')
        raw_post_dates = [div.text.strip() for div in divs]
        return [Post.resolve_post_date(date) for date in raw_post_dates]

    @staticmethod
    def resolve_post_date(date):
        current_datetime = datetime.now().date()
        date_regex = re.compile(r'(\d+)(mo|m|h|d|w|y)')
        result = re.match(date_regex, date)
        if result:
            number = int(result.group(1))
            unit = result.group(2)
        else:
            return None

        if unit == 'm':
            delta = timedelta(minutes=number)
        elif unit == 'h':
            delta = timedelta(hours=number)
        elif unit == 'd':
            delta = timedelta(days=number)
        elif unit == 'w':
            delta = timedelta(weeks=number)
        elif unit == 'mo':
            multiplier = 30 * number
            delta = timedelta(days=multiplier)
        elif unit == 'y':
            multiplier = 365 * number
            delta = timedelta(days=multiplier)

        return current_datetime - delta

    @staticmethod
    def get_name(file):
        return file.find('h1', class_='org-top-card-summary__title')['title']
