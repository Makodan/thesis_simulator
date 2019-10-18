import time
from math import floor

# Sample based simulator
#

timestep = 1  # s
# packet_size = 32 * 24  # byte
# base_consumption = 100  # Ws

# Delay due to processing and sending, receiving
cai_delay = 60 / 1000  # s
dai_delay = 80 / 1000
eai_delay = 100 / 1000
# cai_delay = 0  # s
# dai_delay = 0
# eai_delay = 0

# Maximal frequency in the given mode
cai_freq = 64  # Hz
dai_freq = 16
eai_freq = 8

# Size of sent packet
# TODO add received
cai_packet = 32 * 24  # byte
dai_packet = 80
eai_packet = 1


class Sensor():
    def __init__(self, id, frequency, ai_mode):
        self.id = id
        self.frequency = frequency
        self.ai_mode = ai_mode  # 0 - centralized AI, 1 - distributed AI, 2 - edge AI
        self.neighbours = list()
        self.event = False
        self.delay_handled = False
        self.event_duration = 0
        self.consumption = 0
        self.sent_bytes = 0
        self.samples = 0
        # AI mode dependant variables
        if ai_mode == 0:
            self.delay = cai_delay
            self.max_freq = cai_freq
            self.packet_size = cai_packet
        if ai_mode == 1:
            self.delay = dai_delay
            self.max_freq = dai_freq
            self.packet_size = dai_packet
        if ai_mode == 2:
            self.delay = eai_delay
            self.max_freq = eai_freq
            self.packet_size = eai_packet

    def step(self):
        # If there is new event process it, calculate with higher freqs,
        #  we have to handle the delay once due to processing
        if self.event:
            # If the event's duration or the remaining duration is shorter than a timestep
            if self.event_duration <= timestep:
                if not self.delay_handled:
                    self.samples += floor((self.event_duration - self.delay) * self.max_freq)
                    self.delay_handled = True
                    self.samples += floor((timestep - self.event_duration) * self.frequency)
                    print(self.event_duration)
                    print('aa')

                else:
                    # Max frequency samples
                    self.samples += floor(self.event_duration * self.max_freq)
                    # Base frequency samples
                    self.samples += floor((timestep - self.event_duration) * self.frequency)
                    print(self.event_duration)
                    print('bb')

                self.event = False
                self.delay_handled = False
                self.event_duration = 0

            # If the event's duration is longer then one timestep
            else:
                # The delay has NOT handled already
                if not self.delay_handled:
                    print(self.event_duration)
                    print('cc')
                    self.samples += floor((timestep - self.delay) * self.max_freq)
                    # self.event_duration -= self.delay
                    self.event_duration -= timestep
                    self.delay_handled = True
                # The delay has handled already
                else:
                    print(self.event_duration)
                    print('dd')
                    self.samples += floor(timestep * self.max_freq)
                    self.event_duration -= timestep

        # If there is no event, calculate with base freq
        else:
            self.samples += floor(timestep * self.frequency)

        # Summarize energy, sent bytes based on samples
        # Calculate E, B
        # ...
        self.sent_bytes += self.samples * self.packet_size
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


if __name__ == '__main__':
    s1 = Sensor(1, 2, 0)
    # s2 = Sensor(2, 2, 2)

    for s in range(0, 4):
        if s == 1:
            s1.register_event(0.5)
            print('event')
        s1.step()
        # s2.step()

