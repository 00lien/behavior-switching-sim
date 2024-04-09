import customtkinter
import sys
import cv2
from utils.configurations import Configs
from .controller import Manager
from pubsub import pub
from PIL import Image, ImageTk

customtkinter.set_appearance_mode("dark")

class Label(customtkinter.CTkLabel):

    def __init__(self, master, row, col, pref="{}"):
        super().__init__(master, width=30)
        self.pref = pref
        self.grid(row=row, column=col, padx=10, pady=(0, 0), sticky="w")
        self.configure(text=pref.format("-"))
    
    def set_text(self,text):
        self.configure(text=self.pref.format(text))

class StateButton(customtkinter.CTkButton):

    def __init__(self, master, row, col, states={}):
        super().__init__(master, width=30, hover=False, fg_color='#606770')
        self.states = states
        self.grid(row=row, column=col, padx=10, pady=(0, 0), sticky="w")
    
    def set_state(self, state):
        self.configure(text=self.states.get(state).get('text'))
        self.configure(text_color=self.states.get(state).get('text_color'))
        self.configure(border_color=self.states.get(state).get('text_color'))

class DroneRow(customtkinter.CTkFrame):
        
    def __init__(self, master, ip,  **kwargs):

        self.ip = ip
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        # add widgets onto the frame, for example:
        self.name_label = Label(self,0, 0, f"Drone [{ip}]")
        self.mpad_label = Label(self,0, 1, "MPAD [{}]")
        self.sn_label = Label(self,0, 2, "SN [{}]")
        self.con_state = StateButton(self, 0, 3, {
            'OFF':{
                'text': 'NOT CONNECTED',
                'text_color': '#ff0000'
            },
            'ON':{
                'text': 'CONNECTED',
                'text_color': '#11ff00'
            }
        })
        self.con_state.set_state('OFF')

        self.arm_state = StateButton(self, 0, 4, {
            'NOT_ARM':{
                'text': 'NOT ARMED',
                'text_color': '#ff0000'
            },
            'ARM':{
                'text': 'ARMED',
                'text_color': '#11ff00'
            }
        })
        self.arm_state.set_state('NOT_ARM')

        self.yaw = Label(self,0, 5, 'yaw = {}\N{DEGREE SIGN}')
        self.yaw.set_text("0")

        self.x = Label(self,0, 6, 'x = {}')
        self.y = Label(self,0, 7, 'y = {}')

        self.z = Label(self,0, 8, 'alt = {}')

        self.vx = Label(self,0, 9, 'vx = {}')
        self.vy = Label(self,0, 10, 'vy = {}')

        self.tof = Label(self,0, 11, 'tof = {}')

        self.batt = Label(self,0, 12, 'batt = {}v')
        self.batt.configure(text_color='red')

