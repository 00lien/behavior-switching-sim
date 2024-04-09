from .drone import Drone

DEFAULT_DRONE_IP = '192.168.10.1'

class Factory(Drone):
    
    @staticmethod
    def buildCommonDrone(ip):
        self = Drone(ip)
        self.set_server_mode(False)
        self.start();
        return self
    
    @staticmethod
    def buildServerDrone():
        self = Drone(DEFAULT_DRONE_IP)
        self.set_server_mode(True)
        self.start();
        return self