# Requirement / Purpose: Houses the custom, thread-safe central dictionary class that holds the global state of the robot. 
# It uses threading locks (threading.Lock()) to prevent data corruption.

from copy import deepcopy
import threading  # provides a Lock through the threading module.


class Blackboard:

    def __init__(self):
        self._data = {}                 # shared dictionary
        self._lock = threading.Lock()   # protects data when different threads access it.

    def set(self, key, value):
        with self._lock:
            self._data[key] = value

    def get(self, key, default=None):    #retrieving the value
        with self._lock:
            return self._data.get(key, default)

    def update_many(self, values):
        """Atomically publish a related group of Blackboard values."""
        if not isinstance(values, dict):
            raise TypeError("Blackboard update must be a dictionary")
        with self._lock:
            self._data.update(values)

    def snapshot(self, keys=None):
        """Return a consistent deep copy of all values or selected keys."""
        with self._lock:
            if keys is None:
                return deepcopy(self._data)
            return deepcopy({key: self._data.get(key) for key in keys})
        
