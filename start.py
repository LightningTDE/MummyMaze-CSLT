import sys
import os
import runpy

# 1. Get the current directory (the root folder where start.py is)
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Add this root directory to Python's search path
#    This allows Python to find the 'api' folder!
sys.path.append(current_dir)

# 3. Construct the full path to your main.py inside the dist folder
path_to_main = os.path.join(current_dir, 'dist', 'main.py')

# 4. Run the file
print(f"Launching game from: {path_to_main}...")
runpy.run_path(path_to_main, run_name='__main__')