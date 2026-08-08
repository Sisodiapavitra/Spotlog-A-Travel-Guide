from django.apps import AppConfig


class TweetConfig(AppConfig):
    name = 'tweet'
    
    def ready(self):
        import tweet.signals