class TerminalWindow(customtkinter.CTkFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.textbox = customtkinter.CTkTextbox(self,  width=800,activate_scrollbars=True)
        self.textbox.grid(row=0, column=0, sticky="new")

    def write(self, text):
        self.textbox.insert('end', text)
        self.textbox.see('end')

    def flush(self):
        pass

class Dashboard(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.configs = Configs()
        self.configs.list_all()

        self.manager = Manager(self.configs)

        self.i =1
        self.title("Dashboard")
        self.state('zoomed')

        self.ips = self.configs.get_main('ips')
        if(self.ips is None or self.ips == ''):
            self.ips = []
        else:
            self.ips = self.ips.split(',')


        old_stdout = sys.stdout
        self.tf = TerminalWindow(self)
        self.tf.grid(row=4, column=0, padx=5, pady=5, sticky="ew")
        sys.stdout = self.tf
        
        self.drones = self.init_drones(row=2)
        self.drones_rows = self.init_buttons(row=0)

        self.emptyImage= customtkinter.CTkImage(light_image=None, dark_image=Image.open('assets/NI.png', mode='r'), size=(360,240))
        self.image_label = customtkinter.CTkLabel(self, width=360, height=240, image=self.emptyImage)
        self.image_label.grid(row=0, column=3, padx=5, pady=5, sticky="new")

        self.image_label_dr = customtkinter.CTkLabel(self, width=360, height=240, image=self.emptyImage)
        self.image_label_dr.grid(row=1, column=3, padx=5, pady=5, sticky="new")

        pub.subscribe(self.update, 'odo')
        pub.subscribe(self.update_image, 'original_image')
       # pub.subscribe(self.update_dr_image, 'drone_image')

        print("******************** Stareted ********************")

    def update_image(self, data):
        data = cv2.resize(data, (360, 240))
        b,g,r = cv2.split(data)
        img = cv2.merge((r,g,b))
        img = Image.fromarray(img)
       # img = ImageTk.PhotoImage(image=img)
        img = customtkinter.CTkImage(light_image=None, dark_image=img, size=(640,480))
        self.image_label.configure(image=img)

    def update_dr_image(self, data):
        data = cv2.resize(data, (360, 240))
        b,g,r = cv2.split(data)
        img = cv2.merge((r,g,b))
        img = Image.fromarray(img)
       # img = ImageTk.PhotoImage(image=img)
        img = customtkinter.CTkImage(light_image=None, dark_image=img, size=(640,480))
        self.image_label_dr.configure(image=img)

    def update(self, loc):
        self.thread_level.set((self.manager.del_state_value - 2)/(55-2))
        for data in loc:
            for dr in self.drones:
                if dr.ip == data.get('ip'):
                    # update connection state
                    dr.con_state.set_state("ON" if data.get('connected') is True else "OFF")
                    dr.yaw.set_text(data.get('psi'))
                    dr.x.set_text(round(data.get('x'),3))
                    dr.y.set_text(round(data.get('y'),3))
                    dr.z.set_text(round(data.get('z'),3))

                    dr.vx.set_text(round(data.get('vx'),3))
                    dr.vy.set_text(round(data.get('vy'),3))
                    dr.tof.set_text(data.get('tof'))
                    dr.batt.set_text(data.get('batt'))
                    dr.arm_state.set_state("ARM" if data.get('armed') is True else "NOT_ARM")

    def set_ip(self):
        self.ips = []
        if self.txt_ips.get() != '':
            c = self.txt_ips.get().split(',')
            self.ips = []
            for ck in c:
                self.ips.append(f"{ck}")
        self.configs.set_main('ips', '')
        self.configs.set_main('ips', ','.join(self.ips))
        self.init_drones()

    def init_buttons(self, row=1):

        self.btm_frame = customtkinter.CTkFrame(self, height=10)
        self.btm_frame.grid(row=row, column=0, padx=10, pady=(10, 0), sticky="nsw")

        self.btn_ip_set = customtkinter.CTkButton(self.btm_frame,  text="Set Ips", command=self.set_ip)
        self.btn_ip_set.grid(row=0, column=0, padx=2, pady=2, sticky="new")

        self.btn_connect = customtkinter.CTkButton(self.btm_frame, command=lambda: self.manager.connect_all())
        self.btn_connect.grid(row=0, column=1, padx=2, pady=2, sticky="new")
        self.btn_connect.configure(text="Connect")

        self.btn_arm = customtkinter.CTkButton(self.btm_frame, command=lambda: self.manager.arm_and_takeoff())
        self.btn_arm.grid(row=0, column=2,padx=2, pady=2, sticky="new")
        self.btn_arm.configure(text="Arm")

        self.btn_emland = customtkinter.CTkButton(self.btm_frame, command=lambda: self.manager.land())
        self.btn_emland.grid(row=0, column=4, padx=2, pady=2, sticky="new")
        self.btn_emland.configure(text="Land")

        self.btn_mission = customtkinter.CTkButton(self.btm_frame, command=lambda: self.manager.mission_start())
        self.btn_mission.grid(row=0, column=5, padx=2, pady=2, sticky="new")
        self.btn_mission.configure(text="Mission")

        self.btn_streamon = customtkinter.CTkButton(self.btm_frame, command=lambda: self.manager.stream_on())
        self.btn_streamon.grid(row=0, column=6, padx=2, pady=2, sticky="new")
        self.btn_streamon.configure(text="Stream On")

        self.btn_streamoff = customtkinter.CTkButton(self.btm_frame, command=lambda: self.manager.stream_off())
        self.btn_streamoff.grid(row=0, column=7, padx=2, pady=2, sticky="new")
        self.btn_streamoff.configure(text="Stream Off")

        self.btn_emland = customtkinter.CTkButton(self.btm_frame, command=lambda: self.manager.emland(), bg_color='red', fg_color='red')
        self.btn_emland.grid(row=0, column=8, padx=2, pady=2, sticky="new")
        self.btn_emland.configure(text="Emergency")

        self.btm_frame_1 = customtkinter.CTkFrame(self, height=10, width=800)
        self.btm_frame_1.grid(row=row+1, column=0, padx=10, pady=(10, 0), sticky="nsw")

        self.txt_ips = customtkinter.CTkEntry(self.btm_frame_1, width=800, placeholder_text="Drone IP list (192.168.137.x), leader ip 10.1 is already set")
        self.txt_ips.grid(row=0, column=0, padx=10, pady=5, sticky="new")

        self.thread_level = customtkinter.CTkProgressBar(self.btm_frame_1, width=800, height=20, orientation="horizontal", progress_color='green')
        self.thread_level.grid(row=1, column=0, padx=5, pady=5, sticky="new")

    def init_drones(self, row=3):

        self.drone_row_frame = customtkinter.CTkFrame(self)
        self.drone_row_frame.grid(row=row, column=0, padx=10, pady=(10, 0), sticky="nsw")

        self.i =0
        rows = []
        d = DroneRow(master=self.drone_row_frame, ip = '192.168.10.1', height=25)
        d.grid(row=self.i, column=0, padx=2, pady=2, sticky="new")
        rows.append(d)
        self.i += 1

        ips = []

        for ip in self.ips:
            if(ip == "1"):
                continue
            d = DroneRow(master=self.drone_row_frame, ip = f"192.168.0.{ip}", height=25)
            ips.append(f"192.168.0.{ip}")
            d.grid(row=self.i, column=0, padx=2, pady=2, sticky="new")
            rows.append(d)
            self.i += 1

        self.manager.register_drones(ips)
        return rows
    