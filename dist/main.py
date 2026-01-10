import pygame
import os

from api.io.Lightning.gui import GameUI
from api.io.Lightning.gui.Interface import loading_screen, init, main_menu, classic_mode
from api.io.Lightning.gui.LoginScreen import login_screen
from api.io.Lightning.gui.Leaderboard import leaderboard_screen
from api.io.Lightning.gui.LoseState import lose_screen
from api.io.Lightning.gui.WinState import win_screen
from api.io.Lightning.utils.ConfigFile import *
from api.io.Lightning.gui.GameUI import *
from api.io.Lightning.manager.StorageManager import StorageManager
from api.io.Lightning.manager.SaveManager import SaveManager
from api.io.Lightning.manager.SoundReader import music_manager  # Import music_manager

if __name__ == '__main__':
    screen = init()
    clock = pygame.time.Clock()
    current_screen = "loading"
    background_capture = None
    current_user = None  # Store logged in username
    storage_manager = StorageManager()  # Initialize storage manager

    # Track Times
    win_time = 0
    campaign_total_time = 0

    while current_screen:
        if current_screen == "loading":
            current_screen = loading_screen(screen, clock)
        elif current_screen == "login":
            result = login_screen(screen, clock)
            if result and result[0] == "logged_in":
                current_user = result[1]
                # Set storage manager current user
                storage_manager.current_user = current_user
                storage_manager.current_profile = storage_manager.load_profile(current_user)
                # Load user profile in GameUI and set storage_manager
                GameUI.set_current_user(current_user)
                GameUI.set_storage_manager(storage_manager)
                current_screen = "main_menu"
            else:
                current_screen = None
        elif current_screen == "main_menu":
            current_screen = main_menu(screen, clock, storage_manager, current_user)
            
            # Handle menu actions
            if current_screen == "logout":
                storage_manager.logout()
                current_user = None
                current_screen = "login"
            elif current_screen == "continue":
                # Load saved game
                if GameUI.load_game():
                    current_screen = "classic_mode"
                else:
                    # Failed to load, go back to menu
                    current_screen = "main_menu"
            elif current_screen == "classic_mode":
                # Start new game (delete any existing save and regenerate level)
                if storage_manager:
                    storage_manager.delete_save()
                campaign_total_time = 0
                GameUI.start_new_game()
                current_screen = "classic_mode"
            elif current_screen == "leaderboard":
                # Show leaderboard
                current_screen = "leaderboard"

        elif current_screen == "leaderboard":
            result = leaderboard_screen(screen, clock, storage_manager)
            if result == "back":
                current_screen = "main_menu"
            else:
                current_screen = None

        elif current_screen == "classic_mode":
            result = classic_mode(screen, clock)

            if isinstance(result, tuple):
                status, data = result
                if status == "lose_screen":
                    background_capture = data
                    current_screen = "lose_screen"
                elif status == "win_screen":
                    win_time = data
                    current_screen = "win_screen"
            elif result == "main_menu":
                # Save game before returning to menu
                GameUI.save_and_quit()
                current_screen = "main_menu"
                music_manager.start_menu_music()
            else:
                current_screen = None

        elif current_screen == "lose_screen":
            current_screen = lose_screen(screen, clock, background_surf=background_capture)
            if current_screen == "retry":
                GameUI.restart_level()
                current_screen = "classic_mode"
            elif current_screen == "save_quit":
                # Save game before quitting
                GameUI.save_and_quit()
                current_screen = "main_menu"
                music_manager.start_menu_music()
            elif current_screen == "undo":
                GameUI.undo_move()
                current_screen = "classic_mode"
            elif current_screen == "abandon":
                GameUI.start_abandon_hope()
                current_screen = "classic_mode"

        elif current_screen == "win_screen":
            # --- FIX: Timer Pausing ---
            GameUI.pause_timer()

            total_display = campaign_total_time + win_time
            action = win_screen(screen, clock, level_time_ms=win_time, total_time_ms=total_display)

            if action == "next_level":
                campaign_total_time += win_time
                
                # Check if pyramid complete (level 15)
                level_system = GameUI.get_level_system()
                if level_system and level_system.get_current_level() == 15:
                    # Pyramid complete! Submit to leaderboard
                    pyramid = level_system.get_current_pyramid()
                    if storage_manager and storage_manager.current_user:
                        storage_manager.submit_score(pyramid, campaign_total_time + win_time)
                    # Reset for next pyramid
                    campaign_total_time = 0
                
                GameUI.next_level()
                current_screen = "classic_mode"
            elif action == "undo":
                # --- FIX: Resume Timer on Undo ---
                GameUI.resume_timer()
                GameUI.undo_move()
                current_screen = "classic_mode"
            elif action == "reset":
                # Reset doesn't need resume as start_timer is called in level gen,
                # but good practice to clear pause state just in case logic changes.
                GameUI.resume_timer()
                GameUI.restart_level()
                current_screen = "classic_mode"
            elif action == "quit":
                # --- FIX: Reset level to prevent instant win loop ---
                GameUI.save_and_quit()
                GameUI.restart_level()
                current_screen = "main_menu"
                music_manager.start_menu_music()
            else:
                current_screen = "main_menu"
                music_manager.start_menu_music()

        elif current_screen == "tutorial":
            current_screen = None
            if current_screen == "main_menu":
                music_manager.start_menu_music()
        else:
            break

    pygame.quit()
