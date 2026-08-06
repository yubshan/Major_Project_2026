# Requirement / Purpose: Houses the custom, thread-safe central dictionary class that holds the global state of the robot. 
# It uses threading locks (threading.Lock()) to prevent data corruption.

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
        
