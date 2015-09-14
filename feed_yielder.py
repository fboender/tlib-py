# Copyright (c) 2015 Ferry Boender
# 
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
# 
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

__VERSION__ = (0, 1)

"""
The FeedYielder module yields new items from RSS or Atom feeds in the correct
order.

Example:

>>> f = FeedYielder('https://www.reddit.com/r/all/.rss')
>>> f.poll()
"""

import feedparser
import time
import logging
import json


class FieldYielderError(Exception):
    pass


class FeedYielder:
    """
    Yield new items from RSS or Atom feed in correct order.
    """
    def __init__(self, url, interval=3600, last_seen=None, last_id=None):
        """
        Create a new FeedYielder. `url` is an url or path pointing to an
        RSS or Atom feed. `interval` in seconds determines how often the feed
        will be reloaded. `last_seen` is a unix timestamp (time.time()) of when
        the feed was last seen. If `interval` seconds has elapsed since then,
        the feed will be reread. `last_id` is the last item id (guid for RSS,
        id from Atom feeds) that was seen. This is used to figure out which
        items are new.

        By default, the feed isn't read for the first time until `interval` has
        elapsed. If you want it to be read right away, pass 0 as the last_seen
        value.
        """
        self.url = url
        self.interval = interval
        if last_seen is not None:
            self.last_seen = last_seen
        else:
            self.last_seen = time.time()
        self.last_id = last_id
        self.changed = False
        self.log = logging.getLogger('FEEDYIELDER')

    def poll(self):
        """
        Check the feed for new items. If the interval since the last time the
        feed has been fetched has not elapsed, it returns an empty list without
        rereading the feed.  Otherwise, it yields a new item each time in the
        order they were published in.
        """
        self.changed = False
        now = time.time()
        if not self._interval_elapsed(now):
            return
        self.last_seen = now
        self.changed = True

        feed = self._read_feed()
        new_items = self._get_new_items(feed)
        if new_items:
            self.last_id = new_items[0]['id']
            for new_item in reversed(new_items):
                yield new_item

    def _get_new_items(self, feed):
        """
        Return a list of new items that have appeared in the feed since last
        time.
        """
        new_items = []
        for item in feed['items']:
            if item['id'] == self.last_id:
                break
            new_items.append(item)

        return new_items

    def _read_feed(self):
        """
        Read the feed and return it. If errors are detected, raises a
        FeedYielderError.
        """
        self.log.debug("Reading feed {}".format(self.url))
        feed = feedparser.parse(self.url)
        if 'status' in feed and feed['status'] != 200:
            raise FieldYielderError(
                'Feed returned HTTP error status {}'.format(feed['status'])
            )
        if 'bozo' in feed and feed['bozo']:
            raise FieldYielderError(
                'Feed parse error: {}'.format(feed.bozo_exception)
            )

        return feed

    def _interval_elapsed(self, now):
        """
        Returns True if the interval between having seen the feed for the last
        time has elapsed. Otherwise, returns False
        """
        return self.last_seen + self.interval < now

    def get_status(self):
        """
        Return a dictionary with the last_seen and last_id values.
        """
        return {
            "last_seen": self.last_seen,
            "last_id": self.last_id,
        }

    def __repr__(self):
        return "<FieldYielder url='{}'>".format(self.url)


class MultiFeedYielder:
    def __init__(self, persist_path=None):
        self.persist_path = persist_path
        self.feeds = []
        self._feed_status = self._load_status()
        self.log = logging.getLogger('MULTIFEEDYIELDER')

    def add_feed(self, url, interval, last_seen=None, last_id=None):
        if url in self._feed_status:
            # Override params with persisted state
            last_seen = self._feed_status[url]['last_seen']
            last_id = self._feed_status[url]['last_id']
        feed = FeedYielder(url, interval, last_seen, last_id)
        self.feeds.append(feed)

    def poll(self):
        changed = False
        new_items = []
        for feed in self.feeds:
            for new_item in feed.poll():
                new_items.append(
                    (feed, new_item)
                )
            if feed.changed:
                changed = True

        if changed:
            self._save_status()

        return new_items

    def _load_status(self):
        feed_status = {}
        if self.persist_path is not None:
            try:
                feed_status = json.load(file(self.persist_path, 'r'))
            except IOError:
                pass
        return feed_status

    def _save_status(self):
        self.log.debug("Saving changed feed status")
        feed_status = {}
        for feed in self.feeds:
            feed_status[feed.url] = feed.get_status()

        json.dump(feed_status, file(self.persist_path, 'w'))

    def dump(self):
        import pprint
        pprint.pprint(self.feeds)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    mfy = MultiFeedYielder('feed_status.json')
    mfy.add_feed('/home/fboender/reddit.rss', interval=50, last_seen=0)
    mfy.add_feed('/home/fboender/cataclysm.rss', interval=5, last_seen=0)
    mfy.add_feed('/home/fboender/fboender.private.atom', interval=5, last_seen=0)
    mfy.dump()

    import pprint
    import time
    while True:
        pprint.pprint(mfy.poll())
        time.sleep(1)
