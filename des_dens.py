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
# noai_freq = 2
# cai_freq = 2  # Hz
# eai_freq = 2

# Size of sent packet
# TODO add received
noai_packet = 772
cai_packet = 772  # byte
eai_packet = 4

# Consumtion/sample = t * U * I= (SAMPLING + PREDICTION + SENDING) * 3.3V * 45mA = [mWs]
# Consumption / sample
noai_cps = (0.428805555555556 + 0.006166666666667) * 5 * 116.73 / 1000  # t * U * I = (kiolvasas + kalkulacio + kuldes)
eai_cps = (0.428805555555556 + 0.1117801683816651) * 5 * 116.73 / 1000
eai_cps_send = (0.428805555555556 + 0.006166666666667 + 0.1117801683816651) * 5 * 116.73 / 1000
cai_cps = (0.428805555555556 + 0.006166666666667) * 5 * 116.73 / 1000  # t * U * I = (kiolvasas + kalkulacio + kuldes)

# Frequencies
noai_fmax = 1
noai_fmin = 1
cai_fmax = 2.25
cai_fmin = 0.2
eai_fmax = 1.9
eai_fmin = 0.2

poz_FLOPS = 89184
cai_FLOPS = 2615


class Sensor():
    def __init__(self, id, ai_mode):
        # AI mode dependant variables
        if ai_mode == 0:
            self.delay = cai_delay
            self.packet_size = cai_packet
            self.cps = cai_cps
            self.accuracy = 1
            self.completeness = 0
            self.fmax = cai_fmax
            self.fmin = cai_fmin
        if ai_mode == 1:
            # self.delay = noai_delay
            self.delay = 0
            self.packet_size = noai_packet
            self.cps = noai_cps
            self.accuracy = 1
            self.completeness = 0
            self.fmax = noai_fmax
            self.fmin = noai_fmin
        if ai_mode == 2:
            self.delay = eai_delay
            self.packet_size = eai_packet
            self.cps = eai_cps
            self.accuracy = 0.71
            self.completeness = 1
            self.fmax = eai_fmax
            self.fmin = eai_fmin

        self.id = id
        self.frequency = self.fmin
        self.ai_mode = ai_mode  # 0 - centralized AI, 1 - no AI, 2 - edge AI
        self.event = False
        self.delay_handled = False
        self.event_duration = 0
        self.consumption = 0
        self.sent_bytes = 0
        self.samples = 0
        self.sum_steps = 0
        self.sum_quality = 0
        self.sum_flops = 0

        # Per sec variables
        self.actual_frequency = self.frequency
        self.actual_bandwidth = 0
        self.actual_power = 0
        self.actual_quality = 0
        self.actual_FLOPS = 0

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
                    self.samples += ((self.event_duration - self.delay) * self.actual_frequency)
                    self.delay_handled = True
                    self.samples += ((timestep - self.event_duration) * self.actual_frequency)

                else:
                    # Max frequency samples
                    self.samples += (self.event_duration * self.actual_frequency)
                    # Base frequency samples
                    self.actual_frequency = self.fmin
                    self.samples += ((timestep - self.event_duration) * self.actual_frequency)

                self.event = False
                self.delay_handled = False
                self.event_duration = 0

            # If the event's duration is longer then one timestep
            else:
                # The delay has NOT handled already
                if not self.delay_handled:
                    self.actual_frequency = self.fmax
                    self.samples += ((timestep - self.delay) * self.actual_frequency)
                    # self.event_duration -= self.delay
                    self.event_duration -= timestep
                    self.delay_handled = True
                # The delay has handled already
                else:
                    self.samples += (timestep * self.actual_frequency)
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
        self.actual_quality = (self.accuracy + (
                self.actual_frequency / 2.33) + self.completeness) / 3
        if self.ai_mode == 2 and self.event:
            self.actual_bandwidth = self.actual_frequency * noai_packet
            self.actual_power = self.actual_frequency * eai_cps_send

        # FLOPS calculation
        # Depends on AI mode 
        if self.ai_mode == 0:  # CAI
            if self.event:
                self.actual_FLOPS = (poz_FLOPS + cai_FLOPS) * self.samples
            else:
                self.actual_FLOPS = cai_FLOPS * self.samples

        if self.ai_mode == 1:  # NoAI
            self.actual_FLOPS = poz_FLOPS * self.samples

        if self.ai_mode == 2:  # EAI
            if self.event:
                self.actual_FLOPS = poz_FLOPS * self.samples
            else:
                self.actual_FLOPS = 0

        #
        # Sent bytes calculation
        if self.ai_mode == 2 and self.event:
            self.sent_bytes += self.samples * noai_packet
        else:
            self.sent_bytes += self.samples * self.packet_size

        # Consumption calculation
        # If EAI and there is event
        if self.ai_mode == 2 and self.event:
            self.consumption += self.samples * eai_cps_send
        else:
            self.consumption += self.samples * self.cps

        self.sum_steps += 1
        self.sum_quality += self.actual_quality
        self.sum_flops += self.actual_FLOPS
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

    def calculate_average_quality(self):
        return self.sum_quality / self.sum_steps


