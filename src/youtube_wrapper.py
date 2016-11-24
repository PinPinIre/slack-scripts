import httplib2
import os
import sys
import json

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow


class YoutubeWrapper(object):

    # This variable defines a message to display if the CLIENT_SECRETS_FILE
    # is missing.
    MISSING_SECRETS_MSG = "WARNING: Please configure OAuth 2.0"
    # This OAuth 2.0 access scope allows for full read/write access to the
    # authenticated user's account.
    YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"
    YOUTUBE_API_SERVICE_NAME = "youtube"
    YOUTUBE_API_VERSION = "v3"

    def __init__(self, client_secrets_file):
        self.secrets_file = client_secrets_file
        self.youtube = self.__get_client()

    def __get_client(self):
        """
        Most of this is the Google boilerplate code. This will get a client to
        access the Youtube API
        """
        flow = flow_from_clientsecrets(self.secrets_file,
                                       message=self.MISSING_SECRETS_MSG,
                                       scope=self.YOUTUBE_READ_WRITE_SCOPE)

        # TODO: Fix this! Came with boilerplate
        storage = Storage("%s-oauth2.json" % sys.argv[0])
        credentials = storage.get()

        if credentials is None or credentials.invalid:
            flags = argparser.parse_args()
            credentials = run_flow(flow, storage, flags)

        youtube = build(self.YOUTUBE_API_SERVICE_NAME,
                        self.YOUTUBE_API_VERSION,
                        http=credentials.authorize(httplib2.Http()))
        return youtube

    def create_playlist(self, title, description=""):
        """
        Create a new Youtube playlist.
        Returns request respons
        """
        if self.youtube is None:
            self.youtube = __get_client()
        # This code creates a new, private playlist in the authorized user's
        # channel.
        playlists_insert_response = self.youtube.playlists().insert(
          part="snippet,status",
          body = {
            "snippet": {
              "title": title,
              "description": description
            },
            "status": {
              "privacyStatus": "private"
            }
          }
        ).execute()
        return playlists_insert_response

    def get_playlists(self):
        """
        Get all the playlists for the current user
        """
        if self.youtube is None:
            self.youtube = __get_client()
        return self.youtube.playlists().list(part="snippet", mine=True)\
            .execute()

    def get_playlist_items(self, playlist_id):
        """
        Get all of the playlist items from a playlist.
        Returns a list of playlistItems
        """
        return_val = []
        max_window = 50
        if self.youtube is None:
            self.youtube = __get_client()
        count = 1
        response = self.youtube.playlistItems()\
            .list(part="snippet",
                  playlistId=playlist_id,
                  maxResults=max_window).execute()
        return_val = return_val + response['items']
        while 'nextPageToken' in response:
            # response has nextPageToken and prevPageToken properties
            response = self.youtube.playlistItems()\
                .list(part="snippet",
                      playlistId=playlist_id,
                      maxResults=max_window,
                      pageToken=response['nextPageToken'])\
                .execute()
            return_val = return_val + response['items']
        return return_val

    def add_video_to_playlist(self, video_id, playlist_id):
        """
        Add a video id to a playlists
        Returns None
        """
        if self.youtube is None:
            self.youtube = __get_client()
        self.youtube.playlistItems().insert(
            part="snippet",
            body={
                    'snippet': {
                      'playlistId': playlist_id,
                      'resourceId': {
                              'kind': 'youtube#video',
                              'videoId': video_id
                        }
                    }
            }
        ).execute()
