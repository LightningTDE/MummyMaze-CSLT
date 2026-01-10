import random
from collections import deque
from api.io.Lightning.entities.Enemy import EnemyAI


# --- Helper Class for Simulation ---
class SimGate:
    """Mimics the visual Gate object for AI collision checks during generation"""

    def __init__(self, x, y, is_open):
        self.grid_x = x
        self.grid_y = y
        self.open = is_open

    def is_blocking(self):
        return not self.open


class MazeGenerator:
    def __init__(self):
        self.min_loops = 0

    def generate_level(self, difficulty):
        config = self._get_config(difficulty)
        size = config['size']

        attempts = 0
        max_attempts = 1000

        while attempts < max_attempts:
            attempts += 1
            if attempts % 50 == 0:
                print(f"Gen: Attempt {attempts}...")

            # 1. Structure
            walls_layout = self._generate_layout(size)
            self._braid_maze(walls_layout, size, config['braid_factor'])
            raw_walls = self._get_raw_walls(walls_layout, size)
            pruned_walls = self._smart_prune_walls(raw_walls, size, config['wall_density'])

            # 2. Place Entities
            level_data = self._place_entities(size, pruned_walls, config)
            if not level_data:
                continue

            # 3. Finalize Walls
            level_data['walls'] = self._merge_walls(level_data['walls'])

            # 4. Verify Solvability & Print Debug Solution
            # We capture the solution path instead of just a boolean
            solution_path = self._is_level_solvable(level_data, size)

            if solution_path:
                print(f"✅ Generated clean level in {attempts} attempts.")

                # --- DEBUG: PRINT SOLUTION ---
                print(f"\n🧩 DEBUG: Solution Path ({len(solution_path)} steps):")
                print(solution_path)
                print("-" * 40 + "\n")
                # -----------------------------

                return level_data

        print("⚠️ Generation failed. Creating Fallback Level.")
        return self._generate_fallback_level(size, difficulty)

    @staticmethod
    def _get_config(difficulty):
        if difficulty == 'easy':
            return {'size': 6, 'min_enemies': 1, 'max_enemies': 2,
                    'enemy_pool': ['white_mummy', 'red_mummy', 'scorpion'], 'traps': 0,
                    'use_key_gate': False, 'braid_factor': 0.5, 'wall_density': 0.5, 'difficulty_str': 'easy'}
        elif difficulty == 'hard':
            return {'size': 10, 'min_enemies': 2, 'max_enemies': 3,
                    'enemy_pool': ['white_mummy', 'red_mummy', 'scorpion', 'red_scorpion'], 'traps': 2,
                    'use_key_gate': True, 'braid_factor': 1.0, 'wall_density': 0.5, 'difficulty_str': 'hard'}
        else:
            return {'size': 8, 'min_enemies': 2, 'max_enemies': 3,
                    'enemy_pool': ['white_mummy', 'red_mummy', 'scorpion'], 'traps': 1, 'use_key_gate': True,
                    'braid_factor': 0.7, 'wall_density': 0.5, 'difficulty_str': 'medium'}

    def _generate_fallback_level(self, size, difficulty):
        walls_layout = self._generate_layout(size)
        self._braid_maze(walls_layout, size, 1.0)
        raw_walls = self._get_raw_walls(walls_layout, size)
        pruned = self._smart_prune_walls(raw_walls, size, 0.2)
        walls = self._merge_walls(pruned)
        player = {'x': 0, 'y': 0, 'direction': 'down'}
        exit_pos = {'x': size - 1, 'y': size - 1}
        walls = [w for w in walls if not (w['x'] == exit_pos['x'] and w['y'] == exit_pos['y'])]
        enemies = []
        if difficulty != 'easy':
            enemies.append({'type': 'white_mummy', 'x': size - 1, 'y': 0})
        return {
            "difficulty": "fallback", "mazeType": str(size), "maze_size": size,
            "player": player, "exit": exit_pos,
            "enemies": enemies, "traps": [],
            "walls": walls, "key": None, "gate": None
        }

    def _place_entities(self, size, walls, config):
        occupied = set()
        side = random.randint(0, 3)
        if side == 0:
            exit_pos = {'x': random.randint(0, size - 1), 'y': 0}
        elif side == 1:
            exit_pos = {'x': random.randint(0, size - 1), 'y': size - 1}
        elif side == 2:
            exit_pos = {'x': 0, 'y': random.randint(0, size - 1)}
        else:
            exit_pos = {'x': size - 1, 'y': random.randint(0, size - 1)}
        occupied.add((exit_pos['x'], exit_pos['y']))
        wall_to_remove = None
        if side == 0:
            target = {'x': exit_pos['x'], 'y': 0, 'dir': 'horizontal'}
        elif side == 2:
            target = {'x': 0, 'y': exit_pos['y'], 'dir': 'vertical'}
        else:
            target = None
        if target:
            for w in walls:
                if w['x'] == target['x'] and w['y'] == target['y'] and w['dir'] == target['dir']:
                    wall_to_remove = w
                    break
        if wall_to_remove: walls.remove(wall_to_remove)
        player_pos = None
        for _ in range(50):
            px, py = random.randint(0, size - 1), random.randint(0, size - 1)
            if (px, py) not in occupied:
                dist = self._get_path_distance((px, py), (exit_pos['x'], exit_pos['y']), walls, size)
                if dist > size // 2:
                    player_pos = {'x': px, 'y': py, 'direction': 'down'}
                    occupied.add((px, py))
                    break
        if not player_pos: return None
        enemies = []
        min_e = config.get('min_enemies', 1)
        max_e = config.get('max_enemies', 1)
        count = random.randint(min_e, max_e)
        pool = config.get('enemy_pool', ['white_mummy'])
        if pool:
            for _ in range(count):
                e_type = random.choice(pool)
                for _ in range(50):
                    ex, ey = random.randint(0, size - 1), random.randint(0, size - 1)
                    if (ex, ey) not in occupied:
                        dist = self._get_path_distance((ex, ey), (player_pos['x'], player_pos['y']), walls, size)
                        safe_dist = 6 if config['difficulty_str'] == 'hard' else 4
                        if dist > safe_dist:
                            enemies.append({'type': e_type, 'x': ex, 'y': ey})
                            occupied.add((ex, ey))
                            break
        key_data = None
        gate_data = None
        if config['use_key_gate']:
            valid_walls = [w for w in walls if w['dir'] == 'horizontal' and 1 <= w['y'] <= size - 2]
            if valid_walls:
                target_wall = random.choice(valid_walls)
                gate_data = {'x': target_wall['x'], 'y': target_wall['y']}
                walls.remove(target_wall)
                for _ in range(50):
                    kx, ky = random.randint(0, size - 1), random.randint(0, size - 1)
                    if (kx, ky) not in occupied:
                        dist = self._get_path_distance((kx, ky), (player_pos['x'], player_pos['y']), walls, size)
                        if dist > 3:
                            key_data = {'x': kx, 'y': ky}
                            occupied.add((kx, ky))
                            break
        traps = []
        for _ in range(config['traps']):
            for _ in range(20):
                tx, ty = random.randint(0, size - 1), random.randint(0, size - 1)
                if (tx, ty) not in occupied:
                    traps.append({'x': tx, 'y': ty})
                    occupied.add((tx, ty))
                    break
        return {"difficulty": config['difficulty_str'], "mazeType": str(size), "maze_size": size, "player": player_pos,
                "exit": exit_pos, "enemies": enemies, "traps": traps, "walls": walls, "key": key_data,
                "gate": gate_data}

    @staticmethod
    def _generate_layout(size):
        grid = [[set() for _ in range(size)] for _ in range(size)]
        visited = set()
        stack = [(0, 0)]
        visited.add((0, 0))
        while stack:
            cx, cy = stack[-1]
            neighbors = []
            for dx, dy, d in [(0, -1, 'N'), (0, 1, 'S'), (-1, 0, 'W'), (1, 0, 'E')]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < size and 0 <= ny < size and (nx, ny) not in visited:
                    neighbors.append((nx, ny, dx, dy, d))
            if neighbors:
                nx, ny, dx, dy, d = random.choice(neighbors)
                if d == 'N':
                    grid[cx][cy].add('N')
                    grid[nx][ny].add('S')
                elif d == 'S':
                    grid[cx][cy].add('S')
                    grid[nx][ny].add('N')
                elif d == 'W':
                    grid[cx][cy].add('W')
                    grid[nx][ny].add('E')
                elif d == 'E':
                    grid[cx][cy].add('E')
                    grid[nx][ny].add('W')
                visited.add((nx, ny))
                stack.append((nx, ny))
            else:
                stack.pop()
        return grid

    @staticmethod
    def _braid_maze(grid, size, factor):
        dead_ends = []
        for x in range(size):
            for y in range(size):
                if len(grid[x][y]) == 1: dead_ends.append((x, y))
        random.shuffle(dead_ends)
        count = int(len(dead_ends) * factor)
        for i in range(count):
            cx, cy = dead_ends[i]
            neighbors = []
            for dx, dy, d, opp in [(0, -1, 'N', 'S'), (0, 1, 'S', 'N'), (-1, 0, 'W', 'E'), (1, 0, 'E', 'W')]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < size and 0 <= ny < size and d not in grid[cx][cy]:
                    neighbors.append((nx, ny, d, opp))
            if neighbors:
                nx, ny, d, opp = random.choice(neighbors)
                grid[cx][cy].add(d)
                grid[nx][ny].add(opp)

    @staticmethod
    def _get_raw_walls(grid, size):
        walls = []
        for x in range(size):
            for y in range(size):
                if 'N' not in grid[x][y]: walls.append({'x': x, 'y': y, 'dir': 'horizontal'})
                if 'W' not in grid[x][y]: walls.append({'x': x, 'y': y, 'dir': 'vertical'})
        return walls

    def _smart_prune_walls(self, walls, size, target_density):
        max_walls = int((size * size) * target_density)
        if len(walls) <= max_walls: return walls
        walls_copy = walls.copy()
        random.shuffle(walls_copy)
        removed = 0
        target = len(walls) - max_walls
        for wall in walls_copy:
            if removed >= target: break
            test = [w for w in walls if w != wall]
            if self._is_maze_connected(test, size):
                walls.remove(wall)
                removed += 1
        return walls

    def _is_maze_connected(self, walls, size):
        visited = set()
        queue = deque([(0, 0)])
        visited.add((0, 0))
        while queue:
            x, y = queue.popleft()
            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                nx, ny = x + dx, y + dy
                if not (0 <= nx < size and 0 <= ny < size): continue
                if (nx, ny) in visited: continue
                if self._check_wall(x, y, nx, ny, walls): continue
                visited.add((nx, ny))
                queue.append((nx, ny))
        return len(visited) == size * size

    @staticmethod
    def _merge_walls(walls):
        merged = {}
        for w in walls:
            key = (w['x'], w['y'])
            if key not in merged:
                merged[key] = w['dir']
            else:
                merged[key] = 'both'
        return [{'x': x, 'y': y, 'dir': d} for (x, y), d in merged.items()]

    def _get_path_distance(self, start, end, walls, size):
        queue = deque([(start[0], start[1], 0)])
        visited = {(start[0], start[1])}
        while queue:
            cx, cy, dist = queue.popleft()
            if cx == end[0] and cy == end[1]: return dist
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < size and 0 <= ny < size:
                    if (nx, ny) not in visited:
                        if not self._check_wall(cx, cy, nx, ny, walls):
                            visited.add((nx, ny))
                            queue.append((nx, ny, dist + 1))
        return -1

    @staticmethod
    def _check_wall(x1, y1, x2, y2, walls):
        if x2 > x1:
            for w in walls:
                if w['x'] == x2 and w['y'] == y2 and w['dir'] in ['vertical', 'both']: return True
        elif x2 < x1:
            for w in walls:
                if w['x'] == x1 and w['y'] == y1 and w['dir'] in ['vertical', 'both']: return True
        elif y2 > y1:
            for w in walls:
                if w['x'] == x2 and w['y'] == y2 and w['dir'] in ['horizontal', 'both']: return True
        elif y2 < y1:
            for w in walls:
                if w['x'] == x1 and w['y'] == y1 and w['dir'] in ['horizontal', 'both']: return True
        return False

    def _is_level_solvable(self, level_data, size):
        start = (level_data['player']['x'], level_data['player']['y'])
        target = (level_data['exit']['x'], level_data['exit']['y'])

        # Fix: Handle missing key/gate safely
        key_pos = None
        if level_data.get('key'):
            key_pos = (level_data['key']['x'], level_data['key']['y'])

        gate_info = None
        if level_data.get('gate'):
            gate_info = (level_data['gate']['x'], level_data['gate']['y'])

        # --- FIX: COLLECT TRAPS ---
        # Add trap locations to a set for quick lookup
        traps = set()
        if 'traps' in level_data:
            for t in level_data['traps']:
                traps.add((t['x'], t['y']))
        # --------------------------

        ai = EnemyAI(size, level_data['walls'], gate=None)
        init_enemies = tuple((e['x'], e['y']) for e in level_data['enemies'])

        start_state = (start[0], start[1], False, init_enemies)
        queue = deque([start_state])
        visited = {start_state}

        # Path Tracking
        parent_map = {start_state: None}

        steps = 0
        max_steps = 5000

        while queue:
            steps += 1
            if steps > max_steps: return None

            current_state = queue.popleft()
            px, py, gate_open, e_positions = current_state

            # Target Reached
            if (px, py) == target:
                path = []
                trace = current_state
                while trace is not None:
                    path.append((trace[0], trace[1]))
                    trace = parent_map[trace]
                return path[::-1]

            for dx, dy in [(0, 0), (0, -1), (0, 1), (-1, 0), (1, 0)]:
                nx, ny = px + dx, py + dy

                # Standard Bounds & Wall Checks
                if not (0 <= nx < size and 0 <= ny < size): continue
                if self._check_wall(px, py, nx, ny, level_data['walls']): continue

                # --- FIX: CHECK TRAP COLLISION ---
                # Do not move onto a tile that has a trap
                if (nx, ny) in traps: continue
                # ---------------------------------

                if (nx, ny) in e_positions: continue

                if gate_info and not gate_open:
                    gx, gy = gate_info
                    if px == gx and py == gy - 1 and nx == gx and ny == gy: continue
                    if px == gx and py == gy and nx == gx and ny == gy - 1: continue

                next_gate_open = gate_open
                if key_pos and (nx, ny) == key_pos: next_gate_open = True

                ai.gate = SimGate(gate_info[0], gate_info[1], next_gate_open) if gate_info else None

                next_e_positions = []
                player_died = False
                for i, pos in enumerate(e_positions):
                    enemy = {'type': level_data['enemies'][i]['type'], 'pos': [pos[0], pos[1]]}
                    path = ai.get_move_path(enemy, [nx, ny], difficulty=level_data['difficulty'])
                    new_pos = path[-1] if path else enemy['pos']

                    if path:
                        for step in path:
                            if step[0] == nx and step[1] == ny: player_died = True
                    if new_pos[0] == nx and new_pos[1] == ny: player_died = True
                    next_e_positions.append(tuple(new_pos))

                if player_died: continue

                new_state = (nx, ny, next_gate_open, tuple(next_e_positions))
                if new_state not in visited:
                    visited.add(new_state)
                    parent_map[new_state] = current_state
                    queue.append(new_state)

        return None