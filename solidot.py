import os
import json

import feedparser
import requests

from datetime import datetime
from typing import Dict, Any


RSS_URL = "https://www.solidot.org/index.rss"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
DATE_FORMAT = "%a, %d %b %Y %H:%M:%S %z"
RUN_INTERVAL = 10 * 60 # 10 分钟跑一次
session = requests.Session()


def get_current_feeds():
    """
    Retrieve the current feeds from the RSS_URL.

    Returns:
        List[FeedEntry]: A list of feed entries that meet the specified criteria.
    """
    feeds = []
    feed = feedparser.parse(RSS_URL)
    for entry in feed.entries:
        published_date = datetime.strptime(entry.published, DATE_FORMAT)
        now = datetime.now(tz=published_date.tzinfo)
        print(f"{entry.title} published at {published_date}, now {now}")
        if (now.timestamp() - published_date.timestamp()) > RUN_INTERVAL:
            print("already send, skip")
            continue

        feeds.append(entry)

    return feeds


def gen_lark_msg_card(feed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates a Lark message card based on the provided feed.

    Args:
        feed (Dict[str, Any]): The feed data used to generate the message card.

    Returns:
        Dict[str, Any]: The generated Lark message card.

    Raises:
        None
    """
    published_date = datetime.strptime(feed.published, DATE_FORMAT)
    card = {
        "config": {"wide_screen_mode": True},
        "elements": [
            {
                "tag": "div",
                "text": {
                    "content": feed.summary_detail.value,
                    "tag": "lark_md"
                }
            },
            {
                "actions": [
                    {
                        "tag": "button",
                        "text": {
                            "content": "查看详情",
                            "tag": "plain_text"
                        },
                        "type": "default",
                        "multi_url": {"url": feed.link}
                    }
                ],
                "tag": "action"
            },
            {
                "tag": "hr"
            },
            {
                "elements": [
                    {
                        "content": f"发表于 {published_date.strftime('%Y-%m-%d %H:%M:%S')}",
                        "tag": "plain_text"
                    }
                ],
                "tag": "note"
            }
        ],
        "header": {
            "template": "wathet",
            "title": {
                "content": feed.title,
                "tag": "plain_text"
            }
        }
    }
    return {"msg_type": "interactive","card": json.dumps(card)}


def send_to_lark(feeds):
    """
    Send the feeds to the Lark webhook.

    Args:
        feeds (List[FeedEntry]): A list of feed entries that meet the specified criteria.
    """
    if not WEBHOOK_URL:
        print("webhook not found")
        return

    print(f"found {len(feeds)} post, start send to lark")
    for feed in feeds:
        card = gen_lark_msg_card(feed)
        resp = session.post(WEBHOOK_URL, json=card)
        print(f"send to lark: {feed.title}, resp: {resp.text}")


if __name__ == "__main__":
    print("start run")
    send_to_lark(get_current_feeds())
    print("send done")
