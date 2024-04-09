from math import *
from ..constants import FOCUL_LENGTH, AVERAGE_HEIGHT_OF_A_PERSON, FRAME_HEIGHT, SENSOR_SIZE, FRAME_WIDTH, GRID_SIZE

delim = lambda x: 0.5 if x >= 0 else -0.5

"""
    calculate distance by s = ut + 1/2 at^2
"""
def calculate_distance(u, a, t):
    return (u*t) + (0.5*a*t*t)

def calc_rotation_matrix( X, Y, Z, PHI, THETA, PSI):
        X_ = cos(PSI)*cos(THETA)*X + sin(PSI)*cos(THETA)*Y - sin(THETA)*Z
        Y_ = (cos(PSI)*sin(PHI)*sin(THETA) - cos(PHI)*sin(PSI))*X + (sin(PHI)*sin(PSI)*sin(THETA)+cos(PHI)*cos(PSI))*Y + (cos(THETA)*sin(PHI))*Z
        Z_ = (cos(PHI)*cos(PSI)*sin(THETA) + sin(PHI)*sin(PSI))*X + (cos(PHI)*sin(PSI)*sin(THETA)-cos(PSI)*sin(PHI))*Y + (cos(PHI)*cos(THETA))*Z
        return (X_, Y_, Z_)

"""This gives the distance by millimeters"""
def calc_approximate_distance_to_object_by_avg_human_height(pixel_height):
      return (FOCUL_LENGTH * AVERAGE_HEIGHT_OF_A_PERSON * FRAME_HEIGHT)/(pixel_height * SENSOR_SIZE)

def calc_approximate_x_y_in_mms(xc, yc, ratio):
      approximately_y = ((FRAME_HEIGHT/2) - yc) * ratio 
      approximately_x = ((FRAME_WIDTH/2) - xc) * ratio 
      return (approximately_x, approximately_y)

def to_meters(mm):
      return round(mm/1000, 2)

"""
      get grid coordinates
      x and y should be in meters
"""
def get_grid_coords_from_meters(x, y):
      return int((x/GRID_SIZE)+delim(x)), int((y/GRID_SIZE)+delim(y))

"""
      get meters coordinates from grid
      x and y should be in grid coords
"""
def get_meters_from_grid_coords(x, y):
      return x * GRID_SIZE, y * GRID_SIZE

def calculate_velocity(x,y, alpha=1.2, min =20, max=80):
      d = sqrt(x**2 + y**2)
      v = max / (1 + exp(-d * alpha))
      if v < min:
            return min
      elif v > max:
            return max
      else:
            return v
      
validate_a = lambda a: a if abs(a) > 0.3 else 0
