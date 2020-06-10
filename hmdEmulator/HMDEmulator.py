#!/usr/bin/env python
# -*- Mode: Python -*-
# -*- encoding: utf-8 -*-
# Copyright (c) Giuseppe Ribezzo <ribes170289@gmail.com>

# This file may be distributed and/or modified under the terms of
# the GNU General Public License version 2 as published by
# the Free Software Foundation.
# This file is distributed without any warranty; without even the implied
# warranty of merchantability or fitness for a particular purpose.
# See "LICENSE" in the source distribution for more information.

import csv
import numpy as np 
import math
import time
from twisted.internet import defer, reactor

sampling_time = 0.1

class HMDEmulator():
    def __init__(self, csv_file = None):
        self.readTrace(csv_file)
        self.pitch_angle  = self.getCurrentAngles(0.0)
        
        
    def start(self, t_experiment_started):
        self.t_experiment_started = t_experiment_started
        self.updateHMDPosition()
        
    def stop(self):
        reactor.stop()
        
    # update HMDPosition
    def updateHMDPosition(self):
        '''
        Performs hmd emulation
        Reads angular data from hmd trace each sampling_time seconds
        '''
        #try:
            ## for now, is bound to play time, theorically needs being indipendent
            ##playtime = self.media_engine.pipeline.query_position(Gst.Format.TIME)[1] * 10 ** -9#convert into second
            #playtime = time.time() - self.t_experiment_started
        #except Exception, e:
            #playtime = 0.0
        
        cur_angles = self.getCurrentAngles(time.time() - self.t_experiment_started)
        
        self.pitch_angle[0] = math.radians(cur_angles[0] / math.pi)
        self.pitch_angle[1] = math.radians(cur_angles[1] / math.pi)
        self.pitch_angle[2] = math.radians(cur_angles[2] / math.pi)
        
        reactor.callLater(sampling_time, self.updateHMDPosition)
        
        
    def getPitchAngle(self):
        '''
        Returns the current Pitch Angle in [0, 1]

        '''
        return self.pitch_angle
        
    def readTrace(self, csv_file):
        with open(csv_file) as filecsv:
            time = []
            alpha = []
            beta = []
            gamma = []
            self.reader = csv.reader(filecsv, delimiter=",")
            next(self.reader)
            for row in self.reader:
                time.append(float(row[0]))
                alpha.append(float(row[1]))
                beta.append(float(row[2]))
                gamma.append(float(row[3]))
        self.t = np.array(time)
        self.alpha = np.array(alpha)
        self.beta = np.array(beta)
        self.gamma = np.array(gamma)

    def get_time_idx(self, timestamp):
        '''
        Returns the index of the self.t array that is the closest to param:timestamp

        '''
        # Search the idx
        #return np.searchsorted(self.t, time % self.t[-1])
        timestamp = timestamp % np.amax(self.t)
        idx = (np.abs(self.t - timestamp)).argmin()
        return idx

    def getCurrentAngles(self, time):
        '''
        Gets the angles vector at time param:time
        '''
        idx = self.get_time_idx(time)
        return [self.alpha[idx], self.beta[idx], self.gamma[idx]]
        
 
