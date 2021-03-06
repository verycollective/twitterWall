from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream

import configparser
import csv


class TwitterAuthenticator():
    """Class for streaming and processing live tweets."""

    def authenticate(self):
        config = configparser.ConfigParser()
        config.readfp(open(r'config.cfg'))
        cred = config['TWITTER CREDENTIALS']

        auth = OAuthHandler(cred['CONSUMER_KEY'], cred['CONSUMER_SECRET'])
        auth.set_access_token(cred['ACCESS_TOKEN'], cred['ACCESS_TOKEN_SECRET'])
        return auth


class TwitterStreamer():
    """Class for streaming and processing live tweets."""

    def __init__(self):
        self.authenticator = TwitterAuthenticator()

    def stream_tweets(self, save_to, keywords=':)', lang='en'):
        # Handles auth and connection to API
        auth = self.authenticator.authenticate()

        listener = TwitterListener(save_to)
        stream = Stream(auth, listener, tweet_mode='extended')
        stream.filter(track=keywords, is_async=True, languages=lang)
        # myStream.filter(follow=["2211149702"])


class TwitterListener(StreamListener):
    """Listener Class to handle twitter streams."""

    STATUS = 'FOR_REVIEW'
    stay_connected = True
    next_screen_id = 0

    def cleanup(self, s):
        s_ = ''.join([i if ord(i) < 128 else ' ' for i in s])
        s_ = s_.replace('\n', ' ').replace('\r', '')
        return s_

    def get_last_id(self):
        id = 0
        with open(self.save_to, "r") as file:
            for line in file:
                last = line[-3:].strip(',')
                last = last.strip('\n')
                if last.isdigit():
                    id = int(last)
        return id

    def __init__(self, save_to):
        super().__init__()
        self.save_to = save_to
        self.next_screen_id = self.get_last_id()
        return

    def on_status(self, status):
        # Start with doing some filtering
        # avoid retweets
        if hasattr(status, 'retweeted_status'):
            if (status.retweeted_status):
                print('retweet filtered')
                return
        # avoid replies
        # ! not working properly
        if hasattr(status, 'in_reply_to_status_id'):
            if (status.in_reply_to_status_id):
                print('reply filtered')
                return

        # status.user.description
        # status.user.location
        # status.user.screen_name
        # status.user.followers_count
        # status.text
        # status.created_at
        # status.retweet_count
        # geographic coordinates
        # status.coordinates

        media_files = set()
        media = status.entities.get('media', [])
        if(len(media) > 0):
            media_files.add(media[0]['media_url'])
            print('!!!!!!!!shouldhave downloaded something')

        self.next_screen_id = (self.next_screen_id % 16) + 1
        tweet = ''
        try:
            tweet = status.extended_tweet["full_text"]
        except:
            tweet = status.text
        data = [status.id, status.created_at,
                self.cleanup(status.user.screen_name),
                self.cleanup(tweet),
                self.STATUS,
                self.next_screen_id]
        print("From twitter listener")
        print(data)

        try:
            with open(self.save_to, 'a') as write_file:
                writer = csv.writer(write_file)
                writer.writerow(data)
            return self.stay_connected
        except BaseException as e:
            print ('Error on data {}'.format(e))
        return self.stay_connected

    def on_error(self, status_code):
        print (status_code)
        if status_code == 420:
            # disconnects the stream
            return False

    def on_timeout(self):
        print('Timeout error, keeping connection')
        # return True keeps connection alieve
        return False

    def disconnect(self):
        self.stay_connected = False
        return


if __name__ == '__main__':
    keywords = ['kristiansand', 'kilden', 'fake news']
    languages = ['en']
    db = 'db/tweets.csv'

    twitter_streamer = TwitterStreamer()
    twitter_streamer.stream_tweets(db, keywords, languages)
