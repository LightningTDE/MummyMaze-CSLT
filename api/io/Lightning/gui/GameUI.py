# ----------------------------------- Package ----------------------------------- #
import pygame
import os
import datetime
from enum import Enum

from api.io.Lightning.gui.MapTracker import WorldMapPanel
from api.io.Lightning.manager.SoundReader import sfx_manager, music_manager
from api.io.Lightning.manager.TextDesigner import CustomFont
from api.io.Lightning.maze.MazeLoader import MazeLoader
from api.io.Lightning.listener.AnimatedListener import initialize_torch_animation
from api.io.Lightning.utils.ConfigFile import UI_PATH, maze_coord_x, maze_coord_y
from api.io.Lightning.manager.ButtonManager import ButtonManager
from api.io.Lightning.entities.Player import Player, PlayerState
from api.io.Lightning.maze.LevelSelector import LevelSystem
from api.io.Lightning.manager.ProfileManager import ProfileManager
from api.io.Lightning.manager.SaveManager import SaveManager
from api.io.Lightning.manager.StorageManager import StorageManager
from api.io.Lightning.entities.Enemy import Enemy
# ----------------------------------- Package ----------------------------------- #

"""
/**
 * Tạo quy tắc cho trò chơi theo luật:
 * Nhận thông tin từ người chơi
 * -> Nhận thông tin từ quái vật
 * -> Xử lý tranh chấp giữa vật thể
 */
"""
class TurnState(Enum):
    PLAYER_INPUT = 0
    PLAYER_MOVING = 1
    ENEMY_TURN = 2
    ENEMY_MOVING = 3
    PLAYER_DYING = 4
    FIGHT_PAUSE = 5


"""
/**
 * Các thành phần toàn cục của trò chơi:
 * Nút bấm, hiệu ứng, thông tin map,
 * cơ chế map level, giải đố
 */
"""
_button_manager = None
_torch_animation = None
_world_map = None
_level_system = None
_solution_pen = None  # For rendering debug text

"""
/**
 * Các thành phần xử lý của trò chơi:
 * Khởi tạo mê cung, nhân vật thám hiểm,
 * các giao diện trong trò chơi
 */
"""
_maze_loader = None
_player = None
_turn_state = TurnState.PLAYER_INPUT
_show_options = False
_show_ankh = True  # Default to True (show ankh)

"""
/**
 * Bộ đếm thời gian và sự kiện
 */
"""
_death_timer = 0
_death_step = 0
_death_step_timer = 0
_fight_pause_timer = 0
_level_start_time = 0  # Starts when level is generated
_killer_ref = None
_active_trap = None

"""
/**
 * Tìm đường đi cho giải đố
 */
"""
_is_abandoning = False
_solution_path = []
_last_abandon_move_time = 0

"""
/**
 * Profile and save system
 */
"""
_current_user = None
_user_profile = None
_storage_manager = None  # Add global storage_manager reference

# --- TIMER VARIABLES ---
_total_paused_time = 0
_paused_at = 0

def start_timer():
    """Resets and starts the level timer."""
    global _level_start_time, _total_paused_time, _paused_at
    _level_start_time = pygame.time.get_ticks()
    _total_paused_time = 0
    _paused_at = 0

def pause_timer():
    """Pauses the timer (e.g., when on Win Screen)."""
    global _paused_at
    if _paused_at == 0:
        _paused_at = pygame.time.get_ticks()

def resume_timer():
    """Resumes the timer (e.g., when Undoing from Win Screen)."""
    global _paused_at, _total_paused_time
    if _paused_at != 0:
        _total_paused_time += (pygame.time.get_ticks() - _paused_at)
        _paused_at = 0

def get_level_time():
    """Calculates effective gameplay time."""
    current_time = pygame.time.get_ticks()
    # If currently paused, use the pause timestamp as the 'current' time
    # so the timer appears frozen.
    if _paused_at != 0:
        current_time = _paused_at
    return max(0, current_time - _level_start_time - _total_paused_time)

def get_total_time():
    """Get total time across all levels in the current session.
    
    Returns:
        int: Total time in milliseconds
    """
    global _user_profile
    if _user_profile:
        return _user_profile.get('total_time', 0)
    return 0

def set_storage_manager(storage_manager):
    """Set the storage manager instance for save/load operations.
    
    Args:
        storage_manager: StorageManager instance
    """
    global _storage_manager
    _storage_manager = storage_manager

"""
/**
 * Khởi tạo giao diện cho trò chơi
 */
"""
def initialize_ui():
    global _button_manager, _torch_animation, _world_map, _level_system, _solution_pen, _show_ankh

    _button_manager = ButtonManager()
    _torch_animation = initialize_torch_animation()
    _world_map = WorldMapPanel(x=8, y=320)
    _level_system = LevelSystem()
    _solution_pen = CustomFont(color=(0, 255, 0))  # Init once for performance

    sfx_manager.initialize()
    music_manager.initialize()
    
    # Load show_ankh setting from profile (will be loaded properly when user logs in)
    _show_ankh = True  # Default value

    _generate_current_level_maze()

