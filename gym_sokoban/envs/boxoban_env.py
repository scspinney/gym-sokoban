from .sokoban_env import SokobanEnv
from .render_utils import room_to_rgb
import os
from os import listdir
from os.path import isfile, join
import requests
import zipfile
from tqdm import tqdm
import random
import numpy as np
from gym.spaces import Box

class BoxobanEnv(SokobanEnv):
    num_boxes = 4
    dim_room=(10, 10)

    def __init__(self,
             observation_mode = "rgb_array",
             dim_room = (10,10),
             max_steps=120,
             difficulty='unfiltered', 
             split='train'):
        self.difficulty = difficulty
        self.split = split
        self.verbose = False
        self.observation_mode = observation_mode
        self.dim_room = dim_room
        super(BoxobanEnv, self).__init__(self.observation_mode, self.dim_room, max_steps, self.num_boxes, None)
        

    def reset(self):
        self.cache_path = os.path.join(os.environ["SCRATCH"], ".sokoban_cache")
        self.train_data_dir = os.path.join(self.cache_path, 'boxoban-levels-master', self.difficulty, self.split)
        if not os.path.exists(self.cache_path):
           
            url = "https://github.com/deepmind/boxoban-levels/archive/master.zip"
            
            if self.verbose:
                print('Boxoban: Pregenerated levels not downloaded.')
                print('Starting download from "{}"'.format(url))

            response = requests.get(url, stream=True)

            if response.status_code != 200:
                raise "Could not download levels from {}. If this problem occurs consistantly please report the bug under https://github.com/mpSchrader/gym-sokoban/issues. ".format(url)

            os.makedirs(self.cache_path)
            path_to_zip_file = os.path.join(self.cache_path, 'boxoban_levels-master.zip')
            with open(path_to_zip_file, 'wb') as handle:
                for data in tqdm(response.iter_content()):
                    handle.write(data)

            zip_ref = zipfile.ZipFile(path_to_zip_file, 'r')
            zip_ref.extractall(self.cache_path)
            zip_ref.close()
        
        self.select_room()

        self.num_env_steps = 0
        self.reward_last = 0
        self.boxes_on_target = 0

        starting_observation = self.render(self.observation_mode)

        return starting_observation

    def select_room(self):
        
        generated_files = [f for f in listdir(self.train_data_dir) if isfile(join(self.train_data_dir, f))]
        source_file = join(self.train_data_dir, random.choice(generated_files))

        maps = []
        current_map = []
        
        with open(source_file, 'r') as sf:
            for line in sf.readlines():
                if ';' in line and current_map:
                    maps.append(current_map)
                    current_map = []
                if '#' == line[0]:
                    current_map.append(line.strip())
        
        maps.append(current_map)

        selected_map = random.choice(maps)

        if self.verbose:
            print('Selected Level from File "{}"'.format(source_file))

        self.room_fixed, self.room_state, self.box_mapping = self.generate_room(selected_map)


    def generate_room(self, select_map):
        room_fixed = []
        room_state = []

        targets = []
        boxes = []
        for row in select_map:
            room_f = []
            room_s = []

            for e in row:
                if e == '#':
                    room_f.append(0)
                    room_s.append(0)

                elif e == '@':
                    self.player_position = np.array([len(room_fixed), len(room_f)])
                    room_f.append(1)
                    room_s.append(5)


                elif e == '$':
                    boxes.append((len(room_fixed), len(room_f)))
                    room_f.append(1)
                    room_s.append(4)

                elif e == '.':
                    targets.append((len(room_fixed), len(room_f)))
                    room_f.append(2)
                    room_s.append(2)

                else:
                    room_f.append(1)
                    room_s.append(1)

            room_fixed.append(room_f)
            room_state.append(room_s)


        # used for replay in room generation, unused here because pre-generated levels
        box_mapping = {}

        return np.array(room_fixed), np.array(room_state), box_mapping


    # def set_observation_mode(self,observation_mode):
    #     self.observation_mode=observation_mode
    #     if self.observation_mode == "vector":
    #         self.observation_space = self.dim_room[0]*self.dim_room[1] 
    #     elif self.observation_mode == "map":
    #         self.observation_space = Box(low=0, high=5, shape=(self.screen_height, self.screen_width, 1), dtype=np.uint8)
    #     else:
    #         self.observation_space  = Box(low=0, high=255, shape=(self.screen_height, self.screen_width, 3), dtype=np.uint8)


