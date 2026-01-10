import pygame
import os
from api.io.Lightning.manager.UIFont import UIFont
from api.io.Lightning.manager.ProfileManager import ProfileManager
from api.io.Lightning.utils.ConfigFile import UI_PATH, fps
from api.io.Lightning.manager.SoundReader import music_manager  # Import music_manager


def login_screen(screen, clock):
    """Login/Register screen UI.

    Args:
        screen: Pygame screen surface
        clock: Pygame clock object

    Returns:
        tuple: ("logged_in", username) or None for quit
    """
    # Load background
    menuback = pygame.image.load(os.path.join(UI_PATH, 'menuback.jpg'))

    # Use pygame.font for input boxes (typing)
    input_font = pygame.font.SysFont("arial", 24)

    # Use UIFont for labels and buttons
    ui_font = UIFont(size=28)
    error_font = UIFont(size=24, color=(255, 50, 50))
    title_font = UIFont(size=32, color=(255, 125, 17))

    # Input fields
    username_input = ""
    password_input = ""
    active_field = "username"  # "username" or "password"
    error_message = ""

    # Input field rectangles
    username_rect = pygame.Rect(220, 200, 200, 35)
    password_rect = pygame.Rect(220, 260, 200, 35)

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        clicked = False
        submit_action = None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            
            # Handle music events
            music_manager.handle_event(event)

            # Handle mouse clicks
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked = True
                # Check input field clicks
                if username_rect.collidepoint(mouse_pos):
                    active_field = "username"
                elif password_rect.collidepoint(mouse_pos):
                    active_field = "password"

            # Handle keyboard input
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    if active_field == "username":
                        username_input = username_input[:-1]
                    else:
                        password_input = password_input[:-1]
                elif event.key == pygame.K_TAB:
                    # Switch between fields
                    active_field = "password" if active_field == "username" else "username"
                elif event.key == pygame.K_RETURN:
                    # Enter key attempts login
                    submit_action = "login"
                elif event.unicode and event.unicode.isprintable():
                    # Only accept alphanumeric characters
                    if event.unicode.isalnum():
                        if active_field == "username" and len(username_input) < 15:
                            username_input += event.unicode
                        elif active_field == "password" and len(password_input) < 15:
                            password_input += event.unicode

        # Draw background
        screen.blit(menuback, (0, 0))

        # Draw title using UIFont
        title_font.render_header('LOGIN / REGISTER', screen, 320, 150)

        # Draw labels using UIFont
        ui_font.render_label("USER:", screen, 160, 217)
        ui_font.render_label("PASS:", screen, 160, 277)

        # Draw username input field
        pygame.draw.rect(screen, (255, 255, 255) if active_field == "username" else (200, 200, 200), username_rect, 2)
        if username_input:
            username_text = input_font.render(username_input, True, (255, 255, 255))
            screen.blit(username_text, (username_rect.x + 5, username_rect.y + 5))

        # Draw password input field (masked)
        pygame.draw.rect(screen, (255, 255, 255) if active_field == "password" else (200, 200, 200), password_rect, 2)
        if password_input:
            masked_password = '*' * len(password_input)
            password_text = input_font.render(masked_password, True, (255, 255, 255))
            screen.blit(password_text, (password_rect.x + 5, password_rect.y + 5))

        # Draw buttons using UIFont
        if ui_font.draw_button(screen, "LOGIN", 250, 340, mouse_pos, clicked):
            submit_action = "login"

        if ui_font.draw_button(screen, "REGISTER", 390, 340, mouse_pos, clicked):
            submit_action = "register"

        # Reset cursor if not hovering buttons
        if not (220 < mouse_pos[0] < 420 and 325 < mouse_pos[1] < 355):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        # Handle submission
        if submit_action:
            u, p = username_input, password_input
            if len(u) < 3:
                error_message = "USERNAME TOO SHORT (MIN 3)"
            elif len(p) < 4:
                error_message = "PASSWORD TOO SHORT (MIN 4)"
            elif not u or not p:
                error_message = "MISSING INFO"
            else:
                if submit_action == "login":
                    success, message = ProfileManager.authenticate(u, p)
                    if success:
                        return ("logged_in", u)
                    error_message = message.upper()
                else:
                    success, message = ProfileManager.create_profile(u, p)
                    if success:
                        return ("logged_in", u)
                    error_message = message.upper()
            pygame.time.wait(250)

        # Draw error message
        if error_message:
            error_font.render_label(error_message, screen, 320, 400)

        pygame.display.flip()
        clock.tick(fps)

    return None