"""
/**
 * Khởi tạo mê cung theo chỉ định
 */
"""
def _generate_current_level_maze():
    global _maze_loader, _player, _turn_state, _death_timer, \
        _killer_ref, _level_start_time, _is_abandoning, _level_system, _active_trap

    # Lấy thông tin từ LevelSelector
    current_diff = _level_system.get_current_difficulty() if _level_system else 'easy'
    _maze_loader = MazeLoader(generate_infinite=True, difficulty=current_diff)

    # Khởi tạo vị trí người chơi
    if _maze_loader and _maze_loader.parsed:
        p = _maze_loader.parsed['player']
        _player = Player(p['x'], p['y'], _maze_loader.maze_size, _maze_loader.cell_size)

    # Khởi tạo bộ đếm thời gian, sự kiện trong trò chơi
    _turn_state = TurnState.PLAYER_INPUT
    _death_timer = 0
    _killer_ref = None
    _active_trap = None
    _is_abandoning = False
    
    start_timer() # Start tracking time for this level

    # Cài đặt lại nút bấm
    if _button_manager:
        _button_manager.clear_clicked()

"""
/**
 * Bắt đầu lại mê cung từ vị trí xuất phát
 */
"""
def restart_level():
    global _player, _maze_loader, _turn_state, _death_timer, \
        _killer_ref, _is_abandoning, _active_trap
    
    if _maze_loader:
        _maze_loader.reset()
        if _maze_loader.parsed:
            p = _maze_loader.parsed['player']
            _player = Player(p['x'], p['y'], _maze_loader.maze_size, _maze_loader.cell_size)

    _turn_state = TurnState.PLAYER_INPUT
    _death_timer = 0
    _killer_ref = None
    _active_trap = None
    _is_abandoning = False
    if _button_manager:
        _button_manager.clear_clicked()

"""
/**
 * Bắt đầu giải đố khi người chơi bỏ cuộc
 */
"""
def start_abandon_hope():
    global _is_abandoning, _solution_path, _last_abandon_move_time, _turn_state

    restart_level()

    if _maze_loader and _player:
        path = _maze_loader.get_solution_path(_player)
        if path:
            _solution_path = path
            _is_abandoning = True
            _last_abandon_move_time = pygame.time.get_ticks()
            _turn_state = TurnState.PLAYER_INPUT
            print(f"Abandon Hope active: {len(path)} steps.")
        else:
            print("No solution found for Abandon Hope.")

"""
/**
 * Bắt đầu màn chơi mới sau khi hoàn thành
 */
"""
def next_level():
    global _level_system, _user_profile, _current_user, _storage_manager
    if _level_system:
        pyramid_complete = not _level_system.next_level()  # Returns False when pyramid complete
        _generate_current_level_maze()
        
        # Update user profile with new pyramid/level
        new_pyramid = _level_system.get_current_pyramid()
        new_level = _level_system.get_current_level()
        
        # Update via storage_manager if available
        if _storage_manager and _storage_manager.current_profile:
            _storage_manager.update_progression(new_pyramid, new_level)
            # Also update local reference
            _user_profile = _storage_manager.current_profile
        elif _user_profile and _current_user:
            # Fallback to ProfileManager if storage_manager not available
            _user_profile['pyramid'] = new_pyramid
            _user_profile['level'] = new_level
            ProfileManager.save_profile(_user_profile)
        
        if pyramid_complete:
            print(f"🎉 Pyramid {new_pyramid - 1} completed! Moving to Pyramid {new_pyramid}, Level {new_level}")
        else:
            print(f"📈 Advanced to Pyramid {new_pyramid}, Level {new_level}")

def start_new_game():
    """Start a new game from the beginning (Level 1, Pyramid 1)."""
    global _level_system, _storage_manager, _user_profile
    
    if _level_system:
        _level_system.reset_progress()  # Resets to Pyramid 1, Level 1
    
    # CRITICAL: Update profile immediately when starting new game
    # Using explicit values (1, 1) to ensure new game always starts at beginning
    if _storage_manager and _storage_manager.current_profile:
        _storage_manager.update_progression(1, 1)  # Set to Pyramid 1, Level 1
        _user_profile = _storage_manager.current_profile
        print("✅ Started new game: Pyramid 1, Level 1 - Profile updated")
    elif _user_profile:
        # Fallback to ProfileManager
        _user_profile['pyramid'] = 1
        _user_profile['level'] = 1
        _user_profile['total_time'] = 0  # Reset total time for new game
        ProfileManager.save_profile(_user_profile)
        print("✅ Started new game: Pyramid 1, Level 1")
    
    _generate_current_level_maze()

"""
/**
 * Cho phép quay lại lượt di chuyển trước đó
 */
"""
def undo_move():
    global _player, _maze_loader, _turn_state, \
        _death_timer, _killer_ref, _is_abandoning, _active_trap
    if _maze_loader and _player:
        if _maze_loader.undo_last_move(_player):
            _turn_state = TurnState.PLAYER_INPUT
            _death_timer = 0
            _killer_ref = None
            _active_trap = None
            _player.state = PlayerState.IDLE
            _player.frame_index = 0
            _is_abandoning = False
            print("Undo successful.")

