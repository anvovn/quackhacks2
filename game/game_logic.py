import time

# Basic information 
NIGHT_DURATION = 240
NIGHT = 1
FLOOR_TIMER = 90

# Player won't have class (unless player complexity gets high enough to benefit from class usage)
PLAYER_HEALTH = 10


# Every enemy will inherit from this (including bosses because I'm lazy)
class BaseEnemy:
    def __init__(self, health=None, attack=None, movement=None):
        self.health = 0
        self.attack = 0
        self.movement = 0

    def attack(target):
        PLAYER_HEALTH = PLAYER_HEALTH - self.attack

    def receive_damage(damage):
        self.health = self.health - damage

    def isAlive():
        return self.health <= 0

# Basic enemies
class Ghost(BaseEnemy):
    def __init__(self, hp, attack, movement):
        super().__init__(5, 1, 1)

class Zombie(BaseEnemy):
    def __init__(self, hp, attack, movement):
        super().__init__(10, 2, 1)

#Night methods
def update_night(night):
    print(f'Night {NIGHT} has been completed!')
    NIGHT = night + 1
    time.sleep(5)
    if NIGHT != 6:
        print(f'Night {NIGHT} has begun')
        game_time_loop()
    elif NIGHT == 6:
        print(f'You survived Five Nights at the EMU!')
    
def restart_night(night):
    print(f'You died')
    time.sleep(5)
    game_time_loop()

def display_countdown(current_time):
    print(f'Time: {NIGHT_DURATION - current_time} s')

def floor_time_is_up():
    for i in range(10):
        Ghost()

# The time loop so far
def game_time_loop():
    print(f'Night {NIGHT} has begun')
    start_time = time.time()
    floor_time = time.time()
    while True:
        time_passed = time.time - start_time
        remaining_time = NIGHT_DURATION - time_passed
        remaining_ft = FLOOR_TIMER - time_passed
        if remaining_time <= 0:
            update_night(NIGHT)
            break
        elif remaining_ft <= 0:
            floor_time_is_up()
        time.sleep(0.1)

