import logging
import os
from typing import Any, BinaryIO

from luna_kit.file_utils import PathOrBinaryFile, get_filesize, open_binary
import requests

from .config import Config


class WikiBot:
    config: Config
    session: requests.Session
    _csrf_token: str = ''
    chunk_size: int = 5000

    
    def __init__(self, config: Config) -> None:
        self.config = config
        self.session = requests.Session()
        self.url = self.config.wiki.url
        if self.config.wiki.chunk_size:
            self.chunk_size = self.config.wiki.chunk_size
        self._login()
    
    def _get_params(self, action: str, format: str = 'json', **params: Any):
        if not self._csrf_token:
            raise ValueError("Not logged in")
        
        return {
            'action': action,
            'format': format,
            "token": self._csrf_token,
            **params,
        }
    
    def _login(self):
        if not self.config.wiki.url:
            raise ValueError("No wiki url se")
        
        response = self.session.get(self.config.wiki.url, params = {
            "format": "json",
            "action": "query",
            "meta": "tokens",
            "type": "login",
        })
        response.raise_for_status()
        login_token = response.json()["query"]["tokens"]["logintoken"]

        response = self.session.post(self.url, data = {
            "format": "json",
            "action": "login",
            "lgname": self.config.wiki.username,
            "lgpassword": self.config.wiki.password,
            "lgtoken": login_token,
        })
        response.raise_for_status()

        response = self.session.get(self.url, params = {
            "format":"json",
            "action": "query",
            "meta":"tokens",
        })
        response.raise_for_status()
        self._csrf_token = response.json()["query"]["tokens"]["csrftoken"]

        if not self._csrf_token:
            raise ValueError("Could not get csrf token")
    
    def logout(self):
        params = self._get_params(action = 'logout')
        response = self.session.post(self.url, data = params)
        self._csrf_token = ''
        return response.json()
    
    def upload_file(self, name: str, target_file: PathOrBinaryFile):
        with open_binary(target_file, 'r') as file:
            filesize = get_filesize(file)
            file.seek(0)

            if filesize > self.chunk_size:
                return self._upload_chunked_file(name, file, filesize)
            else:
                return self._upload_file(name, file)

    
    def _upload_file(self, name: str, target_file: BinaryIO):
        logging.debug(f'Uploading {name} as one request')

        file_data = {
            "file": (
                name,
                target_file,
                'multipart/form-data',
            )
        }

        response = self.session.post(
            self.url,
            files = file_data,
            data = self._get_params(
                action = 'upload',
                filename = name,
                ignorewarnings = 1,
                comment = f"Uploaded {name} from pony-turnarounds bot",
            ),
        )
        response.raise_for_status()
        return response.json()
    
    def _upload_chunked_file(self, name: str, target_file: BinaryIO, filesize: int):
        logging.debug(f'Uploading {name} as chunks')

        offset = 0
        filekey: str | None = None
        ext = os.path.splitext(name)[1]

        for i, chunk in enumerate(read_chunks(target_file, self.chunk_size)):
            params = self._get_params(
                action = "upload",
                stash = 1,
                offset = offset,
                filename = name,
                filesize = filesize,
                ignorewarnings = 1,
            )

            if filekey:
                params['filekey'] = filekey
            
            file_data = {
                'chunk':(
                    f'{i}{ext}',
                    chunk,
                    'multipart/form-data',
                )
            }

            response = self.session.post(
                self.url,
                files = file_data,
                data = params,
            )

            data = response.json()
            filekey = data["upload"]["filekey"]
            if data['upload']['result'] == 'Continue':
                offset = data["upload"]["offset"]
        
        response = self.session.post(
            self.url,
            data = self._get_params(
                action = 'upload',
                filename = name,
                filekey = filekey,
                comment = f"Uploaded {name} from pony-turnarounds bot",
            )
        )

        return response.json()


def read_chunks(file_object: BinaryIO, chunk_size: int):
    """Return the next chunk of the file"""

    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data
