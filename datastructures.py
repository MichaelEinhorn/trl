from collections import deque
import numpy as np
from torch.utils.data.dataset import IterableDataset
from typing import Iterable, Callable

class RollingBuffer:
    def __init__(self, max_size):
        self.max_size = max_size
        self.queue = deque([])

    def __len__(self):
        return len(self.queue)

    def __iter__(self):
        return iter(self.queue)

    def append(self, obj):
        self.queue.append(obj)
        if len(self.queue) > self.max_size:
            return self.queue.pop()
        else:
            return None

    def clear(self):
        self.queue = deque([])
        

class ExperienceSourceDataset(IterableDataset):
    """
    Implementation from PyTorch Lightning Bolts:
    https://github.com/PyTorchLightning/pytorch-lightning-bolts/blob/master/pl_bolts/datamodules/experience_source.py
    Basic experience source dataset. Takes a generate_batch function that returns an iterator.
    The logic for the experience source and how the batch is generated is defined the Lightning model itself
    """

    def __init__(self, generate_batch: Callable):
        self.generate_batch = generate_batch

    def __iter__(self) -> Iterable:
        iterator = self.generate_batch()
        return iterator


class ReplayBuffer:
    """
    Replay Buffer for storing past experiences allowing the agent to learn from them
    Args:
        capacity: size of the buffer
    """

    def __init__(self, capacity):
        self.buffer = deque(maxlen=capacity)

    def __len__(self):
        return len(self.buffer)

    def append(self, experience):
        """
        Add experience to the buffer
        Args:
            experience: tuple (scores, queries, responses, values, ret_cross, adv_cross)
        """
        self.buffer.append(experience)

    def sample(self, batch_size, data_collator):
        indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        # original states, actions, rewards, dones, next_states
        scores, queries, responses, values, ret_cross, adv_cross = zip(*[self.buffer[idx] for idx in indices])

        return scores, queries, responses, values, ret_cross, adv_cross
        # return (np.array(scores, dtype=np.float32), np.array(queries), np.array(responses),
        #         np.array(values, dtype=np.float32), np.array(ret_cross, dtype=np.float32), np.array(adv_cross, dtype=np.float32))


class RLDataset(IterableDataset):
    """
    Iterable Dataset containing the ReplayBuffer
    which will be updated with new experiences during training
    Args:
        buffer: replay buffer
        sample_size: number of experiences to sample at a time
    """
    
    def __init__(self, buffer: ReplayBuffer, data_collator, sample_size: int = 200):
        self.buffer = buffer
        self.sample_size = sample_size
        self.data_collator = data_collator

    def __iter__(self):
        scores, queries, responses, values, ret_cross, adv_cross = self.buffer.sample(self.sample_size, self.data_collator)
        for i in range(len(scores)):
            yield scores[i], queries[i], responses[i], values[i], ret_cross[i], adv_cross[i]
            
class LineBuffer:
    """
    Replay Buffer for storing past experiences allowing the agent to learn from them
    Args:
        capacity: size of the buffer
    """

    def __init__(self, capacity):
        self.buffer = deque(maxlen=capacity)

    def __len__(self):
        return len(self.buffer)

    def append(self, experience):
        self.buffer.append(experience)

    def sample(self, batch_size, data_collator):
        indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        # original states, actions, rewards, dones, next_states
        lines = [self.buffer[idx] for idx in indices]

        return lines
            
class LineDataset(IterableDataset):
    def __init__(self, buffer: LineBuffer, sample_size: int = 200):
        self.buffer = buffer
        self.sample_size = sample_size

    def __iter__(self):
        lines = self.buffer.sample(self.sample_size)
        for i in range(len(lines)):
            yield lines[i]
            
