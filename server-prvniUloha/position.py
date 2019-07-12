import address
import socket
from _thread import *
import threading
from threading import Thread
import re
import os
import time
import collections

class Position:
    def __init__(self,INy = 0,INx = 0, prevY = 0, prevX = 0):
        self.posX = INx
        self.posY = INy
        self.posPrevX = prevX
        self.posPrevY = prevY
    def changeParent(self, y, x):
        self.posPrevX = x
        self.posPrevY = y