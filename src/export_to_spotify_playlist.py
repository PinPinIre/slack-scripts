import sys
import os
import json
import argparse
import re
from urlparse import urlparse, parse_qs
from datetime import datetime

from elasticsearch import Elasticsearch, ElasticsearchException
from elasticsearch_dsl import Search

from spotify_wrapper import SpotifyWrapper

TRACK_REGEX = 'track.'
SONG_ID_LENGTH = 22
# TODO:The elasticsearch functions here could be abstracted out into a new file


def get_all_elastic_links(index, service_name="Spotify"):
    """
    Query Elasticsearch and get a list of all links for a service
    """
    # TODO: Create an Elasticsearch wrapper and add this there
    client = Elasticsearch(index=index)
    search = Search(using=client, index=index)\
        .source(include=["attachments.from_url"])\
        .query("match", attachments__service_name=service_name)
    return search


def __es_has_link(elastic_result):
    """
    Check if a result from Elastic search has link attachments
    """
    return len(elastic_result.attachments) is not 0


def __is_a_track(link):
    """
    Determines if it's a track based on whether it has 'track' in the link
    """
    return 'track' in link


def _get_track_id(link):
    """
    The common pattern for tracks urls is track(/|:)[base64 hash]
    This crudely gets the base64 hash
    """
    pattern = re.compile(TRACK_REGEX)
    track_id = pattern.split(link)[1]
    return track_id[0:SONG_ID_LENGTH]


def create_playlist(username, secrets_file, playlist):
    """
    Creates playlist for the specified user
    Returns the created playlists URI
    """
    spotify = SpotifyWrapper(username, secrets_file)
    playlist = spotify.create_playlist(playlist)
    return playlist['uri']


def get_track_ids(index):
    """
    Queries Elasticsearch to get all links that were from the Spotify service,
    then filters out albums/playlists and then returns the unique hash for the
    remaining songs.
    """
    es_results = filter(__es_has_link, [r for r in get_all_elastic_links(index).scan()])
    links = map(lambda x: x.attachments[0].from_url, es_results)
    tracks = filter(__is_a_track, links)
    return map(_get_track_id, tracks)


def add_tracks_to_playlist(username, secrets_file, track_ids, playlist_uri):
    """
    Adds a list of track ids to a spotify playlist
    """
    spotify = SpotifyWrapper(username, secrets_file)
    spotify.add_songs_to_playlist(track_ids, playlist_uri)


def main():
    parser = argparse.ArgumentParser(description='Export Spotify links from a \
        slack channel stored in Elasticsearch')
    parser.add_argument('--username', help='username of the user')
    parser.add_argument('--playlist', help='name of playlist')
    parser.add_argument('--index', help='Elasticsearch index name')
    parser.add_argument('--secrets', help='secrets file')
    args = parser.parse_args()
    with open(args.secrets) as json_file:
        secrets_file = json.load(json_file)
    playlist_uri = create_playlist(args.username, secrets_file, args.playlist)
    track_ids = get_track_ids(args.index)
    add_tracks_to_playlist(args.username, secrets_file, track_ids, playlist_uri)

if __name__ == "__main__":
    main()
