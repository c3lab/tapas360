#!/usr/bin/env python
# -*- Mode: Python -*-
# -*- encoding: utf-8 -*-
# Copyright (c) Giuseppe Ribezzo <giuseppe.ribezzo@poliba.it>
# Copyright (c) Luca De Cicco <luca.decicco@poliba.it>


# This file may be distributed and/or modified under the terms of
# the GNU General Public License version 3 as published by
# the Free Software Foundation.
# This file is distributed without any warranty; without even the implied
# warranty of merchantability or fitness for a particular purpose.
# See "LICENSE" in the source distribution for more information.
import os, sys, math
from utils_py.util import debug, format_bytes
from .BaseViewController import BaseViewController
DEBUG = 1

class ConventionalViewController(BaseViewController):

    def __init__(self):
        super(ConventionalViewController, self).__init__()
        

    def __repr__(self):
        return '<ConventionalViewController-%d>' %id(self)
    
    
    def getView(self, cur_view, cur_angles):
        '''
        Implement the viewport selection strategy.
        Returns the best viewpoint representation
        
        :param cur_view: viewpoint representation currently visualized 
        :param cur_angles: current angular data
        '''
        alpha      = cur_angles[0]
        new_view   = cur_view
        roi_center = self.feedback['yaw_angles'][cur_view]
        
        if (abs(roi_center - alpha) > (self.feedback['threshold_angle'] + self.feedback['delta'])):
            new_view = int((cur_view - math.copysign(1.0, roi_center - alpha)) % self.feedback['n_views'])
        return new_view

    
     
