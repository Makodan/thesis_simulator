import time
from math import floor
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import random
import numpy as np

# Sample based simulator
#

timestep = 1  # s

# Delay due to processing and sending, receiving
noai_delay = (0.428805555555556 + 0.006166666666667 + 10.450 / 1000)
cai_delay = (0.428805555555556 + 0.006166666666667 + 10.450 / 1000)
eai_delay = (0.428805555555556 + 0.1117801683816651) + (10.45 / 1000)
# eai_delay_send = (0.428805555555556 + 0.006166666666667 + 0.1117801683816651) + (10.45 / 1000)
# eai_delay = (30 / 1000) + (111.78 / 1000) + (10.45 / 1000)

# Maximal frequency in the given mode
noai_freq = 2
cai_freq = 2  # Hz
eai_freq = 2

# Size of sent packet
# TODO add received
noai_packet = 772
cai_packet = 772  # byte
eai_packet = 5

# Consumtion/sample = t * U * I= (SAMPLING + PREDICTION + SENDING) * 3.3V * 45mA = [mWs]
# Consumption / sample
noai_cps = (0.428805555555556 + 0.006166666666667) * 5 * 116.73 / 1000  # t * U * I = (kiolvasas + kalkulacio + kuldes)
eai_cps = (0.428805555555556 + 0.1117801683816651) * 5 * 116.73 / 1000
eai_cps_send = (0.428805555555556 + 0.006166666666667 + 0.1117801683816651) * 5 * 116.73 / 1000
cai_cps = (0.428805555555556 + 0.006166666666667) * 5 * 116.73 / 1000  # t * U * I = (kiolvasas + kalkulacio + kuldes)

# Frequencies
noai_fmax = 1
noai_fmin = 1
cai_fmax = 2
cai_fmin = 0.25
eai_fmax = 2
eai_fmin = 0.25


class Sensor():
    def __init__(self, id, ai_mode):
        # AI mode dependant variables
        if ai_mode == 0:
            self.delay = cai_delay
            # self.max_freq = cai_freq
            self.packet_size = cai_packet
            self.cps = cai_cps
            self.accuracy = 1
            self.completeness = 0
            self.fmax = cai_fmax
            self.fmin = cai_fmin
        if ai_mode == 1:
            self.delay = noai_delay
            # self.max_freq = frequency
            self.packet_size = noai_packet
            self.cps = noai_cps
            self.accuracy = 1
            self.completeness = 0
            self.fmax = noai_fmax
            self.fmin = noai_fmin
        if ai_mode == 2:
            self.delay = eai_delay
            # self.max_freq = eai_freq
            self.packet_size = eai_packet
            self.cps = eai_cps
            self.accuracy = 0.7
            self.completeness = 0.5
            self.fmax = eai_fmax
            self.fmin = eai_fmin

        self.id = id
        self.frequency = self.fmin
        self.ai_mode = ai_mode  # 0 - centralized AI, 1 - no AI, 2 - edge AI
        self.neighbours = list()
        self.event = False
        self.delay_handled = False
        self.event_duration = 0
        self.consumption = 0
        self.sent_bytes = 0
        self.samples = 0

        # Per sec variables
        self.actual_frequency = self.frequency
        self.actual_bandwidth = 0
        self.actual_power = 0
        self.actual_quality = 0

    # def calculate_delay(self):
    #     sel

    def step(self):
        # If there is new event process it, calculate with higher freqs,
        #  we have to handle the delay once due to processing
        if self.event:
            # If the event's duration or the remaining duration is shorter than a timestep
            if self.event_duration <= timestep:
                if not self.delay_handled:
                    self.actual_frequency = self.fmax
                    # self.samples += floor((self.event_duration - self.delay) * self.actual_frequency)
                    self.samples += floor((self.event_duration - self.delay) * self.actual_frequency)
                    self.delay_handled = True
                    self.samples += floor((timestep - self.event_duration) * self.actual_frequency)

                else:
                    # Max frequency samples
                    self.samples += floor(self.event_duration * self.actual_frequency)
                    # Base frequency samples
                    self.actual_frequency = self.fmin
                    self.samples += floor((timestep - self.event_duration) * self.actual_frequency)

                self.event = False
                self.delay_handled = False
                self.event_duration = 0

            # If the event's duration is longer then one timestep
            else:
                # The delay has NOT handled already
                if not self.delay_handled:
                    self.actual_frequency = self.fmax
                    self.samples += floor((timestep - self.delay) * self.actual_frequency)
                    # self.event_duration -= self.delay
                    self.event_duration -= timestep
                    self.delay_handled = True
                # The delay has handled already
                else:
                    self.samples += floor(timestep * self.actual_frequency)
                    self.event_duration -= timestep

        # If there is no event, calculate with base freq
        else:
            self.samples += (timestep * self.actual_frequency)

        # Summarize energy, sent bytes based on samples
        # Calculate E, B
        # ...
        # Calculate actual metrics
        # Edge AI needs another method to calculate,if there is event
        self.actual_bandwidth = self.actual_frequency * self.packet_size
        self.actual_power = self.actual_frequency * self.cps
        # self.actual_quality = ((1 - self.delay * self.actual_frequency) + self.accuracy + (
        #         self.actual_frequency / self.fmax) + self.completeness) / 4
        self.actual_quality = (self.accuracy + (
                self.actual_frequency / self.fmax) + self.completeness) / 3
        if self.ai_mode == 2 and self.event:
            self.actual_bandwidth = self.actual_frequency * noai_packet
            self.actual_power = self.actual_frequency * eai_cps_send

        self.sent_bytes += self.samples * self.packet_size
        self.consumption += self.samples * self.cps
        # print(f"ID:{self.id} samples: {self.samples} sent bytes: {self.sent_bytes}")
        self.samples = 0


    def register_event(self, duration):
        if duration <= 0:
            print('Event duration can not be 0 or negative')
            return
        self.event_duration = duration
        self.event = True

    def print_stats(self):
        print(f"ID:{self.id}, sent bytes: {self.sent_bytes}")

    def event_generator(self):
        if random.randint(0, 100) > 95:
            # self.register_event(duration=random.random()*120)
            self.register_event(duration=3)


