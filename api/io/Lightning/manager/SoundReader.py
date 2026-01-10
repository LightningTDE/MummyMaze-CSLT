import random
import pygame, os
from api.io.Lightning.utils.ConfigFile import MUSIC_PATH, SOUNDS_PATH


class MusicManager:
    # Music track ranges for different modes
    MENU_TRACKS = list(range(1, 13))  # 01-12.mp3
    CLASSIC_TRACKS = list(range(23, 39))  # 23-38.mp3
    PAUSE_TRACKS = list(range(48, 54))  # 48-53.mp3
    
    def __init__(self):
        self.music_enabled = False
        self.current_track = 0
        self.loop_tracks = self.MENU_TRACKS.copy()
        self.current_loop_index = 0
        self.MUSIC_END = pygame.USEREVENT + 1
        self.initialized = False
        self.current_mode = "menu"
        self.volume = 0.5  # Default volume

    def initialize(self):
        if self.initialized: return
        try:
            if not pygame.mixer.get_init(): pygame.mixer.init()
            pygame.mixer.music.set_volume(self.volume)

            start_music = os.path.join(MUSIC_PATH, "00.mp3")
            if os.path.exists(start_music):
                pygame.mixer.music.load(start_music)
                pygame.mixer.music.play()
                pygame.mixer.music.set_endevent(self.MUSIC_END)
                self.music_enabled = True
                self.initialized = True
        except Exception as e:
            print(f'Music Init Error: {e}')

    def set_volume(self, vol):
        self.volume = max(0.0, min(1.0, vol))
        if self.initialized:
            pygame.mixer.music.set_volume(self.volume)

    def get_volume(self):
        return self.volume

    def handle_event(self, event):
        """Handle pygame music end events for looping"""
        if event.type == self.MUSIC_END and self.music_enabled:
            try:
                print(f"DEBUG: Music ended, current_mode={self.current_mode}, current_track={self.current_track}")
                
                if self.current_mode == "menu":
                    if self.current_track == 0:
                        # Intro (00.mp3) finished, start loop tracks
                        self.loop_tracks = list(range(1, 13))  # 01-12
                        self.current_loop_index = 0
                        self.current_track = self.loop_tracks[0]
                        self._play_track(f'{self.current_track:02d}.mp3')
                    else:
                        # Continue looping menu music
                        self.current_loop_index = (self.current_loop_index + 1) % len(self.loop_tracks)
                        self.current_track = self.loop_tracks[self.current_loop_index]
                        self._play_track(f'{self.current_track:02d}.mp3')
                
                elif self.current_mode == "classic":
                    # Loop classic mode music (01-12.mp3)
                    self.current_loop_index = (self.current_loop_index + 1) % len(self.loop_tracks)
                    self.current_track = self.loop_tracks[self.current_loop_index]
                    self._play_track(f'{self.current_track:02d}.mp3')
                
                elif self.current_mode == "pause":
                    # Loop pause music (48-53.mp3)
                    self.current_loop_index = (self.current_loop_index + 1) % len(self.loop_tracks)
                    self.current_track = self.loop_tracks[self.current_loop_index]
                    music_path = os.path.join(MUSIC_PATH, f'{self.current_track:02d}.mp3')
                    pygame.mixer.music.load(music_path)
                    pygame.mixer.music.set_volume(self.volume)
                    pygame.mixer.music.play()
                    print(f"DEBUG: Looping pause music - {self.current_track:02d}.mp3")

                elif self.current_mode == "win":
                    # Win music plays once, no auto-loop
                    pass

            except Exception as e:
                print(f'ERROR in handle_event: {e}')

    def _play_track(self, filename):
        """Play a music track with error checking."""
        path = os.path.join(MUSIC_PATH, filename)
        if not os.path.exists(path):
            error_msg = (
                f"\n{'='*60}\n"
                f"MUSIC FILE NOT FOUND ERROR\n"
                f"{'='*60}\n"
                f"Missing music file: {filename}\n"
                f"Expected location: {path}\n"
                f"\nPlease ensure the music file exists in the music directory.\n"
                f"{'='*60}\n"
            )
            raise FileNotFoundError(error_msg)
        
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            # Ensure MUSIC_END event is set for looping
            pygame.mixer.music.set_endevent(self.MUSIC_END)
            print(f"DEBUG: Playing {filename} (mode: {self.current_mode})")
        except Exception as e:
            error_msg = (
                f"\n{'='*60}\n"
                f"MUSIC PLAYBACK ERROR\n"
                f"{'='*60}\n"
                f"Failed to play music file: {filename}\n"
                f"Error: {str(e)}\n"
                f"{'='*60}\n"
            )
            raise RuntimeError(error_msg) from e

    def start_classic_mode_music(self):
        """Start classic mode music with error checking."""
        print("DEBUG: start_classic_mode_music() called")
        self.current_mode = "classic"
        self.loop_tracks = self.CLASSIC_TRACKS.copy()
        self.current_loop_index = 0
        self.current_track = self.loop_tracks[0]
        
        # Verify all tracks exist before starting
        missing_tracks = []
        for track in self.loop_tracks:
            track_path = os.path.join(MUSIC_PATH, f'{track:02d}.mp3')
            if not os.path.exists(track_path):
                missing_tracks.append(f'{track:02d}.mp3')
        
        if missing_tracks:
            error_msg = (
                f"\n{'='*60}\n"
                f"CLASSIC MODE MUSIC ERROR\n"
                f"{'='*60}\n"
                f"Missing {len(missing_tracks)} music file(s) for classic mode:\n"
                f"{', '.join(missing_tracks)}\n"
                f"\nExpected location: {MUSIC_PATH}\n"
                f"Please add the missing files to continue.\n"
                f"{'='*60}\n"
            )
            raise FileNotFoundError(error_msg)
        
        self._play_track(f'{self.current_track:02d}.mp3')

    def start_menu_music(self):
        """Start menu music with intro (00.mp3) then loop (01-12.mp3)."""
        self.current_mode = "menu"
        self.current_track = 0  # Start with intro track
        self.loop_tracks = self.MENU_TRACKS.copy()
        self.current_loop_index = 0
        
        # Verify all tracks exist before starting
        missing_tracks = []
        # Check intro track
        intro_path = os.path.join(MUSIC_PATH, '00.mp3')
        if not os.path.exists(intro_path):
            missing_tracks.append('00.mp3')
        
        # Check loop tracks
        for track in self.loop_tracks:
            track_path = os.path.join(MUSIC_PATH, f'{track:02d}.mp3')
            if not os.path.exists(track_path):
                missing_tracks.append(f'{track:02d}.mp3')
        
        if missing_tracks:
            error_msg = (
                f"\n{'='*60}\n"
                f"MENU MUSIC ERROR\n"
                f"{'='*60}\n"
                f"Missing {len(missing_tracks)} music file(s) for menu:\n"
                f"{', '.join(missing_tracks)}\n"
                f"\nExpected location: {MUSIC_PATH}\n"
                f"Please add the missing files to continue.\n"
                f"{'='*60}\n"
            )
            raise FileNotFoundError(error_msg)
        
        # Play intro track first (00.mp3)
        self._play_track('00.mp3')

    def play_pause_music(self):
        """Play pause menu music (48-53.mp3) in a loop with error checking."""
        if not self.music_enabled:
            return
        
        print("DEBUG: play_pause_music() called")
        
        # Set mode FIRST before loading music
        self.current_mode = "pause"
        self.loop_tracks = self.PAUSE_TRACKS.copy()
        self.current_loop_index = 0
        self.current_track = self.loop_tracks[0]
        
        # Verify all tracks exist before starting
        missing_tracks = []
        for track in self.loop_tracks:
            track_path = os.path.join(MUSIC_PATH, f'{track:02d}.mp3')
            if not os.path.exists(track_path):
                missing_tracks.append(f'{track:02d}.mp3')
        
        if missing_tracks:
            error_msg = (
                f"\n{'='*60}\n"
                f"PAUSE MUSIC ERROR\n"
                f"{'='*60}\n"
                f"Missing {len(missing_tracks)} music file(s) for pause menu:\n"
                f"{', '.join(missing_tracks)}\n"
                f"\nExpected location: {MUSIC_PATH}\n"
                f"Please add the missing files to continue.\n"
                f"{'='*60}\n"
            )
            raise FileNotFoundError(error_msg)
        
        music_path = os.path.join(MUSIC_PATH, f'{self.current_track:02d}.mp3')
        try:
            pygame.mixer.music.stop()  # Stop current music first
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play()
            print(f"DEBUG: Successfully playing pause music - {self.current_track:02d}.mp3")
        except Exception as e:
            print(f"ERROR: Failed to play pause music: {e}")

    def play_win_music(self):
        """Play win celebration music (40.mp3) once, no loop, with error checking."""
        self.current_mode = "win"
        
        # Verify win music exists
        win_track = '40.mp3'
        track_path = os.path.join(MUSIC_PATH, win_track)
        if not os.path.exists(track_path):
            error_msg = (
                f"\n{'='*60}\n"
                f"WIN MUSIC ERROR\n"
                f"{'='*60}\n"
                f"Missing win celebration music file: {win_track}\n"
                f"Expected location: {track_path}\n"
                f"\nPlease add the missing file to continue.\n"
                f"{'='*60}\n"
            )
            raise FileNotFoundError(error_msg)
        
        self._play_track(win_track)

    def pause_classic_music(self):
        """Pause the currently playing music"""
        if self.music_enabled:
            pygame.mixer.music.pause()
            print(f"DEBUG: Paused music (mode was: {self.current_mode})")

    def resume_classic_music(self):
        """Resume classic music (restarts from current loop position after win/pause music)"""
        if self.music_enabled:
            # If we were in pause mode, need to switch back to classic
            if self.current_mode == "pause":
                print("DEBUG: Switching from pause mode back to classic mode")
                self.start_classic_mode_music()
            else:
                pygame.mixer.music.unpause()
                print(f"DEBUG: Resumed music (mode: {self.current_mode})")

    def stop(self):
        if self.music_enabled:
            pygame.mixer.music.stop()


