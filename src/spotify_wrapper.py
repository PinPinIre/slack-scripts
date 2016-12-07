import spotipy
import spotipy.util as util


class SpotifyWrapper(object):

    MAX_REQUEST_CHUNK = 100

    def __init__(self, username, secrets_file):
        self.username = username
        self.secrets_file = secrets_file
        self.spotify = self.__get_client()

    def __get_client(self):
        """
        Boilerplate code. This will get a client to access the Spotify API
        """
        client_id = self.secrets_file['client_id']
        client_secret = self.secrets_file['client_secret']
        redirect_uri = self.secrets_file['redirect_uri']
        scope = "playlist-modify-public"
        token = util.prompt_for_user_token(self.username, scope=scope,
                                           client_id=client_id,
                                           client_secret=client_secret,
                                           redirect_uri=redirect_uri)
        return spotipy.Spotify(auth=token)


    def create_playlist(self, title):
        """
        Create a new Spotify playlist.
        Returns request response
        """
        result = self.spotify.user_playlist_create(self.username, title, public=True)
        return result

    def get_playlists(self):
        """
        Get all the playlists for the current user
        """
        # TODO: Implement this
        return None

    def get_playlist_items(self, playlist_id):
        """
        Get all of the playlist items from a playlist.
        """
        # TODO: Implement this
        return None

    def add_songs_to_playlist(self, track_ids, playlist_id):
        """
        Add a list of track ids to a playlists
        Returns None
        """
        # We can only add 100 tracks at a time so chunk
        max_chunk = self.MAX_REQUEST_CHUNK
        for chunk in [track_ids[x:x+max_chunk] for x in xrange(0, len(track_ids), max_chunk)]:
            self.spotify.user_playlist_add_tracks(self.username, playlist_id, chunk)
