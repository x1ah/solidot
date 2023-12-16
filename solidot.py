import os
import json

import feedparser
import requests

from datetime import datetime
from typing import Dict, Any


RSS_URL = "https://www.solidot.org/index.rss"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
DATE_FORMAT = "%a, %d %b %Y %H:%M:%S %z"
CACHE_PATH = ".cache"
CACHE_FILE = "index.json"

session = requests.Session()
log = lambda message: print(f"[{datetime.now()}] {message}")

def load_cache_data():
    """
    Load the cache data from the file.

    Returns:
        Dict[str, Any]: The loaded cache data.
    """
    if not os.path.exists(f"{CACHE_PATH}/{CACHE_FILE}"):
        return {}
    
    with open(f"{CACHE_PATH}/{CACHE_FILE}", "r") as f:
        return json.load(f)
    

def refresh_cache_data(feeds):
    """
    Refresh the cache data with the provided feeds.

    Args:
        feeds (List[FeedEntry]): The list of feed entries to be cached.

    Returns:
        None
    """
    if not os.path.exists(CACHE_PATH):
        os.makedirs(CACHE_PATH)

    with open(f"{CACHE_PATH}/{CACHE_FILE}", "w") as f:
        json.dump(feeds, f)


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
        log("webhook not found")
        return

    log(f"found {len(feeds)} post, start send to lark")
    for feed in feeds:
        card = gen_lark_msg_card(feed)
        resp = session.post(WEBHOOK_URL, json=card)
        log(f"send to lark: {feed.title}, resp: {resp.text}")


cached_feeds = load_cache_data()


def filter_sent_feeds(feeds):
    """
    Filter the feeds that have already been sent.

    Args:
        feeds (List[FeedEntry]): A list of feed entries that meet the specified criteria.

    Returns:
        List[FeedEntry]: The filtered list of feed entries.
    """
    new_feeds = []
    for feed in feeds:
        if feed.link in cached_feeds:
            continue
        new_feeds.append(feed)

    return new_feeds


def gen_new_cache_data(feeds):
    new_index = {feed.link: True for feed in feeds}
    if len(cached_feeds) > 100:
        return new_index
    
    return (new_index | cached_feeds)


if __name__ == "__main__":
    log("start run")
    feed = feedparser.parse(RSS_URL)
    fresh_feeds = filter_sent_feeds(feed.entries)
    if not fresh_feeds:
        log("no new post")
        exit(0)

    log(f"found {len(fresh_feeds)} new post, start send to lark")
    send_to_lark(fresh_feeds)
    refresh_cache_data(gen_new_cache_data(feed.entries))
    log("send done")
