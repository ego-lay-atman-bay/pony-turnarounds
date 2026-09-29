import logging
import urllib.parse

from luna_kit.file_utils import PathOrBinaryFile, open_binary
import mwclient
import mwclient.image
import requests

from .config import Config


class WikiBot:
    config: Config
    api: mwclient.Site
    _csrf_token: str = ''

    
    def __init__(self, config: Config) -> None:
        self.config = config
        
        if not self.config.wiki.url or not self.config.wiki.username or not self.config.wiki.password:
            raise ValueError("Cannot log in, must have url, username, and password")
        
        parsed_url = urllib.parse.urlparse(self.config.wiki.url)
        
        if not parsed_url.netloc:
            raise ValueError("Malformed url, make sure it includes the scheme (https://)")

        
        path = parsed_url.path.strip('api.php')
        if not path.endswith('/'):
            path += '/'
        self.api = mwclient.Site(parsed_url.netloc, path)

        self._login()
    
    def _login(self):
        self.api.login(self.config.wiki.username, self.config.wiki.password)
    
    def upload_file(self, name: str, target_file: PathOrBinaryFile):
        page: mwclient.image.Image = self.api.images[name]
        if page.exists:
            logging.info(f"File '{name}' already exists, skipping")
            return
        
        with open_binary(target_file, 'r') as file:
            self.api.upload(file, name, ignore = True, comment = f'File "{name}" uploaded by pony-turnarounds bot')
