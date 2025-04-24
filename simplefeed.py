#!/usr/bin/env python

from argparse import ArgumentParser
from math import ceil
from pathlib import Path
import sys
from instagram_private_api import Client
from datetime import datetime, timedelta
import requests
from tqdm import tqdm
import smtplib
import shutil
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from credentials import (
    Instagram as InstagramCredentials,
    Gmail as GmailCredentials
)

PROJECT_ROOT = Path(__file__).absolute().parents[1]
sys.path.append(str(PROJECT_ROOT))


BIO_PATTERN = r'\bbio\b|\bbio\.'

MAX_POSTS = 300
DEFAULT_WINDOW = 24  # hours
LAST_SUCCESS_FILE = "last_success.txt"


class SimpleFeed:
    def __init__(self, *args, **kwargs):
        self.input = kwargs['input']
        self.window = self.get_window(kwargs['window'])
        self.api = Client(
            InstagramCredentials.USERNAME,
            InstagramCredentials.PASSWORD
        )
        self.search_terms = self.load_search_terms()
        self.tmp_dir = Path('tmp')
        self.tmp_dir.mkdir(exist_ok=True)

    def get_window(self, window):
        if window:
            return int(window)
        try:
            with open(LAST_SUCCESS_FILE) as f:
                last_run = datetime.fromisoformat(f.read().strip())
                hours = ceil((datetime.now() - last_run).total_seconds() / 3600)
                return int(hours)
        except FileNotFoundError:
            return DEFAULT_WINDOW
        except ValueError:
            print("Invalid datetime format in last_success file")
            return 24

    def load_search_terms(self):
        search_terms = set()
        with open(self.input) as f:
            search_terms = {line.strip().lower() for line in f}

        return search_terms

    def get_stats(self, posts):
        unique_posts = set()
        date_counts = {}
        for post in posts:
            if 'media_or_ad' in post:
                unique_posts.add(post['media_or_ad']['pk'])
                date = datetime.fromtimestamp(post['media_or_ad']['taken_at'])
                date = date.date()
                date_counts[date] = date_counts.get(date, 0) + 1

        print(f"Total unique posts: {len(unique_posts)}")
        print("\nPosts by date:")
        for date, count in sorted(date_counts.items()):
            print(f"{date}: {count} posts")

    def parse_post(self, post):
        if 'media_or_ad' not in post:
            return None
        media = post['media_or_ad']

        caption = media.get('caption', {})
        caption_text = ''
        if isinstance(caption, dict):
            caption_text = caption.get('text', '')

        photo_url = None
        if media.get('carousel_media'):
            mask = media['carousel_media'][0]['image_versions2']
            photo_url = mask['candidates'][0]['url']

        return {
            'caption': caption_text,
            'timestamp': media['taken_at'],
            'user': media['user']['username'],
            'user_id': media['user']['pk'],
            'photo_url': photo_url
        }

    def get_posts(self):
        posts = []
        feed = self.api.feed_timeline()
        posts.extend(feed.get('feed_items', []))
        max_posts = MAX_POSTS

        pbar = tqdm(total=max_posts, desc="Fetching posts")
        pbar.update(len(posts))

        while feed.get('next_max_id') and len(posts) < max_posts:
            feed = self.api.feed_timeline(max_id=feed['next_max_id'])
            new_posts = feed.get('feed_items', [])
            posts.extend(new_posts)
            pbar.update(len(new_posts))

        pbar.close()

        self.get_stats(posts)

        return posts

    def process_posts(self, posts):
        cutoff = datetime.now() - timedelta(hours=self.window)
        content = []
        files = []
        matched_posts = []

        for post in posts:
            post = self.parse_post(post)
            if not post:
                continue

            post_time = datetime.fromtimestamp(post['timestamp'])
            if post_time < cutoff:
                continue

            caption_words = set(post['caption'].lower().split())
            matches = [
                term for term in self.search_terms if term in caption_words
            ]

            if matches:
                img_name = f"{post['user']}_{post['timestamp']}"
                caption = post['caption']

                if re.search(BIO_PATTERN, caption, re.IGNORECASE):
                    user_info = self.api.user_info(post['user_id'])
                    if user_info['user'].get('bio_links'):
                        bio_urls = [
                            link['url'] for link in user_info['user']['bio_links']
                        ]
                        if bio_urls:
                            if len(bio_urls) == 1:
                                caption = re.sub(
                                    BIO_PATTERN,
                                    f"<a href='{bio_urls[0]}'>bio</a>",
                                    caption,
                                    flags=re.IGNORECASE
                                )
                            else:
                                numbered_links = ' '.join(
                                    f"<a href='{url}'>[{i+1}]</a>"
                                    for i, url in enumerate(bio_urls)
                                )
                                caption += f"\n\nBio links: {numbered_links}"

                post_content = (
                    f"<b>Date:</b> {post_time.strftime('%Y-%m-%d %H:%M')}<br>"
                    f"<b>Matching terms:</b> {', '.join(matches)}<br>"
                    f"<b>User:</b> @{post['user']}<br>"
                    f"<b>Caption:</b> {caption}<br>"
                    f"<img src='cid:{img_name}'><hr>"
                )

                matched_posts.append({
                    'date': post_time,
                    'content': post_content,
                    'photo_url': post['photo_url'],
                    'timestamp': post['timestamp'],
                    'user': post['user']
                })

        matched_posts.sort(key=lambda x: x['date'])

        for post in matched_posts:
            content.append(post['content'])
            if post['photo_url']:
                img_name = self.tmp_dir / f"{post['user']}_{post['timestamp']}.jpg"
                img_data = requests.get(post['photo_url']).content
                with open(img_name, 'wb') as f:
                    f.write(img_data)
                    files.append(img_name)

        return content, files

    def send_msg(self, content, files):
        msg = MIMEMultipart()
        msg['From'] = GmailCredentials.EMAIL
        msg['To'] = GmailCredentials.EMAIL
        msg['Subject'] = f"SimpleFeed Newsletter {datetime.today().date()}"
        msg.attach(MIMEText("\n\n".join(content), 'html'))
        for file in files:
            with open(file, 'rb') as f:
                img = MIMEImage(f.read())
                img.add_header('Content-ID', f'<{file}>')
                msg.attach(img)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GmailCredentials.EMAIL, GmailCredentials.PASSWORD)
        server.send_message(msg)
        server.quit()

        return True

    def run(self):
        retval = 0
        try:
            posts = self.get_posts()
            content, files = self.process_posts(posts)

            if content:
                self.send_msg(content, files)
                with open(LAST_SUCCESS_FILE, 'w') as f:
                    f.write(datetime.now().isoformat())
            else:
                print("No matching posts found.")
                retval = 1
        finally:
            shutil.rmtree(self.tmp_dir)

        return retval


def main():
    description = 'SimpleFeed'

    parser = ArgumentParser(description=description)
    parser.add_argument(
        '-i',
        '--input',
        dest='input',
        required=True,
        help='Input csv containing search terms'
    )
    parser.add_argument(
        '-w',
        '--window',
        dest='window',
        help='Window to look back in hrs (default 24)'
    )

    args = parser.parse_args()
    input = args.input
    window = args.window

    simple_feed = SimpleFeed(input=input, window=window)
    retval = simple_feed.run()

    return retval


if __name__ == '__main__':
    retval = main()
    sys.exit(retval)
