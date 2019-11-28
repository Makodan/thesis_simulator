import time
from math import floor
import matplotlib.pyplot as plt
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
            self.accuracy = 0.85
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


if __name__ == '__main__':
    sensor_list = list()
    simulation_length = 3600  # sec

    population_step = 10
    population_max = 100 # number
    event_min = 2
    event_max = 120
    color_list = ("red", "green", "grey")
    # ai_mode  0 - centralized AI, 1 - no AI, 2 - edge AI
    label_list = ("CAI", "NoAI", "EAI")
    for ai_v in range(0,3,1):
        consumption_list = list()
        bytes_list = list()
        delay_list = list()
        actual_frequency_list = list()
        actual_power_list = list()
        actual_bandwidth_list = list()
        actual_quality_list = list()
        event_list = list()
    # Test with 1 sensor
        s1 = Sensor(1, ai_v)
        for t in range(0, simulation_length, timestep):
            s1.step()
            actual_power_list.append(s1.actual_power)
            actual_bandwidth_list.append(s1.actual_bandwidth)
            actual_frequency_list.append(s1.actual_frequency)
            actual_quality_list.append(s1.actual_quality)
            consumption_list.append(s1.consumption)
            if t == 800:
                s1.register_event(120)
            if t == 1700:
                s1.register_event(300)
            if (t >= 800 and t < 920) or (1700 <= t < 2000):
                event_list.append(1)
            else:
                event_list.append(0)

        plt.figure('Graphs')
        plt.subplot(611)
        plt.ylabel('Event')
        plt.plot(event_list, color="blue")
        plt.subplot(612)
        plt.ylabel('Power')
        line = plt.plot(actual_power_list, color=color_list[ai_v], label=label_list[ai_v])
        plt.subplot(613)
        plt.ylabel('Consumption')
        plt.plot(consumption_list, color=color_list[ai_v], label=label_list[ai_v])
        plt.subplot(614)
        plt.ylabel('Actual freq')
        plt.plot(actual_frequency_list, color=color_list[ai_v], label=label_list[ai_v])
        plt.subplot(615)
        plt.ylabel('Bandwidth')
        plt.plot(actual_bandwidth_list, color=color_list[ai_v], label=label_list[ai_v])
        plt.subplot(616)
        plt.ylabel('Quality')
        plt.plot(actual_quality_list, color=color_list[ai_v], label=label_list[ai_v])
        plt.legend(loc="upper left")
    plt.show()
    # for ai_v in range(0,3,1):
    #     consumption_list = list()
    #     delay_list = list()
    #     bytes_list = list()
    #     quality_list = list()
    #     actual_power_list = list()
    #     actual_bandwidth_list = list()
    #     population_list = list()
    #     for population in range(10, population_max, population_step):
    #         start = time.time()
    #         population_list.append(population)
    #         # Generate population
    #         sensor_list = list()
    #         for i in range(population):
    #             sensor_list.append(Sensor(i, ai_v))
    # 
    #         # Step trough time
    #         for t in range(0, simulation_length, timestep):
    #             actual_bandwidth = 0
    #             actual_power = 0
    #             # Choose sensors
    #             chosen_ones = random.sample(range(population), int(0.0 * population))
    #             for x in chosen_ones:
    #                 sensor_list[x].register_event(duration=random.randint(event_min, event_max))
    #             for sens in sensor_list:
    #                 sens.step()
    # 
    #         total_consumption = 0
    #         total_bytes = 0
    #         average_quality = 0
    #         average_delay = 0
    #         # TODO worst, best delay? 
    # 
    #         # Summarize
    #         for sens in sensor_list:
    #             total_consumption += sens.consumption
    #             total_bytes += sens.sent_bytes
    #             average_quality += sens.actual_quality
    # 
    #         # Calculate delays
    #         if sensor_list[0].ai_mode == 2:
    #             delay_list.append(sensor_list[0].delay)
    # 
    #         if sensor_list[0].ai_mode == 0:
    #             delay_list.append(sensor_list[0].delay + len(sensor_list) * len(sensor_list) * 0.0407/1000)
    # 
    #         consumption_list.append(total_consumption)
    #         bytes_list.append(total_bytes)
    #         quality_list.append(average_quality/population)
    #         print(
    #             f"Population: {population}, Total consumption: {total_consumption} mWs, total bytes: {total_bytes},"
    #             f" Time elapsed: {round((time.time() - start),1)}")
    # 
    #     plt.figure('Graphs')
    #     plt.subplot(311)
    #     plt.ylabel('Consumption')
    #     plt.plot(population_list, consumption_list,  color=color_list[ai_v], label=label_list[ai_v])
    #     plt.subplot(312)
    #     plt.ylabel('Average quality')
    #     plt.plot(population_list, quality_list, color=color_list[ai_v], label=label_list[ai_v])
    #     # plt.subplot(613)
    #     # plt.ylabel('Power')
    #     # plt.plot(consumption_list, color=color_list[ai_v], label=label_list[ai_v])
    #     # plt.subplot(614)
    #     # plt.ylabel('Delay')
    #     # plt.plot(delay_list, color=color_list[ai_v], label=label_list[ai_v])
    #     # plt.subplot(615)
    #     # plt.ylabel('Bandwidth')
    #     # plt.plot(actual_bandwidth_list, color=color_list[ai_v], label=label_list[ai_v])
    #     plt.subplot(313)
    #     plt.ylabel('Sum bandwidth')
    #     plt.plot(population_list, bytes_list, color=color_list[ai_v], label=label_list[ai_v])
    #     plt.legend(loc="upper left")

    plt.show()
