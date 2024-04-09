import numpy as np
import multiprocessing as mp
import matplotlib.pyplot as plt
from ..ground_station.controller import Controller
from pubsub import pub

class Trajectory():

    def __init__(self, min_v=-5, max_v=5, figure_width=5) -> None:

        self.colors = ['red','green','blue','magenta', 'cyan', 'yellow','black']

        self.fig = plt.figure()
        self.fig.set_figwidth(figure_width)
        self.ax = self.fig.add_subplot(1, 2, 1, projection='3d')
        self.ax1 = self.fig.add_subplot(1, 2, 2, projection='rectilinear')

        min = min_v
        max = max_v
        size_ = abs(min)+abs(max)
        self.x_axis = np.arange(min, max)
        self.y_axis = np.arange(min, max)
        self.z_axis = np.arange(min, max)

        self.ax = self.create_3d_plot(min,max, size_, self.ax)
        self.ax1 = self.create_2d_plot(min,max, self.ax1)

        self.values= []


    def create_3d_plot(self, min, max, size_, ax):

        ax.plot([0,0], [0,0], [0,0], 'k+')
        ax.plot(self.x_axis, np.zeros(size_), np.zeros(size_), 'r--', linewidth = 0.5)
        ax.plot(np.zeros(size_), self.y_axis, np.zeros(size_), 'g--', linewidth = 0.5)
        ax.plot(np.zeros(size_), np.zeros(size_), self.z_axis, 'b--', linewidth = 0.5)

        ax.set_xlim([min, max])
        ax.set_ylim([min, max])
        ax.set_zlim([min, max])

        ax.set_xlabel('X-axis (in meters)')
        ax.set_ylabel('Y-axis (in meters)')
        ax.set_zlabel('Z-axis (in meters)')

        return ax

    def create_2d_plot(self, min, max, ax):

        ax.set_xlim([min, max])
        ax.set_ylim([min, max])

        ax.set_xlabel('Y-axis (in meters)')
        ax.set_ylabel('X-axis (in meters)')

        return ax
    
    def call_back(self):
        while self.pipe.poll():
            drones = self.pipe.recv()
            if drones is None:
                continue
            
            for i,drone in enumerate(drones):
                if(i >= len(self.values)):
                    self.values.append([[drone['y']],[drone['x']],[drone['z']]])
                else:
                    self.values[i][0].append(drone['y'])
                    self.values[i][1].append(drone['x'])
                    self.values[i][2].append(drone['z'])
                    self.ax.plot(self.values[i][0],self.values[i][1], self.values[i][2], '-', markersize=1, color=self.colors[(i % 7)])
                    self.ax1.plot(self.values[i][0],self.values[i][1], '-', linewidth=1, markersize=1, color=self.colors[(i % 7)])
        self.fig.canvas.draw()
        return True
    
    def terminate(self):
        plt.close('all')
    
    def __call__(self, pipe):
        self.pipe = pipe
        timer = self.fig.canvas.new_timer(interval=1000)
        timer.add_callback(self.call_back)
        timer.start()
        plt.show()

class NBPlot(object):

    def call_back(self, loc):
        try:
            self.plot_pipe.send(loc)
        except:
            pass

    def __init__(self, min_v =-5, max_v=5, figure_width=10):
        self.plot_pipe, plotter_pipe = mp.Pipe()
        self.plotter = Trajectory(min_v, max_v, figure_width)
        self.plot_process = mp.Process(
            target=self.plotter, args=(plotter_pipe,), daemon=True)
        self.plot_process.start()
        pub.subscribe(self.call_back, 'odo')

    def plot(self, data):
        self.plot_pipe.send(data)