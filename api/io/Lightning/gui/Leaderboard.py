import pygame
import os
from api.io.Lightning.manager.UIFont import UIFont
from api.io.Lightning.manager.StorageManager import StorageManager
from api.io.Lightning.utils.ConfigFile import UI_PATH, fps
from api.io.Lightning.manager.SoundReader import music_manager  # Import music_manager


def format_time(ms):
    """Format milliseconds to 'Xm Ys' or 'Xh Ym Zs'.
    
    Args:
        ms (int): Time in milliseconds
        
    Returns:
        str: Formatted time string
    """
    total_seconds = ms // 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


def leaderboard_screen(screen, clock, storage_manager):
    """Display leaderboard with all pyramids combined.
    
    Shows top 10 entries sorted by pyramid DESC (3→2→1), then time ASC.
    No tabs - just a pyramid column.
    
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
    title_font = UIFont(size=32, color=(255, 215, 0))  # Gold
    header_font = UIFont(size=24, color=(255, 100, 100))  # Red headers
    white_font = UIFont(size=24, color=(255, 255, 255))
    
    # Medal colors
    COLOR_GOLD = (255, 215, 0)
    COLOR_SILVER = (192, 192, 192)
    COLOR_BRONZE = (205, 127, 50)
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        clicked = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            
            # Handle music events for looping
            music_manager.handle_event(event)
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked = True
        
        # Draw background
        screen.blit(menuback, (0, 0))
        
        # Draw title
        title_font.render_header("LEADERBOARD", screen, 320, 50)
        
        # Get ALL leaderboard data (all pyramids)
        all_data = storage_manager.get_all_leaderboard_data()
        
        # Sort by: Pyramid DESC (3→2→1), then Time ASC (fastest first)
        all_data.sort(key=lambda x: (-x['pyramid'], x['total_time']))
        
        # Take top 10 only
        top_10 = all_data[:10]
        
        # Draw column headers
        header_y = 100
        header_font.render_label("RANK", screen, 120, header_y)
        header_font.render_label("PYRAMID", screen, 240, header_y)
        header_font.render_label("NAME", screen, 380, header_y)
        header_font.render_label("TIME", screen, 540, header_y)
        
        # Draw entries
        if not top_10:
            white_font.render_label("NO RECORDS YET", screen, 320, 200)
        else:
            row_y = header_y + 40
            for idx, entry in enumerate(top_10):
                # Top 3 colors
                if idx == 0:
                    color = COLOR_GOLD
                elif idx == 1:
                    color = COLOR_SILVER
                elif idx == 2:
                    color = COLOR_BRONZE
                else:
                    color = (255, 255, 255)  # White
                
                row_font = UIFont(size=22, color=color)
                
                # Format data
                rank_str = f"{idx + 1}."
                pyramid_str = str(entry['pyramid'])
                name_str = entry['name'][:12]  # Truncate long names
                time_str = format_time(entry['total_time'])
                
                # Draw columns
                row_font.render_label(rank_str, screen, 120, row_y)
                row_font.render_label(pyramid_str, screen, 240, row_y)
                row_font.render_label(name_str, screen, 380, row_y)
                row_font.render_label(time_str, screen, 540, row_y)
                
                row_y += 35
        
        # Draw back button
        if white_font.draw_button(screen, "BACK", 320, 450, mouse_pos, clicked):
            return "back"
        
        # Reset cursor if not hovering any button
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        pygame.display.flip()
        clock.tick(fps)
    
    return None
