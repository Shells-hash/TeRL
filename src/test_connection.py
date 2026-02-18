from src.environment import TerrariaEnv

from src.tasks import get_task

env = TerrariaEnv(task=get_task("locomotion"))

state = env.reset()

while True:
    state, reward, terminated, truncated, info = env.step(2)  # always move right
    done = terminated or truncated
    print(reward)