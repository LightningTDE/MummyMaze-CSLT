# ----------------------------------- Package ----------------------------------- #
import pygame
import os

from api.io.Lightning.manager.TextDesigner import CustomFont
from api.io.Lightning.utils.ConfigFile import UI_PATH, fps
from api.io.Lightning.manager.SoundReader import sfx_manager, music_manager  # --- FIX: Import music_manager ---

# ----------------------------------- Package ----------------------------------- #

"""
/**
 * Tạo giao diện khi người chơi thua trong trò chơi
 */
"""


def lose_screen(screen, clock, background_surf=None):
    # --- FIX: Play Lose Jingle Always ---
    sfx_manager.play('mummyhowl')

    # 1. Khởi chạy các tài nguyên
    if background_surf:
        menuback = background_surf
    else:
        menuback = pygame.image.load(os.path.join(UI_PATH, 'menuback.jpg'))

    menufront = pygame.image.load(os.path.join(UI_PATH, 'menufront.png'))

    # 2. Chuẩn bị văn bản
    designer = CustomFont(color=(0, 0, 0), hover_color=(245, 0, 0))

    # 3. Chuẩn bị nút bấm
    btn_try = designer.render('TRY AGAIN', outline=False, hovered=False)
    btn_try_h = designer.render('TRY AGAIN', outline_thickness=1, hovered=True)

    btn_abandon = designer.render('ABANDON HOPE', outline=False, hovered=False)
    btn_abandon_h = designer.render('ABANDON HOPE', outline_thickness=1, hovered=True)

    btn_undo = designer.render('UNDO MOVE', outline=False, hovered=False)
    btn_undo_h = designer.render('UNDO MOVE', outline_thickness=1, hovered=True)

    btn_save = designer.render('SAVE AND QUIT', outline=False, hovered=False)
    btn_save_h = designer.render('SAVE AND QUIT', outline_thickness=1, hovered=True)

    # 4. Điều chỉnh vị trí (Centered for better alignment)
    center_x1 = 175  # Left Column Center
    center_x2 = 465  # Right Column Center
    center_y1 = 375  # Top Row Center
    center_y2 = 425  # Bottom Row Center

    # Tạo ô cho nút bấm (Using center instead of topleft)
    rect_try = btn_try.get_rect(center=(center_x1, center_y1))
    rect_abandon = btn_abandon.get_rect(center=(center_x2, center_y1))
    rect_undo = btn_undo.get_rect(center=(center_x1, center_y2))
    rect_save = btn_save.get_rect(center=(center_x2, center_y2))

    # 5. Các biến đại diện cho hiệu ứng
    menu_target_y = 0
    menu_start_y = 480
    animation_progress = 0.0
    animation_speed = 0.02
    animation_complete = False

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            
            # Handle music events for looping
            music_manager.handle_event(event)

            if animation_complete and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()

                if rect_try.collidepoint(mouse_pos):
                    return "retry"
                elif rect_abandon.collidepoint(mouse_pos):
                    return "abandon"
                elif rect_undo.collidepoint(mouse_pos):
                    return "undo"
                elif rect_save.collidepoint(mouse_pos):
                    return "save_quit"

        # Cập nhật hiệu ứng
        current_menu_y = menu_target_y
        if animation_progress < 1.0:
            animation_progress += animation_speed
            if animation_progress > 1.0:
                animation_progress = 1.0
                animation_complete = True
            eased_progress = 1 - (1 - animation_progress) ** 2
            current_menu_y = menu_start_y + (menu_target_y - menu_start_y) * eased_progress

        # Khởi tạo giao diện
        screen.blit(menuback, (0, 0))
        screen.blit(menufront, (0, current_menu_y))

        # Tính toán vị trí hiệu ứng
        y_offset = current_menu_y - menu_target_y
        mouse_pos = pygame.mouse.get_pos()

        # Tạo nút bấm
        def draw_btn(rect, normal_surf, hover_surf):
            if animation_complete and rect.collidepoint(mouse_pos):
                screen.blit(hover_surf, (rect.x, rect.y + y_offset))
            else:
                screen.blit(normal_surf, (rect.x, rect.y + y_offset))

        draw_btn(rect_try, btn_try, btn_try_h)
        draw_btn(rect_abandon, btn_abandon, btn_abandon_h)
        draw_btn(rect_undo, btn_undo, btn_undo_h)
        draw_btn(rect_save, btn_save, btn_save_h)

        # Hiệu ứng khi di chuột
        if animation_complete:
            is_hovering = (rect_try.collidepoint(mouse_pos) or
                           rect_abandon.collidepoint(mouse_pos) or
                           rect_undo.collidepoint(mouse_pos) or
                           rect_save.collidepoint(mouse_pos))
            if is_hovering:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        pygame.display.flip()
        clock.tick(fps)

    return "quit"