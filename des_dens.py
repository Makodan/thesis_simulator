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
eai_delay = (30 / 1000) + (111.78 / 1000) + (10.45 / 1000)

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
    def __init__(self, id, frequency, ai_mode):
        self.id = id
        self.frequency = frequency
        self.ai_mode = ai_mode  # 0 - centralized AI, 1 - no AI, 2 - edge AI
        self.neighbours = list()
        self.event = False
        self.delay_handled = False
        self.event_duration = 0
        self.consumption = 0
        self.sent_bytes = 0
        self.samples = 0

        # Per sec variables
        self.actual_frequency = frequency
        self.base_frequency = frequency
        self.actual_bandwidth = 0
        self.actual_power = 0
        self.actual_quality = 0

        # AI mode dependant variables
        if ai_mode == 0:
            self.delay = cai_delay
            self.max_freq = cai_freq
            self.packet_size = cai_packet
            self.cps = cai_cps
            self.accuracy = 0.85
            self.completeness = 0.5
            self.fmax = cai_fmax
            self.fmin = cai_fmin
        if ai_mode == 1:
            self.delay = noai_delay
            self.max_freq = frequency
            self.packet_size = noai_packet
            self.cps = noai_cps
            self.accuracy = 1
            self.completeness = 0
            self.fmax = noai_fmax
            self.fmin = noai_fmin
        if ai_mode == 2:
            self.delay = eai_delay
            self.max_freq = eai_freq
            self.packet_size = eai_packet
            self.cps = eai_cps
            self.accuracy = 0.6
            self.completeness = 0.5
            self.fmax = eai_fmax
            self.fmin = eai_fmin

    def step(self):
        # If there is new event process it, calculate with higher freqs,
        #  we have to handle the delay once due to processing
        if self.event:
            # If the event's duration or the remaining duration is shorter than a timestep
            if self.event_duration <= timestep:
                if not self.delay_handled:
                    self.actual_frequency = self.max_freq
                    self.samples += floor((self.event_duration - self.delay) * self.max_freq)
                    self.delay_handled = True
                    self.samples += floor((timestep - self.event_duration) * self.frequency)

                else:
                    # Max frequency samples
                    self.samples += floor(self.event_duration * self.max_freq)
                    # Base frequency samples
                    self.samples += floor((timestep - self.event_duration) * self.frequency)
                    self.actual_frequency = self.frequency

                self.event = False
                self.delay_handled = False
                self.event_duration = 0

            # If the event's duration is longer then one timestep
            else:
                # The delay has NOT handled already
                if not self.delay_handled:
                    self.actual_frequency = self.max_freq
                    self.samples += floor((timestep - self.delay) * self.max_freq)
                    # self.event_duration -= self.delay
                    self.event_duration -= timestep
                    self.delay_handled = True
                # The delay has handled already
                else:
                    self.samples += floor(timestep * self.max_freq)
                    self.event_duration -= timestep

        # If there is no event, calculate with base freq
        else:
            self.samples += (timestep * self.frequency)

        # Summarize energy, sent bytes based on samples
        # Calculate E, B
        # ...
        # Calculate actual metrics
        # Edge AI needs another method to calculate,if there is event
        self.actual_bandwidth = self.actual_frequency * self.packet_size
        if self.ai_mode == 2 and self.event:
            self.actual_bandwidth = self.actual_frequency * noai_packet
        self.actual_power = self.actual_frequency * self.cps
        self.actual_quality = ((1-self.delay*self.actual_frequency) + self.accuracy + (
                    self.actual_frequency / self.max_freq) + self.completeness) / 4
        print(self.actual_quality)
        self.sent_bytes += self.samples * self.packet_size
        self.consumption += self.samples * self.cps
        print(f"ID:{self.id} samples: {self.samples} sent bytes: {self.sent_bytes}")
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
    simulation_length = 1100  # sec

    population_step = 1000
    population_max = 10000  # number
    event_min = 2
    event_max = 120
    ai = 2
    freq =0.25
    for ai_v in range(1,2,1):
        consumption_list = list()
        bytes_list = list()
        delay_list = list()
        actual_frequency_list = list()
        actual_power_list = list()
        actual_bandwidth_list = list()
        actual_quality_list = list()
        event_list = list()
    # Test with 1 sensor
        s1 = Sensor(1, freq, ai_v)
        for t in range(0, simulation_length, timestep):
            s1.step()
            actual_power_list.append(s1.actual_power)
            actual_bandwidth_list.append(s1.actual_bandwidth)
            actual_frequency_list.append(s1.actual_frequency)
            actual_quality_list.append(s1.actual_quality)
            consumption_list.append(s1.consumption)
            if t == 1000:
                s1.register_event(100)
            # s1.event_generator()
            if t >= 1000 and t < 1100:
                event_list.append(1)
            else:
                event_list.append(0)

        plt.figure('Event')
        plt.plot(event_list)
        plt.figure('Power')
        plt.plot(actual_power_list)
        plt.figure('Consumption')
        plt.plot(consumption_list)
        plt.figure('Frequency')
        plt.plot(actual_frequency_list)
        plt.figure('Bandwith')
        plt.plot(actual_bandwidth_list)
        plt.figure('Quality')
        plt.plot(actual_quality_list)
    plt.show()

    # for population in range(1, population_max, population_step):
    #     start = time.time()
    #     # Generate population
    #     sensor_list = list()
    #     for i in range(population):
    #         sensor_list.append(Sensor(i, freq, ai))
    #
    #     # Step trough time
    #     for t in range(0, simulation_length, timestep):
    #         actual_bandwidth = 0
    #         actual_power = 0
    #         # Choose sensors
    #         # chosen_ones = np.random.normal(population * 0.5, population * 0.05, random.randint(0, int(population/2))).astype(np.int)
    #         chosen_ones = random.sample(range(population), int(0.2 * population))
    #         for x in chosen_ones:
    #             sensor_list[x].register_event(duration=random.randint(event_min, event_max))
    #         for sens in sensor_list:
    #             sens.step()
    #             actual_bandwidth += sens.actual_bandwidth
    #             actual_power += sens.actual_power
    #         actual_bandwidth_list.append(actual_bandwidth)
    #         actual_power_list.append(actual_power)
    #
    #     total_consumption = 0
    #     total_bytes = 0
    #
    #     # Summarize
    #     for sens in sensor_list:
    #         total_consumption += sens.consumption
    #         total_bytes += sens.sent_bytes
    #
    #     # Calculate delays
    #     if sensor_list[0].ai_mode == 2:
    #         delay_list.append(sensor_list[0].delay)
    #
    #     if sensor_list[0].ai_mode == 0:
    #         delay_list.append(sensor_list[0].delay + len(sensor_list) * len(sensor_list) * 0.0407/1000)
    #
    #     consumption_list.append(total_consumption)
    #     bytes_list.append(total_bytes)
    #     print(
    #         f"Population: {population}, Total consumption: {total_consumption} mWs, total bytes: {total_bytes},"
    #         f" Time elapsed: {round((time.time() - start),1)}")
    #
    #     plt.figure('Power')
    #     plt.plot(actual_power_list)
    #     plt.figure('Bandwidth')
    #     plt.plot(actual_bandwidth_list)
    # plt.figure('Consumption')
    # plt.plot(consumption_list)
    # plt.figure('Bytes')
    # plt.plot(bytes_list)
    # plt.figure('Delay')
    # plt.plot(delay_list)
    # plt.show()
