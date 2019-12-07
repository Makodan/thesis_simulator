import numpy as np
from matplotlib import pyplot as plt
import random

plt.ion()
# numpy [y,x] format
world = None


def generate_start():
    ranbol = random.choice((True, False))

    if ranbol:
        start_y = random.randint(0, world.shape[0]-1)
        print(f"Start y: {start_y}")
        if start_y == 0 or start_y == world.shape[0]-1:
            start_x = random.randint(0, world.shape[1] - 1)
            print(f"Start x: {start_x}")
        else:
            start_x = random.choice((0, world.shape[1] - 1))
            print(f"Start x: {start_x}")

    else:
        start_x = random.randint(0, world.shape[1]-1)
        print(f"Start x: {start_x}")
        if start_x == 0 or start_x == world.shape[1]-1:
            start_y = random.randint(0, world.shape[0] - 1)
            print(f"Start y: {start_y}")
        else:
            start_y = random.choice((0, world.shape[0] - 1))
            print(f"Start y: {start_y}")

    return start_y, start_x


def next_step(current_y, current_x):
    # Cant step back
    sub_mx = world[current_y-1:current_y+2, current_x-1:current_x+2]
    result = np.where(sub_mx == False)
    # print(sub_mx)
    # print(sub_mx.shape)

    if not (sub_mx.shape[0] == 0 or sub_mx.shape[1] == 0):
        if (len(result[0])) == 0:
            start_y, start_x = init()
            current_y = start_y
            current_x = start_x

    n_y = current_y + random.choice((-1, 0, 1))
    n_x = current_x + random.choice((-1, 0, 1))
    i = 0
    while not empty_coordinate(n_y, n_x):
        if i > 20:
            start_y, start_x = init()
            current_y = start_y
            current_x = start_x
        n_y = current_y + random.choice((-1, 0, 1))
        n_x = current_x + random.choice((-1, 0, 1))
        i += 1

    print(n_y, n_x, n_y * world.shape[0] + n_x)
    world[n_y, n_x] = True
    return n_y, n_x


def valid_coordinate(y,x):
    if x > world.shape[1]-1 or x < 0:
        return False
    if y > world.shape[0]-1 or y < 0:
        return False
    return True


def empty_coordinate(y,x):
    if valid_coordinate(y, x):
        if not world[y, x]:
            return True
        else:
            return False
    else:
        return False

def init():
    global world
    world = np.zeros((100, 100), dtype=np.bool)
    start_y, start_x = generate_start()
    world[start_y, start_x] = True
    return  start_y, start_x

def main():
    start_y_1, start_x_1 = init()
    # start_y_2, start_x_2 = init()
    next_y_1 = start_y_1
    # next_y_2 = start_y_2
    next_x_1 = start_x_1
    # next_x_2 = start_x_2
    while True:
        # world = np.zeros((100, 100), dtype=np.bool)
        next_y_1, next_x_1 = next_step(next_y_1, next_x_1)
        # next_y_2, next_x = next_step(next_y_2, next_x_2)
        plt.figure('start pos')
        plt.clf()
        plt.imshow(world)
        plt.show()
        plt.pause(0.0001)


if __name__ == '__main__':
    main()

