import pygame
import os

from api.io.Lightning.gui import GameUI
from api.io.Lightning.gui.LoseState import lose_screen
from api.io.Lightning.gui.WinState import win_screen
from api.io.Lightning.manager.TextDesigner import CustomFont
from api.io.Lightning.manager.ProfileManager import ProfileManager
from api.io.Lightning.utils.ConfigFile import UI_PATH, SOUNDS_PATH, fps
from api.io.Lightning.manager.SoundReader import music_manager


def init():
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    pygame.display.set_caption("Mummy Maze Ultimate 1.0")
    icon = pygame.image.load(os.path.join(UI_PATH, 'game.ico'))
    pygame.display.set_icon(icon)
    GameUI.initialize_ui()
    return screen


def loading_screen(screen, clock):
    music_manager.initialize()
    title = pygame.image.load(os.path.join(UI_PATH, 'title.jpg'))
    progress_bar = pygame.image.load(os.path.join(UI_PATH, 'titlebar.jpg')).convert_alpha()
    color = CustomFont(color=(255, 125, 17), hover_color=(255, 255, 255))
    play = color.render('CLICK HERE TO PLAY', outline_thickness=1, hovered=False)
    play_hovered = color.render('CLICK HERE TO PLAY', outline_thickness=1, hovered=True)
    play_rect = play.get_rect(topleft=(190, 430))

    progress = 0
    speed = 0.8
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            music_manager.handle_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and progress >= 100:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                mouse_pos = pygame.mouse.get_pos()
                if play_rect.collidepoint(mouse_pos):
                    return "login"

        screen.blit(title, (0, 0))
        fill_px = int((progress / 100) * 340)
        bar_crop = progress_bar.subsurface((0, 0, fill_px, 24))
        screen.blit(bar_crop, (147, 392))
        if progress < 100:
            progress += speed
            if progress > 100: progress = 100
        else:
            mouse_pos = pygame.mouse.get_pos()
            if play_rect.collidepoint(mouse_pos):
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                screen.blit(play_hovered, (190, 430))
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                screen.blit(play, (190, 430))
        pygame.display.flip()
        clock.tick(fps)
    return None


def main_menu(screen, clock, storage_manager=None, current_user=None):
    """Main menu with 2x2 button grid matching the original game style.
    
    Layout:
        Left Column: CLASSIC MODE (top), CONTINUE (bottom)
        Right Column: LEADERBOARD (top), LOG OUT (bottom)
    
    Args:
        screen: Pygame screen surface
        clock: Pygame clock object
        storage_manager: StorageManager instance (optional)
        current_user: Current username (optional)
    """
    
    menuback = pygame.image.load(os.path.join(UI_PATH, 'menuback.jpg'))
    menufront = pygame.image.load(os.path.join(UI_PATH, 'menufront.png'))
    logo = pygame.image.load(os.path.join(UI_PATH, 'menulogo.png'))
    color = CustomFont(color=(0, 0, 0), hover_color=(245, 0, 0))
    tombslide_sound = pygame.mixer.Sound(os.path.join(SOUNDS_PATH, 'tombslide.wav'))
    tombslide_sound.play()
    
    # Check for saved game
    has_save = False
    if storage_manager:
        has_save = storage_manager.has_saved_game()
    
    # Render buttons - 2x2 grid layout
    classic = color.render('CLASSIC MODE', outline=False, hovered=False)
    classic_hovered = color.render('CLASSIC MODE', outline_thickness=1, hovered=True)
    
    # Only create CONTINUE buttons if save exists
    if has_save:
        continue_btn = color.render('CONTINUE', outline=False, hovered=False)
        continue_btn_h = color.render('CONTINUE', outline_thickness=1, hovered=True)
    
    leaderboard = color.render('LEADERBOARD', outline=False, hovered=False)
    leaderboard_h = color.render('LEADERBOARD', outline_thickness=1, hovered=True)
    
    logout = color.render('LOG OUT', outline=False, hovered=False)
    logout_h = color.render('LOG OUT', outline_thickness=1, hovered=True)
    
    # Button positions (2x2 grid)
    # Left column center x=175, Right column center x=465
    # Top row center y=360, Bottom row center y=410
    center_x1 = 175  # Left Column Center
    center_x2 = 465  # Right Column Center
    center_y1 = 360  # Top Row Center
    center_y2 = 410  # Bottom Row Center
    
    classic_rect = classic.get_rect(center=(center_x1, center_y1))
    leaderboard_rect = leaderboard.get_rect(center=(center_x2, center_y1))
    logout_rect = logout.get_rect(center=(center_x2, center_y2))
    
    if has_save:
        continue_rect = continue_btn.get_rect(center=(center_x1, center_y2))
    
    # Animation setup (like LoseState)
    logo_target_y = 10
    logo_start_y = -logo.get_height()
    menu_target_y = 0
    menu_start_y = 480
    animation_progress = 0.0
    animation_speed = 0.02
    animation_complete = False

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                return None
            music_manager.handle_event(event)
            
            if animation_complete and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                if classic_rect.collidepoint(mouse_pos):
                    return "classic_mode"
                if has_save and continue_rect.collidepoint(mouse_pos):
                    return "continue"
                if leaderboard_rect.collidepoint(mouse_pos):
                    return "leaderboard"
                if logout_rect.collidepoint(mouse_pos):
                    return "logout"

        # Draw
        screen.blit(menuback, (0, 0))
        
        # Animation
        if animation_progress < 1.0:
            animation_progress += animation_speed
            if animation_progress > 1.0:
                animation_progress = 1.0
                animation_complete = True
            eased_progress = 1 - (1 - animation_progress) ** 2
            current_logo_y = logo_start_y + (logo_target_y - logo_start_y) * eased_progress
            current_menu_y = menu_start_y + (menu_target_y - menu_start_y) * eased_progress
            
            # Draw with offsets
            screen.blit(menufront, (0, current_menu_y))
            screen.blit(logo, (92.5, current_logo_y))
            
            # Draw buttons with offset
            button_y_offset = current_menu_y - menu_target_y
            screen.blit(classic, (classic_rect.x, classic_rect.y + button_y_offset))
            screen.blit(leaderboard, (leaderboard_rect.x, leaderboard_rect.y + button_y_offset))
            screen.blit(logout, (logout_rect.x, logout_rect.y + button_y_offset))
            if has_save:
                screen.blit(continue_btn, (continue_rect.x, continue_rect.y + button_y_offset))
        else:
            # Draw static
            screen.blit(menufront, (0, menu_target_y))
            screen.blit(logo, (92.5, logo_target_y))
            
            mouse_pos = pygame.mouse.get_pos()
            
            # Determine hover state
            hovered = None
            if classic_rect.collidepoint(mouse_pos):
                hovered = 'classic'
            elif has_save and continue_rect.collidepoint(mouse_pos):
                hovered = 'continue'
            elif leaderboard_rect.collidepoint(mouse_pos):
                hovered = 'leaderboard'
            elif logout_rect.collidepoint(mouse_pos):
                hovered = 'logout'
            
            # Draw with hover states
            screen.blit(classic_hovered if hovered == 'classic' else classic, classic_rect)
            screen.blit(leaderboard_h if hovered == 'leaderboard' else leaderboard, leaderboard_rect)
            screen.blit(logout_h if hovered == 'logout' else logout, logout_rect)
            if has_save:
                screen.blit(continue_btn_h if hovered == 'continue' else continue_btn, continue_rect)
            
            if hovered:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        
        pygame.display.flip()
        clock.tick(fps)
    
    return None


