import pygame
import os
from api.io.Lightning.manager.UIFont import UIFont
from api.io.Lightning.manager.StorageManager import StorageManager
from api.io.Lightning.utils.ConfigFile import UI_PATH, fps


def format_time(milliseconds):
    """Format time in milliseconds to readable format.
    
    Args:
        milliseconds (int): Time in milliseconds
        
    Returns:
        str: Formatted time string (e.g., "15m 30s")
    """
    seconds = milliseconds // 1000
    minutes = seconds // 60
    seconds = seconds % 60
    
    if minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


def leaderboard_screen(screen, clock, storage_manager):
    """Display leaderboard with pyramid tabs.
    
    Args:
        screen: Pygame screen surface
        clock: Pygame clock object
        storage_manager: StorageManager instance
        
    Returns:
        str: "back" to return to main menu, or None to quit
    """
    # Load background
    menuback = pygame.image.load(os.path.join(UI_PATH, 'menuback.jpg'))
    
    # Use UIFont for all text rendering
    title_font = UIFont(size=32, color=(255, 215, 0))
    white_font = UIFont(size=24)
    
    # Medal colors
    COLOR_GOLD = (255, 215, 0)
    COLOR_SILVER = (192, 192, 192)
    COLOR_BRONZE = (205, 127, 50)
    
    # Get available pyramids (start with at least pyramid 1)
    available_pyramids = storage_manager.get_available_pyramids()
    if not available_pyramids:
        available_pyramids = [1]  # Default to pyramid 1 if no data
    
    current_pyramid = available_pyramids[0] if available_pyramids else 1
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        clicked = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked = True
        
        # Draw background
        screen.blit(menuback, (0, 0))
        
        # Draw title
        title_font.render_header("LEADERBOARD", screen, 320, 50)
        
        # Draw pyramid tabs
        for i in range(min(3, len(available_pyramids))):  # Max 3 tabs
            pyramid = available_pyramids[i]
            x = 160 + i * 160
            y = 120
            label = f"PYRAMID {pyramid}"
            
            if current_pyramid == pyramid:
                tab_font = UIFont(size=28, color=(255, 215, 0))
            else:
                tab_font = UIFont(size=28, color=(150, 150, 150))
            
            if tab_font.draw_button(screen, label, x, y, mouse_pos, clicked):
                current_pyramid = pyramid
        
        # Draw leaderboard header
        header_y = 170
        white_font.render_label('RANK', screen, 100, header_y)
        white_font.render_label('NAME', screen, 280, header_y)
        white_font.render_label('TIME', screen, 500, header_y)
        
        # Draw divider line
        pygame.draw.line(screen, (255, 255, 255), (60, header_y + 25), (580, header_y + 25), 1)
        
        # Get leaderboard data for current pyramid
        leaderboard = storage_manager.get_leaderboard(current_pyramid)
        
        # Draw leaderboard entries
        entry_y = header_y + 35
        max_entries = 10
        for i, entry in enumerate(leaderboard[:max_entries]):
            rank = i + 1
            username = entry.get("display_name", entry.get("username", "Unknown"))
            total_time = entry.get("total_time", 0)
            
            # Determine color based on rank
            if rank == 1:
                color = COLOR_GOLD
            elif rank == 2:
                color = COLOR_SILVER
            elif rank == 3:
                color = COLOR_BRONZE
            else:
                color = (255, 255, 255)
            
            # Create UIFont with appropriate color
            entry_font = UIFont(size=24, color=color)
            
            # Draw rank
            entry_font.render_label(f'{rank}.', screen, 100, entry_y)
            
            # Draw username (truncate if too long)
            display_name = username[:15] if len(username) > 15 else username
            entry_font.render_label(display_name, screen, 280, entry_y)
            
            # Draw time
            time_str = format_time(total_time)
            entry_font.render_label(time_str, screen, 500, entry_y)
            
            entry_y += 25
        
        # If no entries, show message
        if not leaderboard:
            white_font.render_label('No scores yet!', screen, 320, 280)
        
        # Draw back button
        if white_font.draw_button(screen, "BACK", 320, 440, mouse_pos, clicked):
            return "back"
        
        # Reset cursor if not hovering any button
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        pygame.display.flip()
        clock.tick(fps)
    
    return None