"""
/**
 * Cài đặt lại input
 */
"""
def reset_input():
    if _button_manager:
        _button_manager.clear_clicked()

"""
/**
 * Profile and save system functions
 */
"""
def set_current_user(username):
    """Set the current logged in user and load their profile."""
    global _current_user, _user_profile, _level_system, _show_ankh
    _current_user = username
    _user_profile = ProfileManager.load_profile(username)
    
    # Load user options
    if _user_profile and 'options' in _user_profile:
        options = _user_profile['options']
        music_manager.set_volume(options.get('music_volume', 0.5))
        sfx_manager.set_volume(options.get('sfx_volume', 0.5))
        _show_ankh = options.get('show_ankh', True)
    
    # Sync level system with profile
    if _user_profile and _level_system:
        pyramid = _user_profile.get('pyramid', 1)
        level = _user_profile.get('level', 1)
        _level_system.set_pyramid_and_level(pyramid, level)

def save_game():
    """Save current game state to user profile."""
    global _maze_loader, _player, _level_system, _turn_state, _storage_manager
    
    if not _storage_manager or not _storage_manager.current_user:
        return False
    
    # Check if player is at exit - don't save, they should advance to next level
    if _maze_loader and _player:
        exit_pos = _maze_loader.parsed.get('exit', {})
        if exit_pos and _player.x == exit_pos.get('x') and _player.y == exit_pos.get('y'):
            print("⚠️ Cannot save at exit position - please advance to next level or undo")
            return False
    
    # If player is dead/dying, undo to last valid move
    if _turn_state == TurnState.PLAYER_DYING or (
        _player and _player.state in [
            PlayerState.DIE_RED_MUMMY, 
            PlayerState.DIE_WHITE_MUMMY, 
            PlayerState.DIE_STUNG, 
            PlayerState.DIE_TRAP
        ]
    ):
        print("Player is dead - reverting to last undo before saving")
        undo_move()
    
    if not _maze_loader or not _player:
        return False
    
    # CRITICAL: Get pyramid and level from LEVEL SYSTEM (source of truth for current game)
    if _level_system:
        pyramid = _level_system.get_current_pyramid()
        level = _level_system.get_current_level()
        print(f"DEBUG: Saving game at Pyramid {pyramid}, Level {level} (from level_system)")
    else:
        # Fallback to profile (but this shouldn't happen)
        profile = _storage_manager.current_profile
        if not profile:
            return False
        pyramid = profile.get('pyramid', 1)
        level = profile.get('level', 1)
        print(f"DEBUG: Saving game at Pyramid {pyramid}, Level {level} (from profile - fallback)")
    
    # Update profile progression BEFORE saving
    _storage_manager.update_progression(pyramid, level)
    
    # Get level and total time
    level_time = get_level_time()
    total_time = get_total_time() + level_time
    
    # Save original maze data (for regeneration)
    original_maze = _maze_loader.data
    
    # Save current state
    current_state = {
        "player": {
            "x": _player.x,
            "y": _player.y,
            "direction": _player.direction
        },
        "enemies": [
            {
                "type": e.type,
                "x": e.x,
                "y": e.y,
                "direction": e.direction
            }
            for e in _maze_loader.enemies_list if not e.is_dead
        ],
        "gate_open": not _maze_loader.gate_obj.is_blocking() if _maze_loader.gate_obj else True,
        "gate_frame": _maze_loader.gate_obj.current_frame if _maze_loader.gate_obj else 0,
        "traps": [t.is_triggered for t in _maze_loader.traps],
        "solvable": _maze_loader.is_current_state_solvable  # ← ADD ANKH STATUS
    }
    
    # Use StorageManager to save
    success = _storage_manager.save_game(
        original_maze, 
        current_state, 
        level_time, 
        total_time,
        pyramid=pyramid,
        level=level
    )
    
    if success:
        print(f"✅ Game saved: Pyramid {pyramid} - Level {level}")
    
    return success