def classic_mode(screen, clock):
    """Main game loop for classic mode with animated intro."""
    # Initialize game state
    GameUI.reset_input()
    music_manager.start_classic_mode_music()
    
    # Load and play intro sound
    tombslide_sound = pygame.mixer.Sound(os.path.join(SOUNDS_PATH, 'tombslide.wav'))
    tombslide_sound.play()
    
    # Load logo for animation
    mumlogo = pygame.image.load(os.path.join(UI_PATH, 'mumlogo.png')).convert_alpha()
    mumlogo_x = 14
    mumlogo_start_y = -mumlogo.get_height()
    mumlogo_target_y = 14
    
    # Animation state
    animation_progress = 0.0
    animation_speed = 0.02
    animation_complete = False

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Auto-save before closing
                GameUI.save_game()
                return None
            music_manager.handle_event(event)
            
            if animation_complete:
                action = GameUI.handle_game_input(event, mouse_pos)
                if action == 'quit':
                    # Auto-save before returning to menu
                    GameUI.save_game()
                    return "main_menu"

        # Get button states
        hovered = GameUI.get_hover_state(mouse_pos) if animation_complete else None
        clicked = GameUI.get_clicked_state() if animation_complete else None

        # Update cursor based on hover state
        if animation_complete:
            cursor = pygame.SYSTEM_CURSOR_HAND if hovered else pygame.SYSTEM_CURSOR_ARROW
            pygame.mouse.set_cursor(cursor)

        # Update and draw animation or game
        if animation_progress < 1.0:
            # Animate logo sliding down
            animation_progress += animation_speed
            if animation_progress > 1.0:
                animation_progress = 1.0
                animation_complete = True
            
            eased_progress = 1 - (1 - animation_progress) ** 2
            current_mumlogo_y = mumlogo_start_y + (mumlogo_target_y - mumlogo_start_y) * eased_progress
            
            GameUI.draw_screen(screen, hovered, clicked, draw_mumlogo=False, mumlogo_y=current_mumlogo_y)
            screen.blit(mumlogo, (mumlogo_x, current_mumlogo_y))
        else:
            # Normal gameplay - draw and check for game state changes
            status = GameUI.draw_screen(screen, hovered, clicked)
            
            if status == "lose":
                game_snapshot = screen.copy()
                return "lose_screen", game_snapshot
            elif isinstance(status, tuple) and status[0] == "win":
                return "win_screen", status[1]

        pygame.display.flip()
        clock.tick(fps)
    
    return None


