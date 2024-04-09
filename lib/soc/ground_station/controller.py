import socket
import gc
import threading
import time
from pubsub import pub
from typing import Dict, Tuple
from ..utils.logger import init_logging
from ..utils.break_exception import BreakException
from ..drone_factory.drone import Drone, COMMANDS
from ..constants import DEFAULT_HOST_IP, DEFAULT_HOST_COMMAND_PORT, DEFAULT_HOST_STATE_PORT, DEFAULT_BUFFER_SIZE, MAX_TIME_OUT, ODO

is_thread_initialized = False

class Controller:

    def __init__(self):

        global is_thread_initialized
        self.LOGGER = init_logging()
        self.__registered_drones: Dict[str, Drone] = dict()

        if not is_thread_initialized:
            is_thread_initialized = True
            self.__cmd_socket = self.__create_socket(address=(DEFAULT_HOST_IP, DEFAULT_HOST_COMMAND_PORT))
            self.__start_listener(target = self.__receive_command_thread)
            self.__state_socket = self.__create_socket(address=(DEFAULT_HOST_IP, DEFAULT_HOST_STATE_PORT))
            self.__start_listener(target = self.__receive_state_thread)
            
            #pubsub_
            
            self.__start_listener(target=self.__broadcast_state)

    def get_registered_drones(self):
        return self.__registered_drones
    
    def print_registered_drones(self):
        self.LOGGER.info(f"{self.get_registered_drones_count()} drones are registered!")
        for drone in self.get_registered_drones().values():
            self.LOGGER.info(f"{drone.get_ip()}: {'Server' if drone.is_server_mode() else 'client'}")
    
    def get_registered_drones_count(self):
        return len(self.__registered_drones.keys())
    
    #region Core Method
    """
        create a UDP socket for the given address
    """
    def __create_socket(self,address):
        tmp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        tmp_socket.bind(address)
        return tmp_socket
    
    """ 
        Start new thread to listen targeted udp socket
    """
    def __start_listener(self, target):
        receive_thread = threading.Thread(target=target)
        receive_thread.daemon = True
        receive_thread.start()
        return receive_thread

    def close(self):
        is_thread_initialized = False
        time.sleep(1)
        self.__cmd_socket.close()
        self.__state_socket.close()

    def __broadcast_state(self):
        while(True):
            data = []
            for d in self.get_registered_drones().values():
                data.append({
                    'ip': d.get_ip(),
                    'connected': d.is_connected(),
                    'x': d.x,
                    'y': d.y,
                    'z':d.z,
                    'vx': d.vx,
                    'vy': d.vy,
                    'vz': d.vz,
                    'psi': d.psi,
                    'tof': str(d.get_state().get_tof()),
                    'batt': d.get_state().get_battery(),
                    'armed': d.get_state().get_is_in_air()
                })
            pub.sendMessage(ODO, loc = data)
            time.sleep(0.001)
    #endregion
    
    #region Drone Registration
    def register_drone(self, drone: Drone):
        drone.set_command_channel(self.__cmd_socket)
        self.__registered_drones[drone.get_ip()] = drone
        self.LOGGER.info(f"[{drone.get_ip()}] drone is registered!")
        return self.__registered_drones

    def deregister_drone(self, drone: Drone):
        drone.set_command_channel(None)
        self.__registered_drones.pop(drone.get_ip())
        self.LOGGER.info(f"[{drone.get_ip()}] drone is unregistered!")
        gc.collect()
        return self.__registered_drones
    
    def deregister_all_drones(self):
        self.__registered_drones = dict()
        self.LOGGER.info(f"all drones are unregistered!")
        gc.collect()
        return self.__registered_drones
    
    #endregion
    
    #region Sockets and Listeners
    """
        Recieve responses for sent command and publish it to the relevent drone object
    """
    def __receive_command_thread(self):
        while is_thread_initialized:
            try:
                data, ip = self.__cmd_socket.recvfrom(DEFAULT_BUFFER_SIZE)
                self.LOGGER.debug("CMD: {}: Recieved {}".format(ip, data))

                # check the drone is registered
                drone: Drone = self.__registered_drones.get(ip[0])
                if drone is None:
                    continue
                
                if drone.is_empty_messages():
                    continue
                drone.set_response_to_last_message(data)
            except Exception as e:
                self.LOGGER.error(e, exc_info=True)
                break

    """
        Recieve responses from drone state manager
    """
    def __receive_state_thread(self):
        while is_thread_initialized:
            try:
                data, ip = self.__state_socket.recvfrom(DEFAULT_BUFFER_SIZE)
                # check the drone is registered
                
                drone: Drone = self.__registered_drones.get(ip[0])
                if drone is None:
                    continue
                
                drone.update(data=data)
            except Exception as e:
                self.LOGGER.error(e, exc_info=True)
                break

    """
        register drone to the ground station
    """
    #endregion

    #region Swarm Functions

    def swarm_control_wait(self, t=3):
        time.sleep(t)

    def swarm_wait_for_control_ok(self):
        
        success, failed = [], []
        drones_list = dict.fromkeys(self.get_registered_drones().keys(), False)
        timeout = time.process_time() + MAX_TIME_OUT
        count = self.get_registered_drones_count()
        try:
             while True:
                for key in drones_list.keys():
                    if(drones_list[key] is True):
                        continue               
                    drone = self.get_registered_drones().get(key)
                    response = drone.check_control_response()
                    if response is not None:
                        if(response is True):
                            success.append(drone)
                        else:
                            failed.append(drone)
                        if(len(success)+len(failed) == count):
                            raise BreakException()
                        
                if time.process_time() >= timeout:
                    self.LOGGER.warn('Swarm Control - Max timeout exceeded...')
                    raise BreakException()
        except BreakException:
            pass
        except Exception as ec:
            self.LOGGER.error(ec, exc_info=True)
        return success, failed
    
    def swarm_wait_for_control_ok_for_drones_set(self, drones=[]):
        
        success, failed = [], []
        drones_list = dict.fromkeys(self.get_registered_drones().keys(), False)
        timeout = time.process_time() + MAX_TIME_OUT
        count = self.get_registered_drones_count()
        try:
             while True:
                for key in drones_list.keys():
                    if(drones_list[key] is True):
                        continue               
                    drone = self.get_registered_drones().get(key)
                    response = drone.check_control_response()
                    if response is not None:
                        if(response is True):
                            success.append(drone)
                        else:
                            failed.append(drone)
                        if(len(success)+len(failed) == count):
                            raise BreakException()
                        
                if time.process_time() >= timeout:
                    self.LOGGER.warn('Swarm Control - Max timeout exceeded...')
                    raise BreakException()
        except BreakException:
            pass
        except Exception as ec:
            self.LOGGER.error(ec, exc_info=True)
        return success, failed
    
    def swarm_wait_for_connect_ok(self):
        
        success, failed = [], []
        drones_list = dict.fromkeys(self.get_registered_drones().keys(), False)
        count = self.get_registered_drones_count()
        timeout = time.process_time() + MAX_TIME_OUT
        try:
             while True:
                for key in drones_list.keys():
                    if(drones_list[key] is True):
                        continue               
                    drone = self.get_registered_drones().get(key)
                    response = drone.check_connection_response()
                    if response is not None:
                        if(response is True):
                            success.append(drone)
                        else:
                            failed.append(drone)
                            self.deregister_drone(drone)
                        drones_list[key] = True
                        if(len(success)+len(failed) == count):
                            raise BreakException()
                if time.process_time() >= timeout:
                    for key in drones_list.keys():
                        if(drones_list[key] is False):
                             self.deregister_drone(self.get_registered_drones().get(key))
                    self.LOGGER.warn('Swarm Control - Max timeout exceeded...')
                    raise BreakException()
        except BreakException:
            pass
        except Exception as ec:
            self.LOGGER.error(ec, exc_info=True)
        return success, failed
    
    def swarm_wait_for_read_response(self) -> list:
        
        return_codes = []
        drones_list = dict.fromkeys(self.get_registered_drones().keys(), False)
        timeout = time.process_time() + MAX_TIME_OUT
        count = self.get_registered_drones_count()
        try:
             while True:
                for key in drones_list.keys():
                    if(drones_list[key] is True):
                        continue               
                    drone = self.get_registered_drones().get(key)
                    response = drone.check_read_response()
                    if response is not None:
                        return_codes = response
                        if(len(return_codes) == count):
                            raise BreakException()
                        
                if time.process_time() >= timeout:
                    self.LOGGER.warn('Swarm Control - Max timeout exceeded...')
                    raise BreakException()
        except BreakException:
            pass
        except Exception as ec:
            self.LOGGER.error(ec, exc_info=True)
        return return_codes
    
    def swarm_connect_all(self):
        for drone in self.get_registered_drones().values():
            drone.connect_async()
    
    def swarm_takeoff_all(self):
        for drone in self.get_registered_drones().values():
            drone.take_off() 

    def swarm_land_all(self):
        for drone in self.get_registered_drones().values():
            drone.land()

    def swarm_come_back_init_positions(self):
        for drone in self.get_registered_drones().values():
            drone.go_to_position_in_meters(drone.init_pos[0], drone.init_pos[1])
    
    def swarm_land_emergency(self):
        for drone in self.get_registered_drones().values():
            drone.emergency() 
        exit()

    def swarm_command_for_all(self, command: str):
        for drone in self.get_registered_drones().values():
            drone.send_command(command=command)

    def swarm_update_gc(self, x, y):
        for drone in self.get_registered_drones().values():
            drone.x+=x
            drone.y+=y
    
    def swarm_localize_through_mpads(self, pads:Dict[int, Tuple[float, float, float]]):
        for drone in self.get_registered_drones().values():
            pad_id = drone.get_state().get_mission_pad_id()
            if pad_id < 0:
                self.LOGGER.warn(f"{drone.get_ip()} No mission pad id found...")
                drone.x = 0
                drone.y =0
                drone.psi =0
                continue
            pad = pads.get(pad_id)
            if pad is None:
                self.LOGGER.warn(f"{drone.get_ip()} No mission pads found...")
                drone.x = 0
                drone.y =0
                drone.psi =0
                continue
            
            (x, y, _) = pad
            drone.init_pos = (x, y)
            drone.x = x - (drone.get_state().get_mission_pad_x()*0.01)
            drone.y = y - (drone.get_state().get_acceloration_y()*0.01)

            drone.psi = drone.get_state().get_mpry()[2]

    def correct_drone_angles(self):
        for drone in self.get_registered_drones().values():
            cmd = COMMANDS.rotate_ccw(abs(drone.psi)) if drone.psi <0 else COMMANDS.rotate_cw(abs(drone.psi))
            drone.send_command(command=cmd)

    def swarm_print_global_localization(self):
        for drone in self.get_registered_drones().values():
            self.LOGGER.info(f"{drone.get_ip()} | x={drone.x}, y={drone.y}, z={drone.z}")

    def print_states(self):
        for drone in self.get_registered_drones().values():
            self.LOGGER.info(f"{drone.get_ip()}: {drone.get_state().to_string()}")
            
    #endregion