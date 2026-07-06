import py_trees 


class IsHazardDetected(py_trees.behaviour.Behaviour):
    def __init__(self, robot):
        self.robot = robot
        super().__init__("IsHazardDetected")
    
    def update(self):
        sensors = self.robot.sensors




















        