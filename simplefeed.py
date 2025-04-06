#!/usr/bin/env python

"""
SimpleFeed
"""

from argparse import ArgumentParser
from pathlib import Path
import instaloader
from datetime import datetime, timedelta
import requests
from credentials import (
    Instagram as InstagramCredentials,
)

PROJECT_ROOT = Path(__file__).absolute().parents[1]
import sys; sys.path.append(str(PROJECT_ROOT))  # noqa


class SimpleFeed:
    def __init__(self, *args, **kwargs):
        self.input = kwargs['input']
        self.address = kwargs['address']
        self.window = int(kwargs['window'])

    def run(self):
        """
        Pull Instagram feed posts containing search term and email them
        """
        # Instagram login
        L = instaloader.Instaloader()
        L.login(
            InstagramCredentials.USERNAME,
            InstagramCredentials.PASSWORD
        )

        # Get posts
        posts = L.get_feed_posts()
        breakpoint()
        
        # cutoff_date = datetime.now() - timedelta(days=self.days)

        # # Prepare email
        # email_content = ""
        # files = []

        # # Get matching posts
        # for post in posts:
        #     if self.input.lower() in post.caption.lower() and post.date > cutoff_date:
        #         email_content += f"\n\nCaption: {post.caption}"
        #         L.download_pic(post.url, post.mediaid)
        #         files.append(("attachment", open(f"{post.mediaid}.jpg", "rb")))

        # # Send email
        # mailgun_url = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"
        # response = requests.post(
        #     mailgun_url,
        #     auth=("api", MAILGUN_API_KEY),
        #     data={"from": f"Simple Feed <feed@{MAILGUN_DOMAIN}>",
        #           "to": self.output,
        #           "subject": f"Instagram Posts Containing '{self.input}'",
        #           "text": email_content},
        #     files=files
        # )

        # return 0 if response.ok else 1


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