def load_game():
    """Load saved game state from user profile."""
    global _maze_loader, _player, _level_system, _turn_state, _level_start_time, _total_paused_time, _storage_manager
    
    if not _storage_manager or not _storage_manager.current_user:
        return False
    
    save_data = _storage_manager.load_game()
    if not save_data:
        return False
    
    # Load pyramid and level from save data
    pyramid = save_data.get("pyramid", 1)
    level = save_data.get("level", 1)
    
    print(f"DEBUG: Loading game - Save data has Pyramid {pyramid}, Level {level}")
    
    # Sync level_system with loaded data
    if _level_system:
        _level_system.set_pyramid(pyramid)
        _level_system.set_level(level)
        print(f"DEBUG: level_system synced to Pyramid {pyramid}, Level {level}")
    
    # Load original maze
    original_maze = save_data.get("original_maze")
    if not original_maze:
        return False
    
    # Create MazeLoader from original maze data
    _maze_loader = MazeLoader.from_data(original_maze)
    
    # Apply current state
    current_state = save_data.get("current_state", {})
    
    # Restore player position
    player_data = current_state.get("player", {})
    px = player_data.get("x", 0)
    py = player_data.get("y", 0)
    pdir = player_data.get("direction", "down")
    
    _player = Player(px, py, _maze_loader.maze_size, _maze_loader.cell_size)
    _player.direction = pdir
    _player.target_x = px * _player.tile_size
    _player.target_y = py * _player.tile_size
    _player.pixel_x = _player.target_x
    _player.pixel_y = _player.target_y
    
    # Restore enemy positions
    saved_enemies = current_state.get("enemies", [])
    _maze_loader.enemies_list.clear()
    
    for e_data in saved_enemies:
        new_enemy = Enemy(
            e_data["x"],
            e_data["y"],
            e_data["type"],
            _maze_loader.maze_size,
            _maze_loader.cell_size,
            _maze_loader.parsed["walls"],
            _maze_loader.gate_obj
        )
        new_enemy.direction = e_data.get("direction", "down")
        new_enemy.pixel_x = new_enemy.x * _maze_loader.cell_size
        new_enemy.pixel_y = new_enemy.y * _maze_loader.cell_size
        new_enemy.target_x = new_enemy.pixel_x
        new_enemy.target_y = new_enemy.pixel_y
        _maze_loader.enemies_list.append(new_enemy)
    
    # Restore gate state
    if _maze_loader.gate_obj:
        gate_open = current_state.get("gate_open", False)
        gate_frame = current_state.get("gate_frame", 0)
        
        if gate_open:
            _maze_loader.gate_obj.state = _maze_loader.gate_obj.STATE_OPEN
        else:
            _maze_loader.gate_obj.state = _maze_loader.gate_obj.STATE_CLOSED
        
        _maze_loader.gate_obj.current_frame = gate_frame
    
    # Restore trap states
    trap_states = current_state.get("traps", [])
    for i, is_triggered in enumerate(trap_states):
        if i < len(_maze_loader.traps):
            if is_triggered:
                _maze_loader.traps[i].is_triggered = True
            else:
                _maze_loader.traps[i].reset()
    
    # Restore ankh solvability status
    _maze_loader.is_current_state_solvable = current_state.get("solvable", True)
    
    # Restore timers
    _level_start_time = pygame.time.get_ticks() - save_data.get("level_time", 0)
    _total_paused_time = 0
    
    # Set correct game state
    _turn_state = TurnState.PLAYER_INPUT
    
    print(f"✅ Game loaded: Pyramid {pyramid} - Level {level}")
    return True

def has_save_game():
    """Check if current user has a saved game."""
    global _storage_manager
    if not _storage_manager or not _storage_manager.current_user:
        return False
    return _storage_manager.has_saved_game()

def save_and_quit():
    """Save game and prepare for quitting to menu."""
    save_game()
    # Don't restart level - we want to save the current state, not reset it

def get_level_system():
    """Get the level system instance.
    
    Returns:
        LevelSystem: The level system instance or None
    """
    global _level_system
    return _level_system

