"""
Music player class


MPyG321 callbacks example
Playing and pausing some music, triggering callbacks
You need to add a "sample.mp3" file in the working directory
"""
from mpyg321.mpyg321 import MPyg321Player, PlayerStatus
from time import sleep


class AudioPlayer(MPyg321Player):

    # Player status: 0 - ready, 1 - playing, 2 - paused, 3 - stopped, 4 - quitted

    def play_audio(self):

        # Player status: 0 - ready; 1 - playing; 2 - paused; 3 - stopped; 4 - quit

        if self.status == 2: # paused
            self.resume()

        elif self.status != 1:
            # currently not paused and not playing -> start
            self.play_song(configs.AUDIO_PATH)
        else:
            pass


# Just an example
def do_some_play_pause(player):
    """Does some play and pause"""
    player.play_song("sample.mp3")
    sleep(5)
    player.pause()
    sleep(3)
    player.resume()
    sleep(5)
    player.stop()
    player.quit()


def main():
    """Do the magic"""
    player = MyPlayer()
    do_some_play_pause(player)

if __name__ == "__main__":
    main()