def surface_plotter(data_matrix_list, ai_type, graph_type):
    hf = plt.figure(graph_type)
    ha = hf.add_subplot(111, projection='3d')
    data_matrix = np.ones((11, 11))
    data_matrix2 = np.zeros((11, 11))
    X, Y = np.meshgrid(range(11), range(11))  # `plot_surface` expects `x` and `y` data to be 2D
    ha.plot_surface(X, Y, data_matrix, color='red', label='ones')
    ha.plot_surface(X, Y, data_matrix2, color='blue', label='ones')
    ha.set_xlabel('X')
    ha.set_ylabel('Y')
    ha.set_zlabel(graph_type)


if __name__ == '__main__':
    sensor_list = list()
    simulation_length = 3600  # sec

    population_step = 100
    population_max = 1100  # number
    population_range = range(1, population_max, population_step)
    print(len(population_range))
    probability_step = 10
    probability_max = 110  # number
    probability_range = range(0, probability_max, probability_step)
    print(len(probability_range))
    event_min = 2
    event_max = 120
    color_list = ("red", "green", "grey")
    # ai_mode  0 - centralized AI, 1 - no AI, 2 - edge AI
    label_list = ("CAI", "NoAI", "EAI")
    data_matrix_list = [
        np.zeros((int(probability_max / probability_step), int(population_max / population_step)), dtype=np.float),
        np.zeros((int(probability_max / probability_step), int(population_max / population_step)), dtype=np.float),
        np.zeros((int(probability_max / probability_step), int(population_max / population_step)), dtype=np.float)]
    print(data_matrix_list[0].shape)
    # exit()
    
    # for ai_v in range(0,3,1):
    #     consumption_list = list()
    #     bytes_list = list()
    #     delay_list = list()
    #     actual_frequency_list = list()
    #     actual_power_list = list()
    #     actual_bandwidth_list = list()
    #     actual_quality_list = list()
    #     event_list = list()
    # # Test with 1 sensor
    #     s1 = Sensor(1, ai_v)
    #     for t in range(0, simulation_length, timestep):
    #         s1.step()
    #         actual_power_list.append(s1.actual_power)
    #         actual_bandwidth_list.append(s1.actual_bandwidth)
    #         actual_frequency_list.append(s1.actual_frequency)
    #         actual_quality_list.append(s1.actual_quality*100)
    #         consumption_list.append(s1.consumption)
    #         if t == 800:
    #             s1.register_event(120)
    #         if t == 1700:
    #             s1.register_event(700)
    #         if (t >= 800 and t < 920) or (1700 <= t < 2400):
    #             event_list.append(1)
    #         else:
    #             event_list.append(0)
    # 
    #     plt.figure('Graphs')
    #     plt.subplot(611)
    #     plt.ylabel('Event')
    #     plt.plot(event_list, color="blue")
    #     plt.subplot(612)
    #     plt.ylabel('Power[mW]')
    #     line = plt.plot(actual_power_list, color=color_list[ai_v], label=label_list[ai_v])
    #     plt.subplot(613)
    #     plt.ylabel('Consumption[mWs]')
    #     plt.plot(consumption_list, color=color_list[ai_v], label=label_list[ai_v])
    #     plt.subplot(614)
    #     plt.ylabel('Actual freq[Hz]')
    #     plt.plot(actual_frequency_list, color=color_list[ai_v], label=label_list[ai_v])
    #     plt.subplot(615)
    #     plt.ylabel('Bandwidth[B/s]')
    #     plt.plot(actual_bandwidth_list, color=color_list[ai_v], label=label_list[ai_v])
    #     plt.subplot(616)
    #     plt.ylabel('Quality[%]')
    #     plt.plot(actual_quality_list, color=color_list[ai_v], label=label_list[ai_v])
    #     plt.legend(loc="upper left")
    # plt.show()

    for ai_v in range(0, 3, 1):
        # consumption_list = list()
        # delay_list = list()
        # bytes_list = list()
        # quality_list = list()
        # actual_power_list = list()
        # actual_bandwidth_list = list()
        # population_list = list()

        # for probability in range(0, probability_max, probability_step):
        for probability in probability_range:
            consumption_list = list()
            delay_list = list()
            bytes_list = list()
            quality_list = list()
            actual_power_list = list()
            actual_bandwidth_list = list()
            population_list = list()
            # for population in range(10, population_max, population_step):
            for population in population_range:
                start = time.time()
                population_list.append(population)
                # Generate population
                sensor_list = list()
                for i in range(population):
                    sensor_list.append(Sensor(i, ai_v))

                # Step trough time
                for t in range(0, simulation_length, timestep):
                    actual_bandwidth = 0
                    actual_power = 0
                    # Choose sensors
                    chosen_ones = random.sample(range(population), int(probability / 100 * population))
                    for x in chosen_ones:
                        sensor_list[x].register_event(duration=random.randint(event_min, event_max))
                    for sens in sensor_list:
                        sens.step()

                total_consumption = 0
                total_bytes = 0
                average_quality = 0
                average_delay = 0
                average_bandwidth = 0
                # TODO worst, best delay?

                # Summarize
                for sens in sensor_list:
                    total_consumption += sens.consumption
                    total_bytes += sens.sent_bytes
                    average_quality += sens.actual_quality
                    average_bandwidth += sens.actual_bandwidth

                # Calculate delays
                if sensor_list[0].ai_mode == 2:
                    delay_list.append(sensor_list[0].delay)

                if sensor_list[0].ai_mode == 0:
                    delay_list.append(sensor_list[0].delay + len(sensor_list) * len(sensor_list) * 0.0407 / 1000)

                consumption_list.append(total_consumption / (1000))
                bytes_list.append(total_bytes)
                quality_list.append((average_quality / population) * 100)
                actual_bandwidth_list.append(average_bandwidth / population)
                print(
                    f"Probability: {probability} Population: {population}, Total consumption: {total_consumption} mWs, total bytes: {total_bytes},"
                    f" Time elapsed: {round((time.time() - start), 1)}")
                data_matrix_list[ai_v][int(population / population_step), int(probability / probability_step)] = (average_quality / population) * 100

                print(int(population / 10), int(probability / 10))
        # hf = plt.figure('consumptions')
        # ha = hf.add_subplot(111, projection='3d')
        # X, Y = np.meshgrid(population_range, probability_range)  # `plot_surface` expects `x` and `y` data to be 2D
        # ha.plot_surface(X, Y, data_matrix_list[ai_v], color=color_list[ai_v], label=label_list[ai_v])
        # ha.set_xlabel('population')
        # ha.set_ylabel('probability')
        # ha.set_zlabel()

        plt.figure('Graphs')
        plt.subplot(411)
        plt.ylabel('Consumption[Ws]')
        plt.plot(population_list, consumption_list,  color=color_list[ai_v], label=label_list[ai_v])
        plt.subplot(412)
        plt.ylabel('Average quality[%]')
        plt.plot(population_list, quality_list, color=color_list[ai_v], label=label_list[ai_v])
        plt.subplot(413)
        plt.ylabel('Average bandwidth[B/s]')
        plt.plot(population_list, actual_bandwidth_list, color=color_list[ai_v], label=label_list[ai_v])
        # plt.subplot(614)
        # plt.ylabel('Delay')
        # plt.plot(delay_list, color=color_list[ai_v], label=label_list[ai_v])
        # plt.subplot(615)
        # plt.ylabel('Bandwidth')
        # plt.plot(actual_bandwidth_list, color=color_list[ai_v], label=label_list[ai_v])
        plt.subplot(414)
        plt.ylabel('Sum bandwidth[B]')
        plt.plot(population_list, bytes_list, color=color_list[ai_v], label=label_list[ai_v])
        plt.legend(loc="upper left")
    hf = plt.figure('consumptions0')
    ha = hf.add_subplot(111, projection='3d')
    X, Y = np.meshgrid(population_range, probability_range)  # `plot_surface` expects `x` and `y` data to be 2D
    ha.plot_surface(X, Y, data_matrix_list[0], color=color_list[0], label=label_list[0])
    ha.plot_surface(X, Y, data_matrix_list[1], color=color_list[1], label=label_list[1])
    ha.plot_surface(X, Y, data_matrix_list[2], color=color_list[2], label=label_list[2])
    ha.set_xlabel('population')
    ha.set_ylabel('probability')

    plt.show()