"""
/**
 * Cập nhật trạng thái khi đang chạy trò chơi
 */
"""
def _update_game_state():
    global _turn_state, _death_step, _death_step_timer, _fight_pause_timer, \
        _killer_ref, _is_abandoning, _solution_path, _last_abandon_move_time, _active_trap

    if not _player or not _maze_loader:
        return None

    _player.update()
    _maze_loader.update()

    # --- Trạng thái: Người chơi di chuyển ---
    if _turn_state == TurnState.PLAYER_MOVING:
        if not _player.is_moving:
            _maze_loader.check_key_collision(_player.x, _player.y)

            triggered_trap = _maze_loader.check_trap_collision(_player.x, _player.y)
            if triggered_trap:
                _active_trap = triggered_trap
                _turn_state = TurnState.PLAYER_DYING
                _death_step = 10  # Special Start Step for Trap
                _death_step_timer = pygame.time.get_ticks()
                sfx_manager.play('block')
                try:
                    _player.state = PlayerState.DIE_TRAP
                except:
                    _player.state = PlayerState.IDLE
                return None

            _turn_state = TurnState.ENEMY_TURN

    # --- Trạng thái: Lượt của kẻ địch ---
    elif _turn_state == TurnState.ENEMY_TURN:
        for e in _maze_loader.enemies_list:
            e.prev_x, e.prev_y = e.x, e.y
        _maze_loader.init_enemy_turn_sequence()
        _turn_state = TurnState.ENEMY_MOVING

    # --- Trạng thái: Lượt di chuyển của kẻ địch ---
    elif _turn_state == TurnState.ENEMY_MOVING:
        kill = False
        for e in _maze_loader.enemies_list:
            if e.x == _player.x and e.y == _player.y:
                sfx_manager.play('pummel')
                e.move_queue.clear()
                _killer_ref = e
                _maze_loader.spawn_fight_cloud(_player.x, _player.y)
                _killer_ref.face_target(_player.x, _player.y)
                _turn_state = TurnState.PLAYER_DYING
                _death_step = 1
                _death_step_timer = pygame.time.get_ticks()
                kill = True
                _is_abandoning = False
                break

        if not kill:
            if _maze_loader.resolve_enemy_collisions():
                _maze_loader.pause_enemies()
                _turn_state = TurnState.FIGHT_PAUSE
                _fight_pause_timer = pygame.time.get_ticks()
            else:
                if _maze_loader.update_turn_sequence(_player.get_pos()):
                    # Kiểm tra điều kiện thắng
                    exit_pos = _maze_loader.parsed['exit']
                    if _player.x == exit_pos['x'] and _player.y == exit_pos['y']:
                        elapsed = get_level_time()
                        if _is_abandoning: 
                            _is_abandoning = False
                            return "lose"
                        return "win", elapsed

                    _maze_loader.face_enemies_to_player(_player)
                    _turn_state = TurnState.PLAYER_INPUT
                    _player.last_input_time = pygame.time.get_ticks()
                    _maze_loader.check_solvability(_player)

    # --- Trạng thái: Tranh chấp ---
    elif _turn_state == TurnState.FIGHT_PAUSE:
        if pygame.time.get_ticks() - _fight_pause_timer > 500:
            _maze_loader.process_pending_deaths()
            _maze_loader.resume_enemies()
            _turn_state = TurnState.ENEMY_MOVING

    # --- Trạng thái: Người chơi chết ---
    elif _turn_state == TurnState.PLAYER_DYING:
        now = pygame.time.get_ticks()
        if _death_step < 10:
            if _death_step == 1:
                if now - _death_step_timer > 550:
                    if _killer_ref and 'scorpion' in _killer_ref.type:
                        _killer_ref.retreat_to(_killer_ref.prev_x, _killer_ref.prev_y)
                        _death_step = 2
                    else:
                        if _killer_ref and 'mummy' in _killer_ref.type:
                            _player.state = PlayerState.DIE_RED_MUMMY if _killer_ref.type == 'red_mummy' else PlayerState.DIE_WHITE_MUMMY
                            if _killer_ref in _maze_loader.enemies_list:
                                _maze_loader.enemies_list.remove(_killer_ref)
                        _player.frame_index = 0
                        _death_step = 3
            elif _death_step == 2:
                if _killer_ref and not _killer_ref.is_moving:
                    _player.state = PlayerState.DIE_STUNG
                    sfx_manager.play('poison')
                    _player.frame_index = 0
                    _death_step = 3
                    _death_step_timer = now
            elif _death_step == 3:
                anim = _player.animations.get(_player.state, [])
                if anim and _player.frame_index >= len(anim) - 1:
                    if _death_step_timer == 0: _death_step_timer = now
                    if now - _death_step_timer > 1000: return "lose"
        else:
            if _death_step == 10:
                anim_done = _player.is_anim_finished()
                if anim_done or (now - _death_step_timer > 800):
                    if _active_trap: _active_trap.trigger()
                    _death_step = 11
            elif _death_step == 11:
                if _active_trap and _active_trap.is_finished():
                    _death_step_timer = now
                    _death_step = 12
            elif _death_step == 12:
                if now - _death_step_timer > 500: return "lose"

    # --- Trạng thái: Điều khiển người chơi ---
    elif _turn_state == TurnState.PLAYER_INPUT:
        if "AFK" in _player.state.name:
            _maze_loader.trigger_enemy_afk()

        # Tự động điều khiển khi giải đố
        if _is_abandoning and _solution_path:
            now = pygame.time.get_ticks()
            if now - _last_abandon_move_time > 400:
                if len(_solution_path) > 1:
                    target = _solution_path[1]
                    dx = target[0] - _player.x
                    dy = target[1] - _player.y
                    if abs(dx) + abs(dy) <= 1:
                        _execute_player_move(dx, dy)
                        _solution_path.pop(0)
                        _last_abandon_move_time = now
                    else:
                        _solution_path.pop(0)
                else:
                    _is_abandoning = False
                    return "lose"

    return None