def surface_plotter(consumption_matrix_list, ai_type, graph_type):
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
    simulation_length = 600  # sec

    population_start = 1000
    population_step = 1000
    population_max = 12000  # number
    population_range = range(population_start, population_max, population_step)
    print(len(population_range))
    probability_start = 0
    probability_step = 10
    probability_max = 110  # number
    probability_range = range(probability_start, probability_max, probability_step)
    print(len(probability_range))
    event_min = 1
    event_max = 6
    event_mean = 5
    event_std = 1
    color_list = ("red", "green", "grey")
    # ai_mode  0 - centralized AI, 1 - no AI, 2 - edge AI
    label_list = ("CAI", "NoAI", "EAI")

    font = {'family': 'normal',
            'weight': 'normal',
            'size': 16}

    plt.rc('font', **font)

    consumption_matrix_list = [
        np.zeros((len(probability_range), len(population_range)), dtype=np.float),
        np.zeros((len(probability_range), len(population_range)), dtype=np.float),
        np.zeros((len(probability_range), len(population_range)), dtype=np.float)]
    print(consumption_matrix_list[0].shape)

    sumflops_matrix_list = [
        np.zeros((len(probability_range), len(population_range)), dtype=np.float),
        np.zeros((len(probability_range), len(population_range)), dtype=np.float),
        np.zeros((len(probability_range), len(population_range)), dtype=np.float)]

    average_bandwidth_matrix_list = [
        np.zeros((len(probability_range), len(population_range)), dtype=np.float),
        np.zeros((len(probability_range), len(population_range)), dtype=np.float),
        np.zeros((len(probability_range), len(population_range)), dtype=np.float)]

    bytes_matrix_list = [
        np.zeros((len(probability_range), len(population_range)), dtype=np.float),
        np.zeros((len(probability_range), len(population_range)), dtype=np.float),
        np.zeros((len(probability_range), len(population_range)), dtype=np.float)]

    average_quality_matrix_list = [
        np.zeros((len(probability_range), len(population_range)), dtype=np.float),
        np.zeros((len(probability_range), len(population_range)), dtype=np.float),
        np.zeros((len(probability_range), len(population_range)), dtype=np.float)]

    # for ai_v in range(0, 3, 1):
    #     consumption_list = list()
    #     bytes_list = list()
    #     delay_list = list()
    #     actual_frequency_list = list()
    #     actual_power_list = list()
    #     actual_bandwidth_list = list()
    #     actual_quality_list = list()
    #     actual_FLOPS_list = list()
    #     event_list = list()
    #     # Test with 1 sensor
    #     s1 = Sensor(1, ai_v)
    #     for t in range(0, simulation_length, timestep):
    #         s1.step()
    #         actual_power_list.append(s1.actual_power)
    #         actual_bandwidth_list.append(s1.actual_bandwidth)
    #         actual_frequency_list.append(s1.actual_frequency)
    #         actual_quality_list.append(s1.actual_quality * 100)
    #         actual_FLOPS_list.append(s1.actual_FLOPS)
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
    #     plt.figure('Graphs', figsize=(15, 15))
    #     a1 = plt.subplot(711)
    #     a1.set_xticklabels([])
    #     plt.ylabel('Event')
    #     plt.plot(event_list, color="blue")
    #     a2 = plt.subplot(712)
    #     a2.set_xticklabels([])
    #     plt.ylabel('Power\n[W]')
    #     line = plt.plot(actual_power_list, color=color_list[ai_v], label=label_list[ai_v])
    #     plt.legend(loc="upper left")
    #     a3 = plt.subplot(713)
    #     a3.set_xticklabels([])
    #     plt.ylabel('Consumption\n[mWs]')
    #     plt.plot(consumption_list, color=color_list[ai_v], label=label_list[ai_v])
    #     a4 = plt.subplot(714)
    #     a4.set_xticklabels([])
    #     plt.ylabel('Frequency\n[Hz]')
    #     plt.plot(actual_frequency_list, color=color_list[ai_v], label=label_list[ai_v])
    #     a5 = plt.subplot(715)
    #     a5.set_xticklabels([])
    #     plt.ylabel('Bandwidth\n[B/s]')
    #     plt.plot(actual_bandwidth_list, color=color_list[ai_v], label=label_list[ai_v])
    #     a6 = plt.subplot(716)
    #     a6.set_xticklabels([])
    #     plt.ylabel('Quality\n[%]')
    #     plt.plot(actual_quality_list, color=color_list[ai_v], label=label_list[ai_v])
    #     a7 = plt.subplot(717)
    #     a7.get_shared_x_axes().join(a1, a2, a3, a4, a5, a6)
    #     plt.ylabel('FLOP')
    #     plt.plot(actual_FLOPS_list, color=color_list[ai_v], label=label_list[ai_v])
    #     plt.xlabel('Time [s]')
    #
    # plt.show()
    # plt.savefig("Graphs.png", bbox_inches='tight')
    # exit()

    for ai_v in range(0, 3, 1):
        print(f"{label_list[ai_v]} simulation started")
        consumption_list = list()
        delay_list = list()
        bytes_list = list()
        quality_list = list()
        actual_power_list = list()
        actual_bandwidth_list = list()
        population_list = list()
        sum_FLOPS_list = list()

        for probability in probability_range:
            consumption_list = list()
            delay_list = list()
            bytes_list = list()
            quality_list = list()
            actual_power_list = list()
            actual_bandwidth_list = list()
            population_list = list()

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
                    has_event = 0
                    no_event = 0
                    # Choose sensors
                    if t % 2:
                        chosen_ones = random.sample(range(population), int(probability / 100 * population))
                        for x in chosen_ones:
                            # sensor_list[x].register_event(duration=random.randint(event_min, event_max))
                            sensor_list[x].register_event(duration=3)
                    for sens in sensor_list:
                        if sens.event:
                            has_event += 1
                        else:
                            no_event += 1
                    for sens in sensor_list:
                        sens.step()
                    # if probability > 90:
                    #     print(f"Probability: {probability}, Event percentage: {(has_event / (has_event + no_event)) * 100}")

                total_consumption = 0
                total_bytes = 0
                average_quality = 0
                average_delay = 0
                average_bandwidth = 0
                sum_flops = 0
                # TODO worst, best delay?

                # Summarize
                for sens in sensor_list:
                    total_consumption += sens.consumption
                    total_bytes += sens.sent_bytes
                    average_quality += sens.calculate_average_quality()
                    average_bandwidth += sens.actual_bandwidth
                    sum_flops += sens.sum_flops

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
                consumption_matrix_list[ai_v][int((population - population_start) / population_step),
                                              int((
                                                          probability - probability_start) / probability_step)] = total_consumption/3600
                sumflops_matrix_list[ai_v][int((population - population_start) / population_step),
                                           int((probability - probability_start) / probability_step)] = sum_flops
                average_bandwidth_matrix_list[ai_v][int((population - population_start) / population_step),
                                                    int((
                                                                probability - probability_start) / probability_step)] = average_bandwidth
                bytes_matrix_list[ai_v][int((population - population_start) / population_step),
                                        int((probability - probability_start) / probability_step)] = total_bytes
                average_quality_matrix_list[ai_v][int((population - population_start) / population_step),
                                                  int((probability - probability_start) / probability_step)] = (
                                                                                                                       average_quality / population) * 100

                print(int((population - population_start) / population_step),
                      int((probability - probability_start) / probability_step))

        # plt.figure('Graphs')
        # plt.subplot(411)
        # plt.ylabel('Consumption[Ws]')
        # plt.plot(population_list, consumption_list,  color=color_list[ai_v], label=label_list[ai_v])
        # plt.subplot(412)
        # plt.ylabel('Average quality[%]')
        # plt.plot(population_list, quality_list, color=color_list[ai_v], label=label_list[ai_v])
        # plt.subplot(413)
        # plt.ylabel('Average bandwidth[B/s]')
        # plt.plot(population_list, actual_bandwidth_list, color=color_list[ai_v], label=label_list[ai_v])
        # plt.subplot(614)
        # plt.ylabel('Delay')
        # plt.plot(delay_list, color=color_list[ai_v], label=label_list[ai_v])
        # plt.subplot(615)
        # plt.ylabel('Bandwidth')
        # plt.plot(actual_bandwidth_list, color=color_list[ai_v], label=label_list[ai_v])
        # plt.subplot(414)
        # plt.ylabel('Sum bandwidth[B]')
        # plt.plot(population_list, bytes_list, color=color_list[ai_v], label=label_list[ai_v])
        # plt.legend(loc="upper left")
    for ai_v in range(0, 3, 1):
        np.savetxt(label_list[ai_v] + '_ ' + "consumption_matrix_list", consumption_matrix_list[ai_v], fmt='%f')
        np.savetxt(label_list[ai_v] + '_ ' + "sumflops_matrix_list", sumflops_matrix_list[ai_v], fmt='%f')
        np.savetxt(label_list[ai_v] + '_ ' + "average_bandwidth_matrix_list", average_bandwidth_matrix_list[ai_v],
                   fmt='%f')
        np.savetxt(label_list[ai_v] + '_ ' + "bytes_matrix_list", bytes_matrix_list[ai_v], fmt='%f')
        np.savetxt(label_list[ai_v] + '_ ' + "average_quality_matrix_list", average_quality_matrix_list[ai_v], fmt='%f')
    hf = plt.figure('Consumption', figsize=(20, 15))
    ha = hf.add_subplot(111, projection='3d')
    Y, X = np.meshgrid(probability_range, population_range)  # `plot_surface` expects `x` and `y` data to be 2D
    ha.plot_surface(X, Y, consumption_matrix_list[0], color=color_list[0], label=label_list[0])
    ha.plot_surface(X, Y, consumption_matrix_list[1], color=color_list[1], label=label_list[1])
    ha.plot_surface(X, Y, consumption_matrix_list[2], color=color_list[2], label=label_list[2])
    ha.set_xlabel('\nPopulation')
    ha.set_ylabel('\nAffected by event [%]')
    ha.set_zlabel('\n\n\nConsumption [Ws]')
    plt.savefig("consumption.png", bbox_inches='tight')

    hf = plt.figure('Summarized FLOPs', figsize=(20, 15))
    ha = hf.add_subplot(111, projection='3d')
    ha.plot_surface(X, Y, sumflops_matrix_list[0], color=color_list[0], label=label_list[0])
    ha.plot_surface(X, Y, sumflops_matrix_list[1], color=color_list[1], label=label_list[1])
    ha.plot_surface(X, Y, sumflops_matrix_list[2], color=color_list[2], label=label_list[2])
    ha.set_xlabel('\nPopulation')
    ha.set_ylabel('\nAffected by event [%]')
    ha.set_zlabel('\n\n\nFLOP number')
    plt.savefig('sumflops.png', bbox_inches='tight')

    hf = plt.figure('Bandwidth', figsize=(20, 15))
    ha = hf.add_subplot(111, projection='3d')
    ha.plot_surface(X, Y, average_bandwidth_matrix_list[0], color=color_list[0], label=label_list[0])
    ha.plot_surface(X, Y, average_bandwidth_matrix_list[1], color=color_list[1], label=label_list[1])
    ha.plot_surface(X, Y, average_bandwidth_matrix_list[2], color=color_list[2], label=label_list[2])
    ha.set_xlabel('\nPopulation')
    ha.set_ylabel('\nAffected by event [%]')
    ha.set_zlabel('\n\n\nBandwidth [B/s]')
    plt.savefig('Bandwidth.png', bbox_inches='tight')

    hf = plt.figure('Sent bytes', figsize=(20, 15))
    ha = hf.add_subplot(111, projection='3d')
    ha.plot_surface(X, Y, bytes_matrix_list[0], color=color_list[0], label=label_list[0])
    ha.plot_surface(X, Y, bytes_matrix_list[1], color=color_list[1], label=label_list[1])
    ha.plot_surface(X, Y, bytes_matrix_list[2], color=color_list[2], label=label_list[2])
    ha.set_xlabel('\nPopulation')
    ha.set_ylabel('\nAffected by event [%]')
    ha.set_zlabel('\n\n\nBytes sent [B]')
    plt.savefig('sentbytes.png', bbox_inches='tight')

    hf = plt.figure('Average quality', figsize=(20, 15))
    ha = hf.add_subplot(111, projection='3d')
    ha.plot_surface(X, Y, average_quality_matrix_list[0], color=color_list[0], label=label_list[0])
    ha.plot_surface(X, Y, average_quality_matrix_list[1], color=color_list[1], label=label_list[1])
    ha.plot_surface(X, Y, average_quality_matrix_list[2], color=color_list[2], label=label_list[2])
    ha.set_xlabel('\nPopulation')
    ha.set_ylabel('\nAffected by event [%]')
    ha.set_zlabel('\n\n\nQuality [%]')
    plt.savefig('quality.png', bbox_inches='tight')

    plt.show()
