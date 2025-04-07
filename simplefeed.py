#!/usr/bin/env python

from argparse import ArgumentParser
from pathlib import Path
import sys
from instagram_private_api import Client
from datetime import datetime, timedelta
import requests
import http
from tqdm import tqdm
from credentials import (
    Instagram as InstagramCredentials,
    Mailgun as MailgunCredentials
)

PROJECT_ROOT = Path(__file__).absolute().parents[1]
sys.path.append(str(PROJECT_ROOT))


class SimpleFeed:
    def __init__(self, *args, **kwargs):
        self.input = kwargs['input']
        self.address = kwargs['address']
        self.window = int(kwargs['window'])
        self.api = Client(
            InstagramCredentials.USERNAME,
            InstagramCredentials.PASSWORD
        )

    def parse_post(self, post):
        if 'media_or_ad' not in post:
            return None
        media = post['media_or_ad']
        caption = media.get('caption', {})
        caption_text = caption.get('text', '') if isinstance(caption, dict) else ''

        return {
            'caption': caption_text,
            'timestamp': media['taken_at'],
            'user': media['user']['username'],
            'photo_url': media['carousel_media'][0]['image_versions2']['candidates'][0]['url'] if media.get('carousel_media') else None
        }

    def run(self):
        # Read input CSV for search terms
        search_terms = set()
        with open(self.input) as f:
            search_terms = {line.strip().lower() for line in f}

        posts = []
        feed = self.api.feed_timeline()
        posts.extend(feed.get('feed_items', []))
        max_posts = 500

        pbar = tqdm(total=max_posts, desc="Fetching posts")
        pbar.update(len(posts))

        while feed.get('next_max_id') and len(posts) < max_posts:
            feed = self.api.feed_timeline(max_id=feed['next_max_id'])
            new_posts = feed.get('feed_items', [])
            posts.extend(new_posts)
            pbar.update(len(new_posts))

        breakpoint()
        cutoff = datetime.now() - timedelta(hours=self.window)

        email_content = []
        files = []

        unique_posts = set()
        date_counts = {}
        for post in posts:
            if 'media_or_ad' in post:
                unique_posts.add(post['media_or_ad']['pk'])
                date = datetime.fromtimestamp(post['media_or_ad']['taken_at']).date()
                date_counts[date] = date_counts.get(date, 0) + 1

        print(f"Total unique posts: {len(unique_posts)}")
        print("\nPosts by date:")
        for date, count in sorted(date_counts.items()):
            print(f"{date}: {count} posts")

        for post in posts:
            post = self.parse_post(post)
            if not post:
                continue
            post_time = datetime.fromtimestamp(post['timestamp'])

            if post_time < cutoff:
                continue

            caption_words = set(post['caption'].lower().split())
            matches = [term for term in search_terms if term in caption_words]

            if matches:
                email_content.append(
                    f"User: {post['user']}\n"
                    f"Caption: {post['caption']}\n"
                    f"Matching terms: {', '.join(matches)}\n"
                )

                if post['photo_url']:
                    img_name = f"img_{post['timestamp']}.jpg"
                    img_data = requests.get(post['photo_url']).content
                    with open(img_name, 'wb') as f:
                        f.write(img_data)
                        files.append(img_name)
        breakpoint()

        if email_content:
            auth = 'api', MailgunCredentials.API_KEY
            url = 'https://api.mailgun.net/v3/mg.alexshulman.com/messages'

            data = {
                'from': self.address,
                'to': self.address,
                'subject': f"SimpleFeed Newsletter {datetime.today()}",
                'text': "\n\n".join(email_content)
            }

            result = requests.post(url, auth=auth, data=data)

            return result.status_code == http.HTTPStatus.OK

        return 0


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
        '-a',
        '--address',
        dest='address',
        required=True,
        help='Recipient email'
    )
    parser.add_argument(
        '-w',
        '--window',
        dest='window',
        help='Window to look back in hrs (default 24)'
    )

    args = parser.parse_args()
    input = args.input
    address = args.address
    window = args.window

    simple_feed = SimpleFeed(input=input, address=address, window=window)
    retval = simple_feed.run()

    return retval


if __name__ == '__main__':
    retval = main()
    sys.exit(retval)
