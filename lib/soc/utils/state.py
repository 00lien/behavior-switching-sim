from typing import Union, Type, Dict, Tuple

INT_STATE_FIELDS = (
    'mid', 'x', 'y', 'z',
    'pitch', 'roll', 'yaw',
    'vgx', 'vgy', 'vgz',
    'templ', 'temph',
    'tof', 'h', 'bat', 'time'
)
FLOAT_STATE_FIELDS = ('baro', 'agx', 'agy', 'agz')

state_field_converters: Dict[str, Union[Type[int], Type[float]]]
state_field_converters = {key : int for key in INT_STATE_FIELDS}
state_field_converters.update({key : float for key in FLOAT_STATE_FIELDS})

class STATES:
    battery='bat'
    pitch='pitch'
    roll='roll'
    yaw='yaw'
    velocity_x='vgx'
    velocity_y='vgy'
    velocity_z='vgz'
    temperature_lower_bound='templ'
    temperature_higher_bound='temph'
    time_of_flight_distance_in_cm='tof'
    height_in_cm='h'
    barometer_in_cm='baro'
    time_of_motors_on='time'
    accelleration_x='agx'
    accelleration_y='agy'
    accelleration_z='agz'
    mpad_x='x'
    mpad_y='y'
    mpad_z='z'
    mpad_id='mid'
    mpry='mpry'

"""
    This class is written in singleton patten because state needs to be updated not the whole object
"""

class State:
    
    def __init__(self) -> None:
        self.state_dict = {}

    def to_string(self):
        return str(self.state_dict)

    def get_state_value(self, param:str):
        if(bool(self.state_dict) is False):
            return 'None'
        else:
            return self.state_dict.get(param)
        
    def to_float(self, value: str):
        if(value == 'None'):
            return 0
        return float(value)
    
    def to_neumaric(self, value: str):
        if(value == 'None'):
            return 0
        return int(value)

    def update(self, state: str):
        state = state.strip()

        if state == 'ok':
            return {}
        
        for field in state.split(';'):
            split = field.split(':')
            if len(split) < 2:
                continue

            key = split[0]
            value: Union[int, float, str] = split[1]

            if key in state_field_converters:
                num_type = state_field_converters[key]
                try:
                    value = num_type(value)
                except ValueError as e:
                    continue

            self.state_dict[key] = value

        self.state_dict['is_in_air'] = True if self.state_dict.get('tof') is not None and self.state_dict.get('tof') > 15 else False

    def get_is_in_air(self) -> Union[bool, None]:
        return self.get_state_value('is_in_air')
    
    def get_mission_pad_id(self) -> int:
        return self.to_neumaric(self.get_state_value(STATES.mpad_id))
    
    def get_mission_pad_position(self) -> Tuple:
        return (self.get_state_value(STATES.mpad_x), self.get_state_value(STATES.mpad_y), self.get_state_value(STATES.mpad_z))

    def get_mission_pad_x(self) -> float:
        return self.get_state_value(STATES.mpad_x)

    def get_mission_pad_y(self)-> float:
        return self.get_state_value(STATES.mpad_y)

    def get_mission_pad_z(self)-> float:
        return self.get_state_value(STATES.mpad_z)

    def get_velocity_x(self)-> float:
        return -self.to_float(self.get_state_value(STATES.velocity_x))/10

    def get_velocity_y(self)-> float:
        return self.to_float(self.get_state_value(STATES.velocity_y))/10
    
    def get_velocity_z(self)-> float:
        return self.to_float(self.get_state_value(STATES.velocity_z))/10
    
    def get_acceloration_x(self)-> float:
        return -self.to_float(self.get_state_value(STATES.accelleration_x))/100

    def get_acceloration_y(self)-> float:
        return self.to_float(self.get_state_value(STATES.accelleration_y))/100
    
    def get_acceloration_z(self)-> float:
        return self.to_float(self.get_state_value(STATES.accelleration_z))/100
    
    def get_roll(self)-> float:
        return self.to_float(self.get_state_value(STATES.roll))

    def get_pitch(self)-> float:
        return self.to_float(self.get_state_value(STATES.pitch))
    
    def get_yaw(self)-> float:
        return self.to_float(self.get_state_value(STATES.yaw))
    
    def get_angles(self)->Tuple:
        return (self.get_roll(), self.get_pitch(), self.get_yaw())
    
    def get_height(self)-> float:
        return self.to_float(self.get_state_value(STATES.height_in_cm))/100
    
    def get_tof(self)-> float:
        return self.to_float(self.get_state_value(STATES.time_of_flight_distance_in_cm))/100
    
    def get_mpry(self) -> Tuple[int, int, int]:
        dc = self.get_state_value(STATES.mpry).split(',')
        return (self.to_neumaric(dc[2]),self.to_neumaric(dc[0]),self.to_neumaric(dc[1]))
    
    def get_battery(self)->int:
        val = self.get_state_value(STATES.battery)
        if val == 'None':
            return -1
        else:
            return int(val)