import sys
import os
import json
import argparse
from urlparse import urlparse, parse_qs
from datetime import datetime

from elasticsearch import Elasticsearch, ElasticsearchException
from elasticsearch_dsl import Search
from youtube_wrapper import YoutubeWrapper

channel_prefixes = ['/channel', '/c/']
VIDEO_ID_LENGTH = 11
# TODO:The elasticsearch functions here could be abstracted out into a new file


def get_all_elastic_links(index, service_name="Youtube"):
    """
    Query Elasticsearch and get a list of all links for a service
    """
    # TODO: Create an Elasticsearch wrapper and add this there
    client = Elasticsearch(index=index)
    search = Search(using=client, index=index)\
        .source(include=["attachments.from_url"])\
        .query("match", attachments__service_name=service_name)
    return search


def get_video_id(link_response):
    """
    Parse a Youtube link to get the video_id
    """
    # TODO: Replace with regex? This is not nice
    link = link_response.attachments[0].from_url
    return_val = ''
    id_start = 1
    id_end = id_start + VIDEO_ID_LENGTH
    yt_url = urlparse(link)
    query_strings = parse_qs(yt_url.query)
    if 'v' in query_strings:
        # Some links are of the form ?v={ID}
        return_val = query_strings['v'][0]
    elif all([x not in yt_url.path for x in channel_prefixes]):
        # Others are variations on {host}/{id}?
        return_val = yt_url.path[id_start:id_end]  # nasty
    return unicode(return_val)


def __es_has_link(elastic_result):
    """
    Check if a result from Elastic search has link attachments
    """
    return len(elastic_result.attachments) is not 0


def export_to_youtube(ids, playlist_id, client):
    """
    Exports a list of Youtube video IDs to a playlist
    """
    # TODO: Maybe move this to youtube_wrapper?
    for idx in ids:
        try:
            client.add_video_to_playlist(idx, playlist_id)
        except Exception:
            #TODO: Log these errors properly
            print(sys.exc_info()[0])
            print("Exception on:\thttps://www.youtube.com/watch?v=" + idx)


def get_all_playlist_items(playlist_id, yt_client):
    """
    Get a list of video ids of videos currently in playlist
    """
    return yt_client.get_playlist_items(playlist_id)


def remove_duplicate_links(link_ids, yt_ids):
    """
    Returns the ids that are in link_ids but not in yt_ids
    """
    #TODO: Do this better
    return [x for x in set(link_ids) if x not in yt_ids]


def get_playlist_id(playlist_name, client):
    """
    Get a playlist called playlist_name, if it doesn't exist it creates it
    """
    playlists = client.get_playlists()
    # Find any matches
    playlist = next((p for p in playlists['items'] if p['snippet']['title'] == playlist_name), None)
    if playlist is None:
        # Create if doesn't exist
        playlist = client.create_playlist(playlist_name)
    return playlist['id']


def get_new_ids(index, playlist_name, client):
    """
    Gets a list of youtube videoIDs that are in the Elasticsearch index but not
    in the Youtube playlist
    """
    playlist_id = get_playlist_id(playlist_name, client)
    # Force evaluation of scan here since it can throw an exception if done
    # lazily (Elasticsearch timeout?)
    yt_links = filter(__es_has_link, [link for link in get_all_elastic_links(index).scan()])
    yt_ids = map(get_video_id, yt_links)
    playlist_items = get_all_playlist_items(playlist_id, client)
    playlist_ids = map(lambda x: x['snippet']['resourceId']['videoId'], playlist_items)
    unique = remove_duplicate_links(yt_ids, playlist_ids)
    return (playlist_id, unique)


def main():
    parser = argparse.ArgumentParser(description='Export Youtube links from a \
        slack channel stored in Elasticsearch')
    parser.add_argument('--playlist', help='name of playlist')
    parser.add_argument('--index', help='Elasticsearch index name')
    parser.add_argument('--secrets', help='path to client_secrets.json')
    args = parser.parse_args()
    client = YoutubeWrapper(args.secrets)
    (playlist_id, video_ids) = get_new_ids(args.index, args.playlist, client)
    export_to_youtube(video_ids, playlist_id, client)

if __name__ == "__main__":
    main()