"""
/**
 * Khởi tạo giao diện trò chơi lên màn hình:
 * Giao diện bên ngoài (Logo, nút bấm, hiệu ứng...)
 * Giao diện bên trong (Nhân vật, mê cung, kẻ địch...)
 */
"""
def draw_screen(screen, hovered=None, clicked=None, draw_mumlogo=True, mumlogo_y=None, update_game=True):
    global _torch_animation, _maze_loader, _player, _show_options, _level_system, _is_abandoning, _show_ankh

    snake = pygame.image.load(os.path.join(UI_PATH, 'snake.png')).convert_alpha()
    mumlogo = pygame.image.load(os.path.join(UI_PATH, 'mumlogo.png')).convert_alpha()

    # 1. Cập nhật trạng thái
    if not _show_options and update_game:
        status = _update_game_state()
        if status: return status

    # 2. Vẽ không gian bên ngoài và mê cung
    if _maze_loader:
        _maze_loader.draw_background(screen)

    if _torch_animation and _torch_animation.loaded:
        _torch_animation.update()
        ms = _maze_loader.maze_size if _maze_loader else 6
        if ms == 6:
            _torch_animation.draw(screen, 300, 40)
            _torch_animation.draw(screen, 475, 40)
        elif ms == 8:
            _torch_animation.draw(screen, 320, 40)
            _torch_animation.draw(screen, 455, 40)
        elif ms == 10:
            _torch_animation.draw(screen, 295, 40)
            _torch_animation.draw(screen, 475, 40)

    if _maze_loader:
        m = pygame.mouse.get_pos() if _turn_state == TurnState.PLAYER_INPUT else None
        _maze_loader.draw(screen, _player, None, m)

    screen.blit(snake, (8, 80))
    if draw_mumlogo:
        screen.blit(mumlogo, (14, mumlogo_y if mumlogo_y else 14))

    # 3. Vẽ bản đồ, Ankh
    if _world_map and _level_system:
        current_pyramid = _level_system.get_current_pyramid()
        _world_map.draw(screen, _level_system.get_current_level(), current_pyramid)

    if _maze_loader:
        _maze_loader.draw_ankh(screen, show_ankh=_show_ankh)

    # 4. Vẽ giao diện cho nút bấm
    if _button_manager:
        # Don't show hover state when options menu is open
        display_hovered = None if _show_options else hovered
        _button_manager.draw_buttons(screen, display_hovered, clicked)

    if _show_options:
        _draw_options_menu(screen)

    # 5. Viết văn bản khi đang giải đố
    if _is_abandoning and _solution_pen:
        text_surf = _solution_pen.render_default("SHOWING SOLUTION", letter_spacing=0)
        screen.blit(text_surf, (165, 15))

    return None