#     for ai_v in range(0, 3, 1):
#         print(f"{label_list[ai_v]} simulation started")
#         probability = 100
#         consumption_list = list()
#         delay_list = list()
#         bytes_list = list()
#         quality_list = list()
#         actual_power_list = list()
#         actual_bandwidth_list = list()
#         population_list = list()
#         actual_FLOPS_list = list()
#         sum_FLOPS_list = list()
#         for population in population_range:
#             start = time.time()
#             population_list.append(population)
#             # Generate population
#             sensor_list = list()
#             for i in range(population):
#                 sensor_list.append(Sensor(i, ai_v))
#
#             # Step trough time
#             for t in range(0, simulation_length, timestep):
#                 # Choose sensors
#                 if t % 2:
#                     chosen_ones = random.sample(range(population), int(probability / 100 * population))
#                     for x in chosen_ones:
#                         # sensor_list[x].register_event(duration=random.randint(event_min, event_max))
#                         sensor_list[x].register_event(duration=20)
#                 # chosen_ones = random.sample(range(population), int(probability / 100 * population))
#                 # for x in chosen_ones:
#                 #     sensor_list[x].register_event(duration=random.randint(event_min, event_max))
#                 for sens in sensor_list:
#                     sens.step()
#
#             total_consumption = 0
#             total_bytes = 0
#             average_quality = 0
#             average_delay = 0
#             average_bandwidth = 0
#             average_FLOPS = 0
#             max_FLOPS = 0
#             # TODO worst, best delay?
#
#             # Summarize
#             for sens in sensor_list:
#                 total_consumption += sens.consumption
#                 total_bytes += sens.sent_bytes
#                 average_quality += sens.calculate_average_quality()
#                 average_bandwidth += sens.actual_bandwidth
#                 average_FLOPS += sens.sum_flops
#
#             # Calculate delays
#             if sensor_list[0].ai_mode == 2:
#                 delay_list.append(sensor_list[0].delay)
#
#             if sensor_list[0].ai_mode == 0:
#                 delay_list.append(sensor_list[0].delay + len(sensor_list) * len(sensor_list) * 0.0407 / 1000)
#
#             consumption_list.append(total_consumption / (1000))
#             bytes_list.append(total_bytes)
#             quality_list.append((average_quality / population) * 100)
#             actual_bandwidth_list.append(average_bandwidth / population)
#             actual_FLOPS_list.append(average_FLOPS / population)
#             sum_FLOPS_list.append(average_FLOPS
#                                   )
#             print(
#                 f"Probability: {probability} Population: {population}, Total consumption: {total_consumption} mWs, total bytes: {total_bytes},"
#                 f" Time elapsed: {round((time.time() - start), 1)}")
#
#         plt.figure('Graphs')
#         plt.subplot(611)
#         plt.ylabel('Consumption[Ws]')
#         plt.plot(population_list, consumption_list, color=color_list[ai_v], label=label_list[ai_v])
#         plt.subplot(612)
#         plt.ylabel('Average quality[%]')
#         plt.plot(population_list, quality_list, color=color_list[ai_v], label=label_list[ai_v])
#         plt.subplot(613)
#         plt.ylabel('Average bandwidth[B/s]')
#         plt.plot(population_list, actual_bandwidth_list, color=color_list[ai_v], label=label_list[ai_v])
#         # plt.subplot(614)
#         # plt.ylabel('Delay')
#         # plt.plot(delay_list, color=color_list[ai_v], label=label_list[ai_v])
#         # plt.subplot(615)
#         # plt.ylabel('Bandwidth')
#         # plt.plot(actual_bandwidth_list, color=color_list[ai_v], label=label_list[ai_v])
#         plt.subplot(614)
#         plt.ylabel('Sum bytes[B]')
#         plt.plot(population_list, bytes_list, color=color_list[ai_v], label=label_list[ai_v])
#         plt.subplot(615)
#         plt.ylabel('Average FLOPs')
#         plt.plot(population_list, actual_FLOPS_list, color=color_list[ai_v], label=label_list[ai_v])
#         plt.subplot(616)
#         plt.ylabel('Sum FLOPs')
#         plt.plot(population_list, sum_FLOPS_list, color=color_list[ai_v], label=label_list[ai_v])
#         plt.legend(loc="upper left")
# plt.show()
