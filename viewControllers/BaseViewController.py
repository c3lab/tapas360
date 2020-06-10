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
import os, sys, inspect
from utils_py.util import debug



class BaseViewController(object):
    
    def __init__(self):
        self.idle_duration = 4
        self.control_action =  None
        self.feedback = None           

    def __repr__(self):
        return '<BaseViewController-%d>' %id(self)

    def getAngles(self):
        return self.feedback['view_angles']
        
    def getView(self):
        '''
        Implement the viewport selection strategy.
        Returns the best viewpoint representation
        '''
        #raise NotImplementedError("Subclasses should implement "+inspect.stack()[0][3]+"()")
        return 0
   
    
    def setPlayerFeedback(self, dict_params):
        '''
        Sets the dictionary of all player feedback used for the control. 
        This method is called from ``TapasPlayer`` before ``calcControlAction``

        :param dict_params: dictionary of player feedbacks.
        '''
        self.feedback = dict_params