"""
/**
 * Giao diện: Tùy chỉnh trò chơi
 * Đang cập nhật - Tạm thời
 */
"""
_options_button_rects = {}
def _draw_options_menu(screen):
    """Draw the options menu overlay with clickable buttons"""
    global _show_options, _options_button_rects, _show_ankh  # ADD _show_ankh here!

    # Panel dimensions
    panel_width = 400
    panel_height = 250
    cx = 400  # Center of game area (160 + 240)
    cy = 240  # Center of screen height (480 / 2)

    # Create panel rect
    rect = pygame.Rect(cx - panel_width//2, cy - panel_height//2, panel_width, panel_height)

    # Draw panel background
    pygame.draw.rect(screen, (40, 30, 20), rect)
    pygame.draw.rect(screen, (200, 150, 50), rect, 3)

    # Title
    title_font = pygame. font.SysFont("arial", 32, bold=True)
    title_surf = title_font.render("OPTIONS", True, (255, 215, 0))
    screen.blit(title_surf, (cx - title_surf.get_width()//2, rect.y + 20))

    # Option font
    option_font = pygame. font.SysFont("arial", 20)

    # Get current settings
    m_vol = int(music_manager.volume * 100)
    s_vol = int(sfx_manager.volume * 100)

    # Clear button rects
    _options_button_rects = {}

    # --- Music Volume ---
    music_y = rect.y + 80
    music_text = option_font.render(f"Music: {m_vol}%", True, (255, 255, 255))
    text_x = rect.x + 50
    screen.blit(music_text, (text_x, music_y))

    # Position buttons after text
    button_x = text_x + music_text.get_width() + 20

    # [-] button for music
    minus_music_surf = option_font.render("[-]", True, (255, 255, 255))
    minus_music_rect = pygame.Rect(button_x, music_y, minus_music_surf.get_width(), minus_music_surf.get_height())
    screen.blit(minus_music_surf, (button_x, music_y))
    _options_button_rects['minus_music'] = minus_music_rect

    # [+] button for music
    plus_music_x = button_x + minus_music_surf.get_width() + 10
    plus_music_surf = option_font.render("[+]", True, (255, 255, 255))
    plus_music_rect = pygame.Rect(plus_music_x, music_y, plus_music_surf.get_width(), plus_music_surf.get_height())
    screen.blit(plus_music_surf, (plus_music_x, music_y))
    _options_button_rects['plus_music'] = plus_music_rect

    # --- SFX Volume ---
    sfx_y = rect.y + 120
    sfx_text = option_font.render(f"SFX:  {s_vol}%", True, (255, 255, 255))
    screen.blit(sfx_text, (text_x, sfx_y))

    # Position buttons after text
    sfx_button_x = text_x + sfx_text.get_width() + 20

    # [-] button for SFX
    minus_sfx_surf = option_font.render("[-]", True, (255, 255, 255))
    minus_sfx_rect = pygame.Rect(sfx_button_x, sfx_y, minus_sfx_surf.get_width(), minus_sfx_surf.get_height())
    screen.blit(minus_sfx_surf, (sfx_button_x, sfx_y))
    _options_button_rects['minus_sfx'] = minus_sfx_rect

    # [+] button for SFX
    plus_sfx_x = sfx_button_x + minus_sfx_surf.get_width() + 10
    plus_sfx_surf = option_font.render("[+]", True, (255, 255, 255))
    plus_sfx_rect = pygame.Rect(plus_sfx_x, sfx_y, plus_sfx_surf.get_width(), plus_sfx_surf.get_height())
    screen.blit(plus_sfx_surf, (plus_sfx_x, sfx_y))
    _options_button_rects['plus_sfx'] = plus_sfx_rect

    # --- Show Ankh Toggle ---
    ankh_y = rect.y + 160
    ankh_label = option_font.render("Ankh:", True, (255, 255, 255))
    screen.blit(ankh_label, (text_x, ankh_y))

    # Position buttons after label
    ankh_button_x = text_x + ankh_label.get_width() + 20

    # [ON] button - Use global _show_ankh directly
    on_color = (255, 215, 0) if _show_ankh else (150, 150, 150)
    on_surf = option_font.render("[ON]", True, on_color)
    on_rect = pygame.Rect(ankh_button_x, ankh_y, on_surf.get_width(), on_surf.get_height())
    screen.blit(on_surf, (ankh_button_x, ankh_y))
    _options_button_rects['on_ankh'] = on_rect

    # / separator
    sep_x = ankh_button_x + on_surf.get_width() + 5
    sep_surf = option_font.render("/", True, (255, 255, 255))
    screen.blit(sep_surf, (sep_x, ankh_y))

    # [OFF] button - Use global _show_ankh directly
    off_x = sep_x + sep_surf.get_width() + 5
    off_color = (255, 215, 0) if not _show_ankh else (150, 150, 150)
    off_surf = option_font.render("[OFF]", True, off_color)
    off_rect = pygame.Rect(off_x, ankh_y, off_surf.get_width(), off_surf.get_height())
    screen.blit(off_surf, (off_x, ankh_y))
    _options_button_rects['off_ankh'] = off_rect

    # --- Close instruction ---
    close_text = option_font.render("Click OPTIONS to Close", True, (180, 180, 180))
    screen.blit(close_text, (cx - close_text.get_width() // 2, rect.y + 210))

"""
/**
 * Xử lý đầu vào của người chơi:
 * Di chuyển (Chuột/Bàn phím)
 * Các nút bấm
 */
"""
def handle_game_input(event, mouse_pos):
    global _button_manager, _player, _maze_loader, _turn_state, _show_options, _is_abandoning, _show_ankh, _user_profile

    # Xử lý chuột
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        clicked_btn = None
        for name, rect in _button_manager.button_rects.items():
            if rect.collidepoint(mouse_pos):
                clicked_btn = name
                _button_manager.set_clicked(name)
                break

        if clicked_btn == 'option':
            _show_options = not _show_options
            return 'option'

        if not _show_options:
            if clicked_btn == 'undo':
                undo_move()
                return 'undo'
            if clicked_btn == 'reset':
                _is_abandoning = False
                restart_level()
                return 'reset'
            # --- FIX: Handle Quit ---
            if clicked_btn == 'quit':
                return 'quit'

        if _show_options:
            # Use 640x480 screen dimensions
            cx = 400  # Center of game area (matching _draw_options_menu)
            cy = 240
            panel_width = 400
            panel_height = 250
            rect_x = cx - panel_width // 2
            rect_y = cy - panel_height // 2

            # Get current settings
            m_vol = int(music_manager.get_volume() * 100)
            s_vol = int(sfx_manager.get_volume() * 100)

            # Calculate text widths to match button positions
            option_font = pygame.font.SysFont("arial", 20)

            text_x = rect_x + 50

            # Music line
            music_y = rect_y + 80
            music_text = option_font.render(f"Music: {m_vol}%", True, (255, 255, 255))
            button_x = text_x + music_text.get_width() + 20

            minus_music_surf = option_font.render("[-]", True, (255, 255, 255))
            minus_music_rect = pygame.Rect(button_x, music_y, minus_music_surf.get_width(),
                                           minus_music_surf.get_height())

            plus_music_x = button_x + minus_music_surf.get_width() + 10
            plus_music_surf = option_font.render("[+]", True, (255, 255, 255))
            plus_music_rect = pygame.Rect(plus_music_x, music_y, plus_music_surf.get_width(),
                                          plus_music_surf.get_height())

            # SFX line
            sfx_y = rect_y + 120
            sfx_text = option_font.render(f"SFX:   {s_vol}%", True, (255, 255, 255))
            sfx_button_x = text_x + sfx_text.get_width() + 20

            minus_sfx_surf = option_font.render("[-]", True, (255, 255, 255))
            minus_sfx_rect = pygame.Rect(sfx_button_x, sfx_y, minus_sfx_surf.get_width(), minus_sfx_surf.get_height())

            plus_sfx_x = sfx_button_x + minus_sfx_surf.get_width() + 10
            plus_sfx_surf = option_font.render("[+]", True, (255, 255, 255))
            plus_sfx_rect = pygame.Rect(plus_sfx_x, sfx_y, plus_sfx_surf.get_width(), plus_sfx_surf.get_height())

            # Ankh line
            ankh_y = rect_y + 160
            ankh_label = option_font.render("Ankh:", True, (255, 255, 255))
            ankh_button_x = text_x + ankh_label.get_width() + 20

            on_surf = option_font.render("[ON]", True, (255, 215, 0))
            on_rect = pygame.Rect(ankh_button_x, ankh_y, on_surf.get_width(), on_surf.get_height())

            sep_x = ankh_button_x + on_surf.get_width() + 5
            sep_surf = option_font.render("/", True, (255, 255, 255))

            off_x = sep_x + sep_surf.get_width() + 5
            off_surf = option_font.render("[OFF]", True, (255, 215, 0))
            off_rect = pygame.Rect(off_x, ankh_y, off_surf.get_width(), off_surf.get_height())

            # Handle music clicks
            if minus_music_rect.collidepoint(mouse_pos):
                new_vol = max(0, music_manager.get_volume() - 0.1)
                music_manager.set_volume(new_vol)
                if _user_profile:
                    if 'options' not in _user_profile:
                        _user_profile['options'] = {}
                    _user_profile['options']['music_volume'] = new_vol
                    ProfileManager.save_profile(_user_profile)
            elif plus_music_rect.collidepoint(mouse_pos):
                new_vol = min(1.0, music_manager.get_volume() + 0.1)
                music_manager.set_volume(new_vol)
                if _user_profile:
                    if 'options' not in _user_profile:
                        _user_profile['options'] = {}
                    _user_profile['options']['music_volume'] = new_vol
                    ProfileManager.save_profile(_user_profile)
            # Handle SFX clicks
            elif minus_sfx_rect.collidepoint(mouse_pos):
                new_vol = max(0, sfx_manager.get_volume() - 0.1)
                sfx_manager.set_volume(new_vol)
                if _user_profile:
                    if 'options' not in _user_profile:
                        _user_profile['options'] = {}
                    _user_profile['options']['sfx_volume'] = new_vol
                    ProfileManager.save_profile(_user_profile)
            elif plus_sfx_rect.collidepoint(mouse_pos):
                new_vol = min(1.0, sfx_manager.get_volume() + 0.1)
                sfx_manager.set_volume(new_vol)
                if _user_profile:
                    if 'options' not in _user_profile:
                        _user_profile['options'] = {}
                    _user_profile['options']['sfx_volume'] = new_vol
                    ProfileManager.save_profile(_user_profile)
            # Handle ankh clicks
            elif on_rect.collidepoint(mouse_pos):
                _show_ankh = True
                if _user_profile:
                    if 'options' not in _user_profile:
                        _user_profile['options'] = {}
                    _user_profile['options']['show_ankh'] = True
                    ProfileManager.save_profile(_user_profile)
            elif off_rect.collidepoint(mouse_pos):
                _show_ankh = False
                if _user_profile:
                    if 'options' not in _user_profile:
                        _user_profile['options'] = {}
                    _user_profile['options']['show_ankh'] = False
                    ProfileManager.save_profile(_user_profile)
            return None

    if _show_options: return None
    if _turn_state != TurnState.PLAYER_INPUT: return None
    if _is_abandoning: return None

    # Xử lý bàn phím
    if _player and _maze_loader:
        move = _player.handle_input()
        if move:
            dx, dy = move
            _execute_player_move(dx, dy)

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        if _player and _maze_loader:
            mx, my = mouse_pos
            gx = (mx - maze_coord_x) // _maze_loader.cell_size
            gy = (my - maze_coord_y) // _maze_loader.cell_size
            if 0 <= gx < _maze_loader.maze_size and 0 <= gy < _maze_loader.maze_size:
                dx = gx - _player.x
                dy = gy - _player.y
                if dx == 0 and dy == 0:
                    _execute_player_move(0, 0)
                elif abs(dx) + abs(dy) == 1:
                    _execute_player_move(dx, dy)

    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
        _button_manager.clear_clicked()
    return None

"""
/**
 * Thực thi di chuyển của người chơi
 */
"""
def _execute_player_move(dx, dy):
    global _player, _maze_loader, _turn_state
    if not _player.is_ready(): return
    tx = _player.x + dx
    ty = _player.y + dy
    for e in _maze_loader.enemies_list:
        if e.x == tx and e.y == ty: return
    if _player.check_eligible_move(tx, ty, _maze_loader.maze_size, _maze_loader.parsed['walls'], _maze_loader.gate_obj):
        _maze_loader.save_state(_player)
        _player.move_player(dx, dy)
        _turn_state = TurnState.PLAYER_MOVING

"""
/**
 * Nhận thông tin khi di chuột
 */
"""
def get_hover_state(mouse_pos):
    if not _button_manager: return None
    for name, rect in _button_manager.button_rects.items():
        if rect.collidepoint(mouse_pos): return name
    return None

"""
/**
 * Nhận thông tin khi nhấp chuột
 */
"""
def get_clicked_state():
    return _button_manager.clicked_button if _button_manager else None