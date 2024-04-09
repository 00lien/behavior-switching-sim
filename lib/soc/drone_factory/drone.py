import time
import gc
from ..utils import logger
from ..utils.state import State
from socket import socket
from typing import Union, Tuple
from .commands import COMMANDS
from ..constants import DEFAULT_HOST_COMMAND_PORT, MAX_TIME_OUT, DEFAULT_CV_PORT, MIN_BATTERY_AMOUNT, MARGINE_FROM_CENTER
from ..stream.background_stream import BackgroundFrameRead
from ..utils.break_exception import BreakException
from ..utils.commons import *
import numpy as np
import math

class Message:
    def __init__(self, command) -> None:
        self.request: str = command
        self.response: str = None

    def is_waiting_for_response(self):
        return self.response is None

class Drone(object):

    def __init__(self, ip):
        self.__ip:str = ip
        self.__is_shutdown:bool = False
        self.__messages: list = []
        self.__state: State = State()
        self.__server_mode:bool = True
        self.__command_channel: socket = None
        self.__is_connected: bool = False
        self.__stream = None
        self.LOGGER = logger.init_logging()
        self.__last_updated_time =0

        # this position
        self.x, self.y, self.z = 0, 0, 0
        self.ty = 0
        # roll pitch yaw
        self.phi, self. theta, self.psi = 0, 0, 0

        #corrections
        self.init_psi = None

        # linear velocities
        self.vx, self.vy, self.vz = 0, 0, 0
        # angular velocities
        self.ax, self.ay, self.az = 0, 0, 0

        self.init_pos = (0, 0)
        self.additional_state ={}

        self.linear_position = np.array

        self.get_linear_position = lambda: np.array([self.x, self.y, self.z]).reshape(3,1)
        self.get_angular_position = lambda: np.array([self.phi, self.theta, self.psi]).reshape(3,1)
        self.get_linear_velocities = lambda: np.array([self.vx, self.vy, self.vz]).reshape(3,1)
        self.get_angular_velocities = lambda: np.array([self.ax, self.ay, self.az]).reshape(3,1)
        
    def is_connected(self):
        return self.__is_connected

    def __validate_last_message_response(self) -> bool:
        return len(self.__messages) > 0 and self.__messages[-1].response is not None
    
    def is_the_drone_in_air(self):
        if(self.__state is None):
            return False
        res = self.__state.get_is_in_air()
        if(res is None):
            return False
        return res

    #region Getters & Setters
    
    def get_ip(self) -> str:
        return self.__ip
    
    def get_globle_position_vector(self):
        return (self.x, self.y, self.z)
    
    def set_response_to_last_message(self, msg):
        last_message: Message = self.__messages[-1]
        last_message.response = msg

    def update(self, data):

        data = data.decode('ASCII')
        self.__state.update(data)
        self.z = self.get_state().get_height()

        return

        # update globle 3D plane
        if(self.__last_updated_time == 0):
            self.__last_updated_time = time.time()
            return
        
        if self.init_psi is None:
           self.init_psi = -(self.get_state().get_yaw())
        
        self.phi = self.get_state().get_roll()
        self.theta = self.get_state().get_pitch()
        self.psi = -(self.get_state().get_yaw()) - self.init_psi

        self.vx = self.get_state().get_velocity_x()
        self.vy = self.get_state().get_velocity_y()
        self.vz = self.get_state().get_velocity_z()

        self.ax = validate_a(self.get_state().get_acceloration_x())
        self.ay = validate_a(self.get_state().get_acceloration_y())

        current_time = time.time()
        diff = current_time - self.__last_updated_time

        # update distances in meters
        self.x += (self.vx * abs(np.cos(np.deg2rad(self.psi))) * diff) + (self.ax * abs(np.cos(np.deg2rad(self.psi))) * diff * diff)
        self.y += (self.vy * abs(np.cos(np.deg2rad(self.psi))) * diff) + (self.ay * abs(np.cos(np.deg2rad(self.psi))) * diff * diff)
        self.z = self.get_state().get_height()

        self.LOGGER.debug(self.get_state().to_string())
    
        self.__last_updated_time = current_time

    def set_command_channel(self, socket_ref: socket):
        self.__command_channel= socket_ref

    def get_state(self) -> State:
        try:
            if(self.__state is None):
                return State()
            else:
                return self.__state
        except Exception:
            self.LOGGER.error(self.__state)
            return State()
        
    def is_server_mode(self):
        return self.__server_mode
    
    def set_server_mode(self, is_server:bool):
        self.__server_mode = is_server
    #endregion

    #region connection and disconnect

    def connect_sync(self):

        self.connect_async()

        timeout = time.process_time() + MAX_TIME_OUT
        
        try:
            while True:
                response = self.check_connection_response()
                if response is not None:
                    raise BreakException()
                if time.process_time() >= timeout:
                    self.LOGGER.warn('Swarm Control - Max timeout exceeded...')
                    raise BreakException()
        except BreakException:
            pass
        except Exception as ec:
            self.LOGGER.error(ec, exc_info=True)
        return self.__is_connected
    
    def connect_async(self):

        if self.__is_connected:
            self.LOGGER.error(f"[{self.get_ip()}] drone is already connected!")
            return False

        if self.__command_channel is None:
            self.LOGGER.error(f"[{self.get_ip()}] drone is not registered!")
            return False
        
        command = 'command'
        
        self.__messages.append(Message(command))
        self.__command_channel.sendto(command.encode('utf-8'), (self.get_ip(), DEFAULT_HOST_COMMAND_PORT))
        self.LOGGER.info(f"[{self.get_ip()}] connecting request sent")

    def check_connection_response(self) -> Union[None, bool]:
        try:
            if(self.__validate_last_message_response()):
                result = self.__messages.pop().response.decode("utf-8")
                if (result) and ('ok' in result.lower()):
                    self.LOGGER.info(f"[{self.get_ip()}] connected...!")
                    self.__is_connected = True
                elif (result) and ('unactive' in result.lower()):
                    self.LOGGER.error(f"[{self.get_ip()}] inactive drone, please activate the drone from server mode")
                    self.__is_connected = False
                else:
                    self.LOGGER.error(f"[{self.get_ip()}] connection is not established")
                    self.__is_connected = False
                return self.__is_connected
            else:
                return None
        except Exception as e:
            #self.LOGGER.error(e, exc_info=True)
            return False
    
    def disconnect(self):
        self.__is_connected = False
        self.LOGGER.info(f"[{self.get_ip()}] disconnected...!")
    
    #endregion
    
    #region takeoff and land

    def take_off(self):
        if self.is_the_drone_in_air():
            self.LOGGER.error(f"{self.get_ip()} drone is in the air, land the drone to take off again")

        self.send_command('takeoff')

    def land(self):
        if self.is_the_drone_in_air():
            self.LOGGER.error(f"{self.get_ip()} drone is not in the air, take off again")

        self.send_command('land')

    #endregion

    #region video stream from camera

    def set_steam_on(self):
        if not self.__server_mode:
            # TODO this is ask from the manufacturer and still no answer got
            self.LOGGER.error(f"{self.get_ip()} Drone should be in the sever mode to connect camera")
            return None
        
        if self.__stream is not None:
            self.LOGGER.error(f"{self.get_ip()} camera stream is opened")
            return self.__stream 

        response = self.execute_sync_command(COMMANDS.streamon)
        if(response is not False):
            self.LOGGER.info(f"{self.get_ip()} stream is about to open")
            address = BackgroundFrameRead.get_udp_address(self.get_ip(), DEFAULT_CV_PORT)
            self.__stream = BackgroundFrameRead(address=address)
            self.__stream.start()
            return self.__stream
        
    def set_steam_off(self):
        if not self.__server_mode:
            # TODO this is ask from the manufacturer and still no answer got
            self.LOGGER.error(f"{self.get_ip()} Drone should be in the sever mode to connect camera")
            return None
        
        if self.__stream is None:
            self.LOGGER.error(f"{self.get_ip()} camera stream is already closed")
            return None

        response = self.execute_sync_command(COMMANDS.streamoff)
        if(response is not False):
            self.__stream.stop()
            self.__stream = None
            gc.collect()
        return None
    
    def get_frame(self):
        if not self.__server_mode:
            # TODO this is ask from the manufacturer and still no answer got
            self.LOGGER.error(f"{self.get_ip()} Drone should be in the sever mode to connect camera")
            return None
        
        if self.__stream is None:
            self.LOGGER.error(f"{self.get_ip()} camera stream is closed")
            return None
        return self.__stream.get_frame()

    #endregion

    def shutdown_drone(self) -> None:
        self.__is_shutdown = True

    def __yield_sender(self):
        while(not self.__is_shutdown):
            command: str = yield
            self.LOGGER.info(f"Command Received [{self.__ip}: {command}]")
            self.execute_async_command(command=command)

    def __yield_go_to_pos(self):
        while(not self.__is_shutdown):
            (x, y, ang) = yield

            #TODO Turning

            # delta_y = y - self.y
            # delta_x = x - self.x

            #turn_angle = int(self.psi + np.rad2deg(np.arctan(delta_y/delta_x)))
            
            #print(f"x={x}, y={y} delta_y={delta_y} selfy={self.y} selfx={self.x} delta_x={delta_x} psi={self.psi} rad={np.rad2deg(np.arctan(delta_y/delta_x))} ta={turn_angle}")


            # if abs(turn_angle) > 3:
            #     cmd = COMMANDS.rotate_cw(turn_angle) if turn_angle > 0 else COMMANDS.rotate_ccw(turn_angle)
            #     self.execute_async_command(cmd)
            #     self.wait_for_async_control_command()

           
            # self.LOGGER.info(f"Command Received [{self.__ip}: Move to pos command executed]")

            if ang != 0:
                cmd = COMMANDS.rotate_cw(ang) if ang > 0 else COMMANDS.rotate_ccw(ang)
                self.execute_async_command(cmd)
                self.wait_for_async_control_command()

            if x > MARGINE_FROM_CENTER[0]:
                x = MARGINE_FROM_CENTER[0]
            elif x < MARGINE_FROM_CENTER[1]:
                x = MARGINE_FROM_CENTER[1]
            
            if y > MARGINE_FROM_CENTER[2]:
                y = MARGINE_FROM_CENTER[2]
            elif y < MARGINE_FROM_CENTER[3]:
                y = MARGINE_FROM_CENTER[3] 
            
            self.execute_async_command(COMMANDS.go_to_pos_relevent_to_global_2D_adj_speed((x,y), self.get_globle_position_vector()))
            self.x = x
            self.y = y
            self.psi = ang
    
    def start(self) -> None:
        self.__sender = self.__yield_sender()
        self.__goto_position = self.__yield_go_to_pos()
        self.__sender.send(None)
        self.__goto_position.send(None)

    def send_command(self, command) -> None:
        self.__sender.send(command)

    """
        x and y should be in grid coords
    """
    def go_to_position_ref_to_grid(self, x, y, ang = 0) -> None:
        x, y = get_meters_from_grid_coords(x, y)
        self.__goto_position.send((x, y, ang))

    def go_to_position_in_meters(self, x, y, ang =0) -> None:
        self.__goto_position.send((x, y, ang))

    def get_position_ref_to_grid(self):
        return get_grid_coords_from_meters(self.x, self.y)

    def is_empty_messages(self) -> bool:
        return self.__messages is None or len(self.__messages) <= 0
    
    def __check_battery(self):

        bat = self.get_state().get_battery()
        if(bat > 0 and bat < MIN_BATTERY_AMOUNT):
            self.LOGGER.error(f"{self.get_ip()} : Battery is not suffucient, please recharge..!")
            exit()

    def execute_sync_command(self, command: str) -> Union[str, bool]:

        if not self.__is_connected:
            self.LOGGER.error(f"[{self.get_ip()}] Drone is not connected...!")
            return False

        if self.__command_channel is None:
            self.LOGGER.error(f"[{self.get_ip()}] drone is not registered!")
            return False

        self.__check_battery()

        self.execute_async_command(command)
        try:
             timeout = time.process_time() + MAX_TIME_OUT
             while True:
                if(self.__validate_last_message_response()):
                    msg = self.__messages.pop().response.decode("utf-8")
                    return msg
                        
                if time.process_time() >= timeout:
                    self.LOGGER.warn(f"{self.get_ip()}: Max timeout exceeded...")
                    raise BreakException()
        except BreakException:
            pass
        except Exception as ec:
            self.LOGGER.error(ec, exc_info=True)
        return None
    
    def wait_for_async_control_command(self):
        try:
             timeout = time.process_time() + MAX_TIME_OUT
             while True:
                response = self.check_control_response()
                if response is not None:
                    self.LOGGER.info(f"{self.get_ip()}: Async command: {response}")
                    raise BreakException()
                        
                if time.process_time() >= timeout:
                    self.LOGGER.warn(f"{self.get_ip()}: Max timeout exceeded...")
                    raise BreakException()
        except BreakException:
            pass
        except Exception as ec:
            self.LOGGER.error(ec, exc_info=True)

    def wait_for_async_read_command(self) -> str | None:
        try:
             timeout = time.process_time() + MAX_TIME_OUT
             while True:
                response = self.check_read_response()
                if response is not None:
                    self.LOGGER.info(f"{self.get_ip()}: Async command: {response}")
                    return response
                        
                if time.process_time() >= timeout:
                    self.LOGGER.warn(f"{self.get_ip()}: Max timeout exceeded...")
                    raise BreakException()
        except BreakException:
            pass
        except Exception as ec:
            self.LOGGER.error(ec, exc_info=True)
        return None

    def wait_until_drone_stops(self):
        try:
             timeout = time.process_time() + MAX_TIME_OUT
             while self.is_flying():
                        
                if time.process_time() >= timeout:
                    self.LOGGER.warn(f"{self.get_ip()}: Max timeout exceeded...")
                    raise BreakException()
        except BreakException:
            pass
        except Exception as ec:
            self.LOGGER.error(ec, exc_info=True)
    
    def execute_async_command(self, command: str) -> Union[str, bool]:
        
        if not self.__is_connected:
            self.LOGGER.error(f"[{self.get_ip()}] Drone is not connected...!")
            return False

        if self.__command_channel is None:
            self.LOGGER.error(f"[{self.get_ip()}] drone is not registered!")
            return False
        
        self.__check_battery()
        
        self.__messages.append(Message(command))
        self.__command_channel.sendto(command.encode('utf-8'), (self.get_ip(), DEFAULT_HOST_COMMAND_PORT))

        self.LOGGER.info(f"[{self.get_ip()}] command \"{command}\" executed")
        return True
    
    def check_control_response(self) -> Union[None, bool]:
        try:
            if(self.__validate_last_message_response()):
                msg = self.__messages.pop().response.decode("utf-8")
                if 'ok' in msg.lower():
                    return True
                else:
                    self.LOGGER.error(msg)
                    return False
            return None
        except Exception as e:
            self.LOGGER.error(e, exc_info=True)
            return False
        
    def check_read_response(self) -> Union[None, str]:
        try:
            if(self.__validate_last_message_response()):
                return self.__messages.pop().response.decode("utf-8")
            return None
        except Exception as e:
            self.LOGGER.error(e, exc_info=True)
            return None
        
    def is_flying(self):
        return abs(self.get_state().get_velocity_x()) > 0 or abs(self.get_state().get_velocity_y()) >0 or abs(self.get_state().get_velocity_z())>0
    
    def get_sn(self):
        self.send_command(COMMANDS.sn)
        return self.wait_for_async_read_command()
    
    def emergency(self):
        self.send_command(COMMANDS.emergency)
    