from ..utils.commons import calculate_velocity

class COMMANDS:
    streamon= 'streamon'
    streamoff= 'streamoff'
    emergency= 'emergency'
    go = lambda x, y, z, speed : 'go {} {} {} {}'.format(x, y, z, speed)
    go_mpad = lambda x, y, z, speed, mid : 'go {} {} {} {} {}'.format(x, y, z, speed, mid)
    move_forward = lambda x : 'forward {}'.format(x)
    move_backword = lambda x : 'back {}'.format(x)
    move_left = lambda x : 'left {}'.format(x)
    move_right = lambda x : 'right {}'.format(x)
    move_up = lambda x : 'up {}'.format(x)
    move_down = lambda x : 'down {}'.format(x)
    rotate_cw = lambda x : 'cw {}'.format(x)
    rotate_ccw = lambda x : 'ccw {}'.format(x)
    enable_mission_pad= 'mon'
    disable_mission_pad= 'moff'
    keepalive= 'keepalive'
    set_mission_pad_detection= lambda x: 'mdirection {}'.format(x)
    get_hardware = 'hardware'
    sn = 'sn?'
    motoron = "motoron"
    motoroff= "motoroff"
    go_to_pos_relevent_to_global_3D = lambda v, v_0,speed: 'go {} {} {} {}'.format(int((v[0]-v_0[0])*100), int((v[1]-v_0[1])*100), int((v[2]-v_0[2])*100), speed)
    go_to_pos_relevent_to_global_2D = lambda v, v_0,speed: 'go {} {} {} {}'.format(int((v[0]-v_0[0])*100), int((v[1]-v_0[1])*100), int(0), speed)
    
    go_to_pos_relevent_to_global_2D_adj_speed = lambda v, v_0: 'go {} {} {} {}'.format(int((v[0]-v_0[0])*100), int((v[1]-v_0[1])*100), int(0), int(calculate_velocity(v[0]-v_0[0], v[1]-v_0[1])))

    def go_curve_relevent_to_global_3D(v, v_0,speed): 
        
        x_2 = int((v[0] - v_0[0])*100)
        y_2 = int((v[1] - v_0[1])*100)
        z_2 = int((v[2] - v_0[2]) *100)

        x_1 = int(x_2*0.4)
        y_1 = int(y_2*0.65)
        z_1 = int(z_2*0.8)
        
        return 'curve {} {} {} {} {} {} {}'.format(x_1, y_1, z_1, x_2, y_2, z_2, speed)
    
    def go_curve_relevent_to_global_2D(v, v_0,speed): 
        
        x_2 = int((v[0] - v_0[0])*100)
        y_2 = int((v[1] - v_0[1])*100)

        x_1 = int(x_2*0.4)
        y_1 = int(y_2*0.65)
        
        return 'curve {} {} {} {} {} {} {}'.format(x_1, y_1, 0, x_2, y_2, 0, speed)