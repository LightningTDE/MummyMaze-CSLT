import os
import json
import pygame
import random
import math
from collections import deque

from api.io.Lightning.manager.SoundReader import sfx_manager
from api.io.Lightning.manager.Spritesheet import Spritesheet
from api.io.Lightning.maze.MazeGenerator import MazeGenerator
from api.io.Lightning.utils.ConfigFile import LEVELS_PATH, UI_PATH, OBJECTS_PATH, maze_coord_x, maze_coord_y
from api.io.Lightning.objects.Key import Key
from api.io.Lightning.objects.Gate import Gate
from api.io.Lightning.objects.Trap import Trap
from api.io.Lightning.entities.Enemy import Enemy


class FightEffect:
    def __init__(self, x, y, dust_frames, star_img, cell_size):
        self.x = x
        self.y = y
        self.cell_size = cell_size
        self.dust_frames = dust_frames
        self.frame_index = 0
        self.anim_speed = 0.45
        self.star_img = star_img
        self.stars = []
        if self.star_img:
            center = cell_size // 2
            for i in range(5):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(1.5, 3.5)
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed - 1
                self.stars.append({
                    'x': center, 'y': center, 'vx': vx, 'vy': vy,
                    'visible': False, 'spawn_frame': random.randint(1, 3)
                })
        self.finished = False

    def update(self):
        self.frame_index += self.anim_speed
        current_frame = int(self.frame_index)
        for star in self.stars:
            if current_frame >= star['spawn_frame']:
                star['visible'] = True
                star['x'] += star['vx']
                star['y'] += star['vy']
                star['vx'] *= 0.95
                star['vy'] *= 0.95
        if self.frame_index >= len(self.dust_frames) + 3:
            self.finished = True

    def draw(self, surface):
        if self.finished: return
        idx = int(self.frame_index)
        if idx < len(self.dust_frames):
            img = self.dust_frames[idx]
            draw_x = maze_coord_x + self.x * self.cell_size + (self.cell_size - img.get_width()) // 2
            draw_y = maze_coord_y + self.y * self.cell_size + (self.cell_size - img.get_height()) // 2
            surface.blit(img, (draw_x, draw_y))
        if self.star_img:
            base_x = maze_coord_x + self.x * self.cell_size
            base_y = maze_coord_y + self.y * self.cell_size
            for star in self.stars:
                if star['visible']:
                    draw_sx = base_x + int(star['x']) - (self.star_img.get_width() // 2)
                    draw_sy = base_y + int(star['y']) - (self.star_img.get_height() // 2)
                    surface.blit(self.star_img, (draw_sx, draw_sy))


class MazeLoader:
    def __init__(self, level_id=None, difficulty='medium', generate_infinite=False):
        self.level_id = level_id
        if generate_infinite:
            print("🎲 Generating procedural level...")
            generator = MazeGenerator()
            self.data = generator.generate_level(difficulty)
            self.parsed = self._parse_level_data(self.data)
        else:
            self.data = self._load_level()
            self.parsed = self._parse_level_from_json()

        self.maze_pixel_size = 360
        self.difficulty = self.parsed["difficulty"]
        self.maze_size = self.parsed["maze_size"]
        self.stair_pos = self.parsed["exit"]
        self.cell_size = self.maze_pixel_size // self.maze_size

        self.backdrop_img = None
        self.floor_img = None
        self.wall_sprites = {}
        self.stair_sprites = {}
        self.arrow_sprites = []
        self.circle_img = None

        self.dust_frames = []
        self.star_img = None
        self.active_effects = []

        self.traps = []
        self.key_obj = None
        self.gate_obj = None
        self.enemies_list = []
        self.enemies_on_key = set()

        self.last_turn_time = 0

        self.history_stack = []
        self.pending_deaths = []
        self.turn_queue = deque()

        self.ankh_frames = []
        self.is_current_state_solvable = True
        self.generator_instance = MazeGenerator()
        self.ankh_timer = 0

        self._load_assets()
        self._create_objects()

    def _load_level(self):
        filepath = os.path.join(LEVELS_PATH, f'level_{self.level_id}.json')
        if not os.path.exists(filepath): return None
        with open(filepath, 'r') as f: data = json.load(f)
        return data

    def _parse_level_from_json(self):
        return self._parse_level_data(self.data)

    @classmethod
    def from_data(cls, data):
        """Create MazeLoader from saved maze data (for loading saved games).
        
        Args:
            data (dict): Saved maze data
            
        Returns:
            MazeLoader: New MazeLoader instance
        """
        loader = cls.__new__(cls)
        loader.data = data
        loader.parsed = cls._parse_level_data(data)
        
        # Initialize all attributes
        loader.maze_pixel_size = 360
        loader.difficulty = loader.parsed["difficulty"]
        loader.maze_size = loader.parsed["maze_size"]
        loader.stair_pos = loader.parsed["exit"]
        loader.cell_size = loader.maze_pixel_size // loader.maze_size
        
        loader.backdrop_img = None
        loader.floor_img = None
        loader.wall_sprites = {}
        loader.stair_sprites = {}
        loader.arrow_sprites = []
        loader.circle_img = None
        
        loader.dust_frames = []
        loader.star_img = None
        loader.active_effects = []
        
        loader.traps = []
        loader.key_obj = None
        loader.gate_obj = None
        loader.enemies_list = []
        loader.enemies_on_key = set()
        
        loader.last_turn_time = 0
        
        loader.history_stack = []
        loader.pending_deaths = []
        loader.turn_queue = deque()
        
        loader.ankh_frames = []
        loader.is_current_state_solvable = True
        loader.generator_instance = MazeGenerator()
        loader.ankh_timer = 0
        
        loader._load_assets()
        loader._create_objects()
        
        return loader
    
    @staticmethod
    def _parse_level_data(data):
        if not data: return None
        key_data = data.get('key')
        key = {'x': key_data['x'], 'y': key_data['y']} if key_data and 'x' in key_data else None
        gate_data = data.get('gate')
        gate = {'x': gate_data['x'], 'y': gate_data['y']} if gate_data and 'x' in gate_data else None
        return {
            'difficulty': data.get('difficulty', 'medium'),
            'maze_size': int(data['mazeType']),
            'player': data['player'],
            'exit': data['exit'],
            'enemies': data.get('enemies', []),
            'key': key,
            'gate': gate,
            'traps': data.get('traps', []),
            'walls': data.get('walls', [])
        }

    def reset(self):
        self._create_objects()
        self.active_effects = []
        self.pending_deaths = []
        self.turn_queue.clear()
        self.is_current_state_solvable = True
        self.history_stack.clear()

    def save_state(self, player):
        state = {
            'player': {'x': player.x, 'y': player.y, 'dir': player.direction},
            'gate_open': not self.gate_obj.is_blocking() if self.gate_obj else True,
            'gate_frame': self.gate_obj.current_frame if self.gate_obj else 0,
            'solvable': self.is_current_state_solvable,
            'enemies': [{'type': e.type, 'x': e.x, 'y': e.y, 'dir': e.direction} for e in self.enemies_list if
                        not e.is_dead],
            'traps': [t.is_triggered for t in self.traps],
            'enemies_on_key': [{'type': e.type, 'x': e.x, 'y': e.y} for e in self.enemies_on_key]
        }
        self.history_stack.append(state)

    def undo_last_move(self, player):
        if not self.history_stack: return False
        state = self.history_stack.pop()

        player.x = state['player']['x']
        player.y = state['player']['y']
        player.direction = state['player']['dir']
        player.target_x = player.x * player.tile_size
        player.target_y = player.y * player.tile_size
        player.pixel_x = player.target_x
        player.pixel_y = player.target_y
        player.is_moving = False

        if self.gate_obj:
            if state['gate_open']:
                self.gate_obj.state = self.gate_obj.STATE_OPEN
            else:
                self.gate_obj.state = self.gate_obj.STATE_CLOSED
            self.gate_obj.current_frame = state.get('gate_frame', 0)

        self.is_current_state_solvable = state['solvable']

        self.enemies_list.clear()
        self.enemies_on_key.clear()
        
        # Restore enemies_on_key data from saved state
        saved_enemies_on_key = state.get('enemies_on_key', [])
        
        for e_data in state['enemies']:
            new_enemy = Enemy(e_data['x'], e_data['y'], e_data['type'], self.maze_size, self.cell_size,
                              self.parsed['walls'], self.gate_obj)
            new_enemy.direction = e_data['dir']
            new_enemy.pixel_x = new_enemy.x * self.cell_size
            new_enemy.pixel_y = new_enemy.y * self.cell_size
            new_enemy.target_x = new_enemy.pixel_x
            new_enemy.target_y = new_enemy.pixel_y
            self.enemies_list.append(new_enemy)
            
            # Restore enemies_on_key by checking if this enemy should be in the set
            # We need to match by position and type since enemy objects are recreated
            for saved_enemy in saved_enemies_on_key:
                if (saved_enemy['x'] == new_enemy.x and 
                    saved_enemy['y'] == new_enemy.y and 
                    saved_enemy['type'] == new_enemy.type):
                    self.enemies_on_key.add(new_enemy)
                    break

        trap_states = state.get('traps', [False] * len(self.traps))
        for i, was_triggered in enumerate(trap_states):
            if i < len(self.traps):
                if self.traps[i].is_triggered and not was_triggered:
                    self.traps[i].reset()

        self.turn_queue.clear()
        self.pending_deaths.clear()
        self.active_effects.clear()
        return True

    def _create_objects(self):
        if self.parsed['key']:
            k = self.parsed['key']
            self.key_obj = Key(k['x'], k['y'], self.cell_size, self.maze_size)
        if self.parsed['gate']:
            g = self.parsed['gate']
            self.gate_obj = Gate(g['x'], g['y'], self.cell_size, self.maze_size)

        self.traps = []
        for t in self.parsed['traps']:
            self.traps.append(Trap(t['x'], t['y'], self.cell_size, self.maze_size))

        self.enemies_list = []
        for e_data in self.parsed['enemies']:
            new_enemy = Enemy(
                x=e_data['x'],
                y=e_data['y'],
                enemy_type=e_data['type'],
                maze_size=self.maze_size,
                tile_size=self.cell_size,
                walls=self.parsed['walls'],
                gate=self.gate_obj
            )
            self.enemies_list.append(new_enemy)

    def _load_assets(self):
        self.backdrop_img = pygame.image.load(os.path.join(UI_PATH, 'backdrop.jpg'))
        self.floor_img = pygame.image.load(os.path.join(OBJECTS_PATH, f'floor{self.maze_size}.jpg'))
        wall_sheet = Spritesheet(os.path.join(OBJECTS_PATH, f'walls{self.maze_size}.gif'))
        match self.maze_size:
            case 6:
                self.wall_sprites['horizontal'] = wall_sheet.get_image(12, 0, 72, 18)
                self.wall_sprites['vertical'] = wall_sheet.get_image(0, 0, 12, 78)
            case 8:
                self.wall_sprites['horizontal'] = wall_sheet.get_image(12, 0, 57, 18)
                self.wall_sprites['vertical'] = wall_sheet.get_image(0, 0, 12, 63)
            case 10:
                self.wall_sprites['horizontal'] = wall_sheet.get_image(8, 0, 44, 12)
                self.wall_sprites['vertical'] = wall_sheet.get_image(0, 0, 8, 48)
        stair_sheet = Spritesheet(os.path.join(OBJECTS_PATH, f"stairs{self.maze_size}.gif"))
        sw = stair_sheet.sheet.get_width() // 4
        sh = stair_sheet.sheet.get_height()
        self.stair_sprites['up'] = stair_sheet.get_image(0, 0, sw, sh)
        self.stair_sprites['right'] = stair_sheet.get_image(sw, 0, sw, sh)
        self.stair_sprites['down'] = stair_sheet.get_image(2 * sw, 0, sw, sh)
        self.stair_sprites['left'] = stair_sheet.get_image(3 * sw, 0, sw, sh)
        try:
            self.circle_img = pygame.image.load(os.path.join(UI_PATH, f'circle{self.maze_size}.png')).convert_alpha()
            arrow_sheet = pygame.image.load(os.path.join(UI_PATH, f'arrows{self.maze_size}.png')).convert_alpha()
            aw = arrow_sheet.get_width()
            ah = arrow_sheet.get_height() // 4
            self.arrow_sprites = [
                arrow_sheet.subsurface((0, 0, aw, ah)),
                arrow_sheet.subsurface((0, 2 * ah, aw, ah)),
                arrow_sheet.subsurface((0, ah, aw, ah)),
                arrow_sheet.subsurface((0, 3 * ah, aw, ah))
            ]
        except Exception:
            pass
        try:
            ankh_sheet = pygame.image.load(os.path.join(UI_PATH, 'ankh.png')).convert_alpha()
            sheet_w, sheet_h = ankh_sheet.get_size()
            frame_h = sheet_h // 4
            for i in range(4):
                self.ankh_frames.append(ankh_sheet.subsurface((0, i * frame_h, sheet_w, frame_h)))
        except Exception as e:
            print(f"Ankh load error: {e}")
        try:
            self.star_img = pygame.image.load(os.path.join(UI_PATH, 'star.png')).convert_alpha()
            dust_filename = f'dust{self.maze_size}.png'
            dust_path = os.path.join(UI_PATH, dust_filename)
            if not os.path.exists(dust_path):
                dust_path = os.path.join(UI_PATH, 'dust6.png')
            if os.path.exists(dust_path):
                dust_sheet = pygame.image.load(dust_path).convert_alpha()
                sheet_w, sheet_h = dust_sheet.get_size()
                frame_size = sheet_h
                cols = sheet_w // frame_size
                for i in range(cols):
                    frame = dust_sheet.subsurface((i * frame_size, 0, frame_size, frame_size))
                    self.dust_frames.append(frame)
        except Exception as e:
            print(f"Effect Load Error: {e}")

    def get_solution_path(self, player):
        if not player: return None
        current_enemies = []
        for e in self.enemies_list:
            if not e.is_dead:
                current_enemies.append({'type': e.type, 'x': e.x, 'y': e.y})
        gate_snapshot = None
        key_snapshot = None
        if self.gate_obj:
            gate_snapshot = {'x': self.gate_obj.grid_x, 'y': self.gate_obj.grid_y}
        if self.key_obj:
            key_snapshot = {'x': self.key_obj.grid_x, 'y': self.key_obj.grid_y}
        snapshot_data = {
            'player': {'x': player.x, 'y': player.y},
            'exit': self.parsed['exit'],
            'enemies': current_enemies,
            'walls': self.parsed['walls'],
            'traps': [{'x': t.grid_x, 'y': t.grid_y} for t in self.traps],
            'gate': gate_snapshot,
            'key': key_snapshot,
            'difficulty': self.difficulty
        }
        return self.generator_instance._is_level_solvable(snapshot_data, self.maze_size)

    def check_solvability(self, player):
        if not player: return
        was_solvable = self.is_current_state_solvable
        current_enemies = []
        for e in self.enemies_list:
            if not e.is_dead:
                current_enemies.append({'type': e.type, 'x': e.x, 'y': e.y})
        gate_snapshot = None
        key_snapshot = None
        if self.gate_obj and self.gate_obj.is_blocking():
            gate_snapshot = {'x': self.gate_obj.grid_x, 'y': self.gate_obj.grid_y}
            if self.key_obj and not self.key_obj.activate():
                key_snapshot = {'x': self.key_obj.grid_x, 'y': self.key_obj.grid_y}
        snapshot_data = {
            'player': {'x': player.x, 'y': player.y},
            'exit': self.parsed['exit'],
            'enemies': current_enemies,
            'walls': self.parsed['walls'],
            'traps': [{'x': t.grid_x, 'y': t.grid_y} for t in self.traps],
            'gate': gate_snapshot,
            'key': key_snapshot,
            'difficulty': self.difficulty
        }
        result = self.generator_instance._is_level_solvable(snapshot_data, self.maze_size)
        self.is_current_state_solvable = (result is not None)
        if was_solvable and not self.is_current_state_solvable:
            sfx_manager.play('badankh')

    def draw_ankh(self, surface, show_ankh=True):
        """
        Draw the ankh indicator (solvability status).
        
        Args:
            surface: Pygame surface to draw on
            show_ankh: Whether to display the ankh (user preference)
        """
        # Return early if user disabled ankh display
        if not show_ankh:
            return
        
        if not self.ankh_frames: return
        base_idx = 0 if self.is_current_state_solvable else 2
        glow_idx = base_idx + 1
        x, y = 90, 320
        if base_idx < len(self.ankh_frames):
            surface.blit(self.ankh_frames[base_idx], (x, y))
        self.ankh_timer += 0.08
        pulse = (math.sin(self.ankh_timer) + 1) / 2
        alpha = int(pulse * 255)
        if glow_idx < len(self.ankh_frames):
            glow_surf = self.ankh_frames[glow_idx].copy()
            glow_surf.set_alpha(alpha)
            surface.blit(glow_surf, (x, y))

    def spawn_fight_cloud(self, x, y):
        if self.dust_frames:
            effect = FightEffect(x, y, self.dust_frames, self.star_img, self.cell_size)
            self.active_effects.append(effect)

    def init_enemy_turn_sequence(self):
        order = {'scorpion': 0, 'red_scorpion': 1, 'white_mummy': 2, 'red_mummy': 3}
        active = [e for e in self.enemies_list if not e.is_dead]
        active.sort(key=lambda e: order.get(e.type, 99))
        self.turn_queue = deque(active)
        self.last_turn_time = 0

    def update_turn_sequence(self, player_pos):
        if any(e.paused for e in self.enemies_list): return False
        if self.are_enemies_moving():
            self.last_turn_time = pygame.time.get_ticks()
            return False
        if self.pending_deaths: return False
        if pygame.time.get_ticks() - self.last_turn_time < 50:
            return False
        if not self.turn_queue: return True
        next_enemy = self.turn_queue[0]
        if next_enemy.is_dead or next_enemy not in self.enemies_list:
            self.turn_queue.popleft()
            return self.update_turn_sequence(player_pos)
        self.turn_queue.popleft()
        next_enemy.move_logic([player_pos[0], player_pos[1]], self.difficulty)
        if not next_enemy.move_queue: return self.update_turn_sequence(player_pos)
        return False

    def trigger_enemy_afk(self):
        for enemy in self.enemies_list:
            enemy.trigger_afk()

    def are_enemies_moving(self):
        for enemy in self.enemies_list:
            if enemy.is_moving or len(enemy.move_queue) > 0:
                return True
        return False

    def pause_enemies(self):
        for enemy in self.enemies_list:
            enemy.paused = True

    def resume_enemies(self):
        for enemy in self.enemies_list:
            enemy.paused = False

    def resolve_enemy_collisions(self):
        pos_map = {}
        for enemy in self.enemies_list:
            if enemy.state.name == "DIE": continue
            pos = (enemy.x, enemy.y)
            if pos not in pos_map: pos_map[pos] = []
            pos_map[pos].append(enemy)
        collision_occurred = False
        for pos, enemies in pos_map.items():
            if len(enemies) > 1:
                sfx_manager.play('pummel')
                self.spawn_fight_cloud(pos[0], pos[1])
                enemies.sort(key=lambda e: e.strength, reverse=True)
                victims = enemies[1:]
                self.pending_deaths.extend(victims)
                collision_occurred = True
        return collision_occurred

    def process_pending_deaths(self):
        for v in self.pending_deaths:
            v.trigger_die(instant=True)
        self.pending_deaths.clear()

    def update(self):
        if self.key_obj: self.key_obj.update()
        if self.gate_obj: self.gate_obj.update()
        for trap in self.traps: trap.update()
        for enemy in self.enemies_list: enemy.update()
        self.enemies_list = [e for e in self.enemies_list if not e.is_dead]
        for eff in self.active_effects: eff.update()
        self.active_effects = [e for e in self.active_effects if not e.finished]
        if self.key_obj and self.gate_obj:
            kx, ky = self.key_obj.grid_x, self.key_obj.grid_y
            for enemy in self.enemies_list:
                if enemy.x == kx and enemy.y == ky:
                    if enemy not in self.enemies_on_key:
                        self.gate_obj.toggle()
                        self.key_obj.activate()
                        sfx_manager.play('gate')
                        self.enemies_on_key.add(enemy)
                else:
                    if enemy in self.enemies_on_key:
                        self.enemies_on_key.remove(enemy)

    def draw_background(self, surface):
        surface.blit(self.backdrop_img, (0, 0))
        surface.blit(self.floor_img, (maze_coord_x, maze_coord_y))

    def _get_active_indicator(self, mouse_pos, player):
        if not player or not self.circle_img or not mouse_pos: return None
        if not player.is_ready(): return None
        mx, my = mouse_pos
        grid_x = (mx - maze_coord_x) // self.cell_size
        grid_y = (my - maze_coord_y) // self.cell_size
        if not (0 <= grid_x < self.maze_size and 0 <= grid_y < self.maze_size): return None
        if grid_x == player.x and grid_y == player.y:
            return {'type': 'circle', 'img': self.circle_img, 'x': grid_x, 'y': grid_y}
        dx, dy = grid_x - player.x, grid_y - player.y
        if abs(dx) + abs(dy) == 1:
            for enemy in self.enemies_list:
                if enemy.x == grid_x and enemy.y == grid_y:
                    return None
            if player.check_eligible_move(grid_x, grid_y, self.maze_size, self.parsed['walls'], self.gate_obj):
                arrow_idx = 0
                if dx == 1:
                    arrow_idx = 2
                elif dx == -1:
                    arrow_idx = 1
                elif dy == 1:
                    arrow_idx = 0
                elif dy == -1:
                    arrow_idx = 3
                if 0 <= arrow_idx < len(self.arrow_sprites):
                    return {'type': 'arrow', 'img': self.arrow_sprites[arrow_idx], 'x': grid_x, 'y': grid_y}
        return None

    def draw(self, surface, player=None, enemies=None, mouse_pos=None):
        indicator = self._get_active_indicator(mouse_pos, player)
        self.draw_stairs(surface)

        # 1. Draw Trap Floor Base (Bottom Layer)
        for trap in self.traps: trap.draw(surface)

        walls = self.parsed['walls']
        current_enemies = enemies if enemies is not None else self.enemies_list

        # FIX: Draw entities and falling blocks inside the row loop for proper Z-ordering
        # Active blocks must cover the player (on same row) and be covered by the front wall (next row)
        draw_priority = {'scorpion': 0, 'red_scorpion': 1, 'player': 2, 'white_mummy': 3, 'red_mummy': 4,
                         'trap_block': 5}

        for row in range(self.maze_size + 1):
            if self.gate_obj and self.gate_obj.grid_y == row: self.gate_obj.draw(surface)
            self._draw_walls_for_row(surface, walls, row)
            if self.key_obj and self.key_obj.grid_y == row: self.key_obj.draw(surface)
            if indicator and indicator['y'] == row:
                img = indicator['img']
                draw_x = maze_coord_x + indicator['x'] * self.cell_size + (self.cell_size - img.get_width()) // 2
                draw_y = maze_coord_y + indicator['y'] * self.cell_size + (self.cell_size - img.get_height()) // 2
                surface.blit(img, (draw_x, draw_y))

            row_entities = []
            if player and player.y == row:
                row_entities.append({'type': 'player', 'obj': player})
            for enemy in current_enemies:
                if enemy.y == row:
                    row_entities.append({'type': enemy.type, 'obj': enemy})

            # --- FIX: Add falling trap blocks to this row's entity list ---
            for trap in self.traps:
                if trap.grid_y == row and trap.is_triggered:
                    row_entities.append({'type': 'trap_block', 'obj': trap})

            row_entities.sort(key=lambda item: draw_priority.get(item['type'], 0))

            for item in row_entities:
                if item['type'] == 'trap_block':
                    item['obj'].draw_active_block(surface)
                else:
                    item['obj'].draw(surface)

            for eff in self.active_effects:
                if eff.y == row:
                    eff.draw(surface)

    def _draw_walls_for_row(self, surface, walls, row):
        for data in walls:
            if data['y'] != row: continue
            wall_x, direction = data['x'], data['dir']
            if wall_x < 0 or wall_x > self.maze_size - 1: continue
            if row < 0 or row > self.maze_size - 1: continue
            base_x = maze_coord_x + wall_x * self.cell_size
            base_y = maze_coord_y + row * self.cell_size
            offset_x = int(self.cell_size * 0.08)
            offset_y = int(self.cell_size * 0.27)
            draw_x = base_x - offset_x
            draw_y = base_y - offset_y
            if direction == 'both':
                if row > 0: surface.blit(self.wall_sprites['horizontal'], (draw_x, draw_y))
                if wall_x > 0: surface.blit(self.wall_sprites['vertical'], (draw_x, draw_y))
            elif direction == 'horizontal':
                if row > 0: surface.blit(self.wall_sprites['horizontal'], (draw_x, draw_y))
            elif direction == 'vertical':
                if wall_x > 0: surface.blit(self.wall_sprites['vertical'], (draw_x, draw_y))

    def draw_stairs(self, surface):
        if not self.stair_pos: return
        gx, gy = self.stair_pos['x'], self.stair_pos['y']
        if gx <= 0:
            stair_img = self.stair_sprites.get('left')
            draw_x = maze_coord_x - stair_img.get_width()
            draw_y = maze_coord_y + gy * self.cell_size + (self.cell_size - stair_img.get_height()) // 2
        elif gx >= self.maze_size - 1:
            stair_img = self.stair_sprites.get('right')
            draw_x = maze_coord_x + self.maze_size * self.cell_size
            draw_y = maze_coord_y + gy * self.cell_size + (self.cell_size - stair_img.get_height()) // 2
        elif gy <= 0:
            stair_img = self.stair_sprites.get('up')
            draw_x = maze_coord_x + gx * self.cell_size + (self.cell_size - stair_img.get_width()) // 2
            draw_y = maze_coord_y - stair_img.get_height()
        else:
            stair_img = self.stair_sprites.get('down')
            draw_x = maze_coord_x + gx * self.cell_size + (self.cell_size - stair_img.get_width()) // 2
            draw_y = maze_coord_y + self.maze_size * self.cell_size
        if stair_img:
            surface.blit(stair_img, (draw_x, draw_y))

    def check_trap_collision(self, x, y):
        for t in self.traps:
            if t.check_collision(x, y):
                # Return the trap object so GameUI can control it
                return t
        return None

    def check_key_collision(self, x, y):
        if self.key_obj and self.key_obj.check_collision(x, y):
            self.key_obj.activate()
            if self.gate_obj:
                self.gate_obj.toggle()
                sfx_manager.play('gate')
            return True
        return False

    def is_gate_blocking(self, fx, fy, tx, ty):
        if not self.gate_obj or not self.gate_obj.is_blocking(): return False
        gx, gy = self.gate_obj.grid_x, self.gate_obj.grid_y
        if fx == gx and fy == gy - 1 and tx == gx and ty == gy: return True
        if fx == gx and fy == gy and tx == gx and ty == gy - 1: return True
        return False

    def face_enemies_to_player(self, player):
        for enemy in self.enemies_list:
            if not enemy.is_moving and not enemy.is_dead and enemy.state.name != 'DIE':
                enemy.face_target(player.x, player.y)