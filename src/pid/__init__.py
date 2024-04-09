import time

class PID(object):
    
    def __init__(self, kp = (1,1,1), ki = (0,0,0), kd = (0,0,0), init_frame=(0,0,0)):
        
        self.kp, self.ki, self.kd = kp, ki, kd
        self.v_x = 0
        self.v_y = 0
        self.v_z = 0
        self.last_time = time.time()
        self.error_last_x = 0
        self.error_last_y = 0
        self.error_last_z = 0
        self.init_frame = init_frame
        self.pid = self.__calc_pid()
        self.pid.send(None)

        
    def __calc_pid(self):
        while(True):
            x, y, z = yield self.v_x, self.v_y, self.v_z

            # it should come as the distance over here, x - distance, although when we take the center (0) so, distance wont be necessary
            ex = x - self.init_frame[0]
            ey = y - self.init_frame[1]
            ez = z - self.init_frame[2]
            et = time.time()
            dt = et - self.last_time

            self.v_x =  (self.kp[0] * ex) + (self.ki[0] * ex * dt) + (self.kd[0] * (ex - self.error_last_x)/dt)
            self.v_y =  (self.kp[1] * ey) + (self.ki[1] * ey * dt) + (self.kd[1] * (ey - self.error_last_y)/dt)
            self.v_z =  (self.kp[2] * ez) + (self.ki[2] * ez * dt) + (self.kd[2] * (ez - self.error_last_z)/dt)

            self.error_last_x = ex
            self.error_last_y = ey
            self.error_last_z = ez
            self.last_time = et
        
    def call_pid(self, x, y, z):
        self.pid.send([x, y, z])

    def get_velocities(self):
        return self.v_x, self.v_y, self.v_z