class SoundEffectManager:
    def __init__(self):
        self.sounds = {}
        self.initialized = False
        self.volume = 0.5  # Default volume

    def initialize(self):
        """Initialize sound effects with error checking."""
        if self.initialized: return
        if not pygame.mixer.get_init(): pygame.mixer.init()

        missing_files = []
        
        def load(name):
            """Load a sound file with error checking.
            
            Args:
                name: Filename of the sound
            
            Returns:
                pygame.mixer.Sound or None
            """
            path = os.path.join(SOUNDS_PATH, name)
            if os.path.exists(path):
                try:
                    snd = pygame.mixer.Sound(path)
                    snd.set_volume(self.volume)
                    return snd
                except Exception as e:
                    error_msg = (
                        f"\n{'='*60}\n"
                        f"SOUND EFFECT LOAD ERROR\n"
                        f"{'='*60}\n"
                        f"Failed to load sound file: {name}\n"
                        f"Error: {str(e)}\n"
                        f"Path: {path}\n"
                        f"{'='*60}\n"
                    )
                    raise RuntimeError(error_msg) from e
            else:
                missing_files.append(name)
                return None

        # 1. Load Walk Sounds
        for variant in ['15', '30', '60']:
            self.sounds[f'exp_start_{variant}'] = load(f'expwalk{variant}a.wav')
            self.sounds[f'exp_end_{variant}'] = load(f'expwalk{variant}b.wav')
            self.sounds[f'mum_start_{variant}'] = load(f'mumwalk{variant}a.wav')
            self.sounds[f'mum_end_{variant}'] = load(f'mumwalk{variant}b.wav')

        self.sounds['scorp_1'] = load('scorpwalk1.wav')
        self.sounds['scorp_2'] = load('scorpwalk2.wav')

        # 2. Load Action Sounds
        self.sounds['pummel'] = load('pummel.wav')
        self.sounds['tombslide'] = load('tombslide.wav')
        self.sounds['gate'] = load('gate.wav')

        # --- NEW: Block Trap Sound ---
        self.sounds['block'] = load('block.wav')

        # 3. Load Death/Misc Sounds
        self.sounds['badankh'] = load('badankh.wav')
        self.sounds['mummyhowl'] = load('mummyhowl.wav')
        self.sounds['poison'] = load('poison.wav')

        # Victory/Completion sounds
        self.sounds['finished'] = load('finishedlevel.wav')

        # Check if any required sounds are missing
        if missing_files:
            error_msg = (
                f"\n{'='*60}\n"
                f"SOUND EFFECTS MISSING ERROR\n"
                f"{'='*60}\n"
                f"Missing {len(missing_files)} required sound effect file(s):\n"
            )
            for i, filename in enumerate(missing_files, 1):
                error_msg += f"  {i}. {filename}\n"
            error_msg += (
                f"\nExpected location: {SOUNDS_PATH}\n"
                f"Please add the missing sound files to continue.\n"
                f"{'='*60}\n"
            )
            raise FileNotFoundError(error_msg)

        self.initialized = True

    def set_volume(self, vol):
        self.volume = max(0.0, min(1.0, vol))
        if self.initialized:
            for sound in self.sounds.values():
                if sound: sound.set_volume(self.volume)

    def get_volume(self):
        return self.volume

    def play(self, name):
        """Play a sound effect with error checking.
        
        Args:
            name: Name of the sound effect to play
        """
        if not self.initialized:
            print(f"Warning: SoundEffectManager not initialized, cannot play '{name}'")
            return
            
        if name not in self.sounds:
            error_msg = (
                f"\n{'='*60}\n"
                f"SOUND EFFECT NOT FOUND ERROR\n"
                f"{'='*60}\n"
                f"Attempted to play unknown sound effect: '{name}'\n"
                f"Available sound effects: {', '.join(sorted(self.sounds.keys()))}\n"
                f"{'='*60}\n"
            )
            raise KeyError(error_msg)
        
        if self.sounds[name] is None:
            print(f"Warning: Sound effect '{name}' failed to load, skipping playback")
            return
            
        try:
            self.sounds[name].play()
        except Exception as e:
            print(f"Warning: Failed to play sound effect '{name}': {e}")

    def play_walk_start(self, entity_type):
        variant = random.choice(['15', '30', '60'])
        if entity_type == 'player':
            self.play(f'exp_start_{variant}')
        elif 'mummy' in entity_type:
            self.play(f'mum_start_{variant}')
        elif 'scorpion' in entity_type:
            scorp_var = random.choice(['1', '2'])
            self.play(f'scorp_{scorp_var}')
            return None
        return variant

    def play_walk_end(self, entity_type, variant):
        if not variant: return
        if entity_type == 'player':
            self.play(f'exp_end_{variant}')
        elif 'mummy' in entity_type:
            self.play(f'mum_end_{variant}')

music_manager = MusicManager()
sfx_manager = SoundEffectManager()