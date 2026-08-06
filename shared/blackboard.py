# Requirement / Purpose: Houses the custom, thread-safe central dictionary class that holds the global state of the robot. 
# It uses threading locks (threading.Lock()) to prevent data corruption.

# Why it is needed: Your modules run concurrently on separate threads. 
# If Yubshan's WiFi module tries to write a human position at the exact microsecond 
# Teammate B's decision tree tries to read it, Python will throw a fatal runtime error or corrupt the data. 
# This file safely gates access so only one thread can touch the data at a time.



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
        
