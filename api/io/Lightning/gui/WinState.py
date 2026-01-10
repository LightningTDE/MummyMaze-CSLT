import pygame
import os

from api.io.Lightning.manager.TextDesigner import CustomFont
from api.io.Lightning.utils.ConfigFile import UI_PATH, fps
from api.io.Lightning.gui import GameUI  # --- FIX: Import GameUI to handle side buttons ---


def format_time_text(ms, include_hours=False):
    """Converts milliseconds to a compact readable string."""
    seconds = int((ms / 1000) % 60)
    minutes = int((ms / (1000 * 60)) % 60)
    hours = int(ms / (1000 * 60 * 60))
    
    if include_hours and hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    else:
        return f"{minutes}m {seconds}s"


def win_screen(screen, clock, level_time_ms=0, total_time_ms=0):
    """
    Displays the Win Screen with stats and the next level button.
    """
    # Track options menu state
    _show_options = False
    
    # 1. Load Background
    background = pygame.image.load(os.path.join(UI_PATH, 'nextlevel.jpg')).convert()
    bg_x, bg_y = 152, 5
    bg_width = background.get_width()
    bg_center_x = bg_x + (bg_width // 2)

    # 2. Setup TextDesigners
    designer_gold = CustomFont(color=(255, 215, 0))
    designer_orange = CustomFont(color=(200, 100, 0))
    designer_red = CustomFont(color=(139, 0, 0))
    designer_btn = CustomFont(color=(255, 255, 0), hover_color=(255, 255, 255))

    # 3. Render Static Text
    title_surf = designer_gold.render_header("YOU HAVE ESCAPED THE MAZE!")
    title_rect = title_surf.get_rect(center=(bg_center_x, bg_y + 40))

    time_str = format_time_text(level_time_ms, include_hours=False)
    total_time_str = format_time_text(total_time_ms if total_time_ms > 0 else level_time_ms, include_hours=True)

    lbl_time = designer_orange.render_header(f"Time: {time_str}")
    lbl_total = designer_orange.render_header(f"Total Time: {total_time_str}")

    rect_time = lbl_time.get_rect(center=(bg_center_x, bg_y + 130))
    rect_total = lbl_total.get_rect(center=(bg_center_x, bg_y + 160))

    flavor_1 = designer_red.render_header("You carefully proceed")
    flavor_2 = designer_red.render_header("to the second chamber...")

    rect_f1 = flavor_1.get_rect(center=(bg_center_x, bg_y + 240))
    rect_f2 = flavor_2.get_rect(center=(bg_center_x, bg_y + 265))

    btn_text = "ENTER THE NEXT CHAMBER"
    btn_surf = designer_btn.render(btn_text, outline=True, hovered=False)
    btn_surf_hover = designer_btn.render(btn_text, outline=True, hovered=True)
    btn_rect = btn_surf.get_rect(center=(bg_center_x, bg_y + 320))

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            # --- FIX: Handle Side Buttons with Options Menu Support ---
            action = GameUI.handle_game_input(event, mouse_pos)
            if action:
                # Toggle options menu instead of exiting
                if action == 'option':
                    _show_options = not _show_options
                    GameUI.reset_input()  # Clear button clicked state after toggling options
                # Only return for actions that should exit win state
                elif action in ('quit', 'reset', 'undo'):
                    return action

            # Handle options menu interactions
            if _show_options and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                from api.io.Lightning.manager.SoundReader import music_manager, sfx_manager
                cx, cy = screen.get_width() // 2, screen.get_height() // 2
                bx, by = cx - 150, cy - 100
                if bx < mouse_pos[0] < bx + 300:
                    if by + 50 < mouse_pos[1] < by + 80:
                        music_manager.set_volume(music_manager.get_volume() + (0.1 if mouse_pos[0] > cx else -0.1))
                    elif by + 90 < mouse_pos[1] < by + 120:
                        sfx_manager.set_volume(sfx_manager.get_volume() + (0.1 if mouse_pos[0] > cx else -0.1))

            if not _show_options and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_rect.collidepoint(mouse_pos):
                    return "next_level"

        # --- Drawing ---

        # 1. Draw Underlying Game Screen (Sidebar + Maze) without updating game logic
        # This keeps side buttons visible and functional
        hovered = GameUI.get_hover_state(mouse_pos)
        clicked = GameUI.get_clicked_state()
        GameUI.draw_screen(screen, hovered, clicked, update_game=False)

        # 2. Draw Win Overlay Background
        screen.blit(background, (bg_x, bg_y))

        # 3. Draw Win Text
        screen.blit(title_surf, title_rect)
        screen.blit(lbl_time, rect_time)
        screen.blit(lbl_total, rect_total)
        screen.blit(flavor_1, rect_f1)
        screen.blit(flavor_2, rect_f2)

        # 4. Draw Next Level Button
        # FIX: Ensure button is drawn even if hovering over side bar
        if btn_rect.collidepoint(mouse_pos):
            screen.blit(btn_surf_hover, btn_rect)
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            screen.blit(btn_surf, btn_rect)
            # Only switch to arrow if NOT hovering a side button
            if not hovered:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)

        # 5. Draw Options Menu Overlay if active
        if _show_options:
            GameUI._draw_options_menu(screen)

        pygame.display.flip()
        clock.tick(fps)

    return "quit"