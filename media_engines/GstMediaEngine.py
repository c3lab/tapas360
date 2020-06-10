#!/usr/bin/env python
# -*- Mode: Python -*-
# -*- encoding: utf-8 -*-
# Copyright (c) Giuseppe Ribezzo <ribes170289@gmail.com>
# Copyright (c) Luca De Cicco <luca.decicco@poliba.com>

# This file may be distributed and/or modified under the terms of
# the GNU General Public License version 3 as published by
# the Free Software Foundation.
# This file is distributed without any warranty; without even the implied
# warranty of merchantability or fitness for a particular purpose.
# See "LICENSE" in the source distribution for more information.
import os, sys, _thread
import traceback
import numpy as np
import math
from math import floor
import time, datetime
import gi

gi.require_version('Gst', '1.0')
gi.require_version('GstGL', '1.0')
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import GObject, Gst, GstGL, Gdk, GdkX11, Gtk

#
from twisted.internet import defer, reactor
from utils_py.util import debug, format_bytes
from hmdEmulator.HMDEmulator import HMDEmulator
from .BaseMediaEngine import BaseMediaEngine


DEBUG = 2


class GstMediaEngine(BaseMediaEngine):
    # qtdemux for video/mp4
    # mpegtsdemux for video/mpegts
    # matroskademux and for vp8_dec video/webm

    # ! capsfilter name=capsfilter
    # ! %s

    PIPELINE = '''
appsrc name=src is-live=0 max-bytes=0
    ! identity sync=false single-segment=true
    ! %s name=demux
    '''

    VIDEO_NODEC = ''' 
demux.
    ! queue name=queue_v max-size-buffers=0 max-size-time=0 max-size-bytes=0 min-threshold-time=%d
    ! %s
    '''

    VIDEO_DEC = ''' 
demux.
    ! %s name=parser
    ! queue name=queue_v max-size-buffers=0 max-size-time=0 max-size-bytes=0 min-threshold-time=%d
    ! %s
    '''

    DEMUX_MPEGTS = 'tsdemux'
    DEMUX_MP4 = 'qtdemux'
    DEMUX_WEBM = 'matroskademux'

    PARSE_H264 = 'h264parse'
    PARSE_MATROSKA = 'matroskaparse'

    # DEC_VIDEO_H264 = '''avdec_h264 ! timeoverlay ! videorate ! videoscale ! video/x-raw-yuv,width=1280,height=720,framerate=30/1,pixel-aspect-ratio=1/1 ! xvimagesink qos=0'''
    # DEC_VIDEO_VP8 = '''vp8dec ! timeoverlay ! videorate ! videoscale ! ! video/x-raw-yuv,width=1280,height=720,framerate=30/1,pixel-aspect-ratio=1/1 ! xvimagesink'''

    DEC_VIDEO_H264 = '''avdec_h264 direct-rendering=0 ! timeoverlay ! videorate ! videoscale method=0 add-borders=false '''
    DEC_VIDEO_VP8 = '''vp8dec ! timeoverlay ! videorate ! videoscale method=0 add-borders=false '''
    #DEC_VIDEO_H264_VR = '''avdec_h264 direct-rendering=0 ! timeoverlay ! videorate ! videoscale '''
    #DEC_VIDEO_VP8_VR = '''vp8dec ! timeoverlay ! videorate ! videoscale '''

    VIDEO_VR = '''
    ! glupload
    ! glcolorconvert 
    ! glcolorscale 
    ! glshader name=glshader
    '''
    
    FAKE_VIDEO_SINK = '''
    fakesink sync=true
    '''
    
    DEC_VIDEO_SINK = '''
    ! xvimagesink
    '''
    
    DEC_VIDEO_VR_SINK = '''
    ! glimagesink
    '''
    
    
    pitch_angle = [ 0.5, 0.5 ]
    
    uniforms_pitch_angle_u = GObject.Value(GObject.TYPE_FLOAT, pitch_angle[0])
    uniforms_pitch_angle_v = GObject.Value(GObject.TYPE_FLOAT, pitch_angle[1])
    
    side_original = float(1280.0)#TODO: need being read from manifest
    side_scaled   = float(480.0)

    rotationShaderFunctions = '''
mat4 rotationX(in float angle) {{
    return mat4(  1.0,           0.0,            0.0,      0.0,
                  0.0,    cos(angle),    -sin(angle),      0.0,
                  0.0,    sin(angle),     cos(angle),      0.0,
                  0.0,           0.0,            0.0,      1.0);
}}

mat4 rotationY(in float angle ) {{
    return mat4(   cos(angle),    0.0,    sin(angle),    0.0,
                          0.0,    1.0,           0.0,    0.0,
                  -sin(angle),    0.0,    cos(angle),    0.0,
                          0.0,    0.0,           0.0,    1.0);
}}

mat4 rotationZ(in float angle ) {{
    return mat4(   cos(angle),   -sin(angle),    0,    0,
                   sin(angle),    cos(angle),    0,    0,
                            0,             0,    1,    0,
                            0,             0,    0,    1);
}}
'''


    fragmentShaderPattern = '''
#version 100
#ifdef GL_ES
precision mediump float;
#endif
#define M_PI 3.1415926535897932384626433832795

varying vec2 v_texcoord;
uniform sampler2D tex;
uniform float pitch_angle_u;
uniform float pitch_angle_v;
uniform float noroi_width_ratio;
uniform float roi_width_ratio;

const vec4 kappa = vec4(1.0,1.7,0.7,15.0);

const float screen_width = {display_width}.0;
const float screen_height = {display_height}.0;
float side_ratio = {side_ratio};

const float scaleFactor = 0.9;

const vec2 leftCenter = vec2(0.25, 0.5);
const vec2 rightCenter = vec2(0.75, 0.5);

const float separation = -0.05;

vec2 fov = vec2(0.45, 0.45);
const vec2 sphere_limit = vec2(M_PI, M_PI / 2.0);

const bool stereo_input  = false;
const bool stereo_output = false;

int currentViewpoint = 0; 
vec3 red = vec3(1.0, 0.0, 0.0); 
vec3 green = vec3(0.0, 1.0, 0.0); 

float rescaleX(in float x) {{
    float b1 = noroi_width_ratio + roi_width_ratio;
    float b2 = 1.0 - roi_width_ratio;
    
    if(x <= (roi_width_ratio * 2.0 - 1.0) * M_PI) {{
        return x * side_ratio; 
    }} else if(x >= (b2 * 2.0 - 1.0) * M_PI) {{ 
        return ((b1 * 2.0 - 1.0) * M_PI) + (x - (b2 * 2.0 - 1.0) * M_PI) * side_ratio; 
    }} else {{ 
        return ((noroi_width_ratio * 2.0 - 1.0) * M_PI) + (x - (roi_width_ratio * 2.0 - 1.0) * M_PI); 
    }} 
}}

float rescaleY(in float y) {{ 
    return y*(1.0 - 1.0/180.0); 
}}

bool check_color(vec3 pixel, vec3 color) {{
    return distance(pixel, color) < 0.7; 
}}

// convert into radiant angles
vec2 get_coord_rad(vec2 point) {{
    vec2 coord_rad = (point * 2.0 - 1.0) * sphere_limit;
    return coord_rad;
}}

// convert into vector coordinates
vec2 get_rad_coord(vec2 point) {{
    vec2 rad_coord = ((point / sphere_limit) + 1.0) / 2.0;
    
    return rad_coord;
}}

vec2 projToSphere(vec2 texCoord, vec2 cp) {{
        
    float x = texCoord[0];
    float y = texCoord[1];

    float rou = sqrt(x * x + y * y);
    float c = atan(rou);
    float sin_c = sin(c);
    float cos_c = cos(c);

    float lat = asin(cos_c * sin(cp[1]) + (y * sin_c * cos(cp[1])) / rou);
    float lon = cp[0] + atan(x * sin_c, rou * cos(cp[1]) * cos_c - y * sin(cp[1]) * sin_c);

    lat = mod((lat / (M_PI / 2.0) + 1.0) * 0.5, 1.0);
    lon = mod((lon / M_PI + 1.0) * 0.5, 1.0);
    
    return vec2(lon, lat);
}}

// Scales input texture coordinates for distortion.
vec2 hmdWarp(vec2 LensCenter, vec2 texCoord, vec2 Scale, vec2 ScaleIn) {{
    vec2 theta = (texCoord - LensCenter) * ScaleIn; 
    float rSq = theta.x * theta.x + theta.y * theta.y;
    vec2 rvector = theta * (kappa.x + kappa.y * rSq + kappa.z * rSq * rSq + kappa.w * rSq * rSq * rSq);
    vec2 tc = LensCenter + Scale * rvector;
    return tc;
}}

bool validate(vec2 tc, int eye) {{
    if ( stereo_input ) {{
        //keep within bounds of texture 
        if ((eye == 1 && (tc.x < 0.0 || tc.x > 0.5)) ||   
            (eye == 0 && (tc.x < 0.5 || tc.x > 1.0)) ||
            tc.y < 0.0 || tc.y > 1.0) {{
            return false;
        }}
    }} else {{
        if ( tc.x < 0.0 || tc.x > 1.0 || 
             tc.y < 0.0 || tc.y > 1.0 ) {{
             return false;
        }}
    }}
    return true;
}}

void main() {{
    vec2  pitch_angle = vec2(pitch_angle_u, pitch_angle_v);
    float as          = float(screen_width / 2.0) / float(screen_height);
    vec2 Scale        = vec2(0.5, as);
    vec2 ScaleIn      = vec2(2.0 * scaleFactor, 1.0 / as * scaleFactor);

    vec2 texCoord = v_texcoord;
    
    // detect view
    if ({n_views} > 1) {{
        for(int i=0; i<{n_views}; i++) {{ 
            if(check_color(texture2D(tex, vec2((float(i) + 0.5)/float({n_views}), 0.0)).rgb, green)) {{ 
                currentViewpoint = i; 
                break; 
            }} 
        }}
        
        // disapply rotation
        float displacement = float({n_views} - currentViewpoint - 1) * 360.0/float({n_views})/180.0;
        pitch_angle[0] = pitch_angle[0] + displacement;
        //pitch_angle  = vec2(rescaleX(pitch_angle[0]), rescaleY(pitch_angle[1]));
    }}
    
    // extract plain field of view
    vec2 texCoord_rad    = get_coord_rad(texCoord) * fov;
    vec2 pitch_angle_rad = get_coord_rad(mod(pitch_angle, 1.0));
    vec2 erp_proj        = projToSphere(texCoord_rad, pitch_angle_rad);
    
    texCoord   = erp_proj;
    
    // rescale to original format
    if ({n_views} > 1) {{
        texCoord     = vec2(rescaleX(texCoord[0]), rescaleY(texCoord[1]));
    }}
    
    vec4 color = vec4(0);
    
    if (stereo_output) {{
        if ( texCoord.x < 0.5 ) {{
            texCoord.x += separation;
            texCoord = hmdWarp(leftCenter, texCoord, Scale, ScaleIn );
            
            if ( !stereo_input ) {{
                texCoord.x *= 2.0;
            }}
            
            color = texture2D(tex, texCoord);
            
            if ( !validate(texCoord, 0) ) {{
                color = vec4(0);
            }}
        }} else {{
            texCoord.x -= separation;
            texCoord = hmdWarp(rightCenter, texCoord, Scale, ScaleIn);
            
            if ( !stereo_input ) {{
                texCoord.x = (texCoord.x - 0.5) * 2.0;
            }}
            
            color = texture2D(tex, texCoord);
            
            if ( !validate(texCoord, 1) ) {{
                color = vec4(0);
            }}
        }}
    }} else {{
        color = texture2D(tex, texCoord);
    }}
    
    gl_FragColor = color;
}}
'''

    def __init__(self, decode_video=True, min_queue_time=10, vr=False, HMDEmulator=None, initial_view=0):
        BaseMediaEngine.__init__(self, min_queue_time, initial_view)
        self.decode_video    = decode_video
        self.pipeline        = None
        self.sink            = None
        self.bus             = None
        self.window          = None
        self.wnd_handler     = None
        self.ind             = 0
        self.queue           = dict(byte=0, sec=0)  #Initialized playout buffer at 0B and 0s
        self.pushed_segments = []
        self.playtime        = min_queue_time # need being set to min_queue_time because of fragment_duration misallignement
        self.evicted_segment = 0

        #vr
        self.vr           = vr
        self.HMDEmulator  = HMDEmulator
        self.n_views      = 1

    def __repr__(self):
        if self.decode_video:
            return '<GstMediaEngine-%d>' % id(self)
        else:
            return '<GstNoDecMediaEngine-%d>' % id(self)

    def start(self):
        try:
            BaseMediaEngine.start(self)
            #
            q = 0  # int(self.min_queue_time*1e9)   #min-threshold-time
            v_sink = self.FAKE_VIDEO_SINK
            if self.getVideoContainer() == 'MP4':
                demux = self.DEMUX_MP4
                parse = self.PARSE_H264
            elif self.getVideoContainer() == 'MPEGTS':
                demux = self.DEMUX_MPEGTS
                parse = self.PARSE_H264
            elif self.getVideoContainer() == 'WEBM':
                demux = self.DEMUX_WEBM
                parse = self.PARSE_WEBM
            else:
                debug(0, '%s Cannot play: video/%s', self, self.getVideoContainer())
                return
            debug(DEBUG, '%s Playing type: video/%s', self, self.getVideoContainer())
            
            if self.decode_video:
                v_sink = self.DEC_VIDEO_SINK
                    
                #self.lock = _thread.allocate_lock()
                _thread.start_new_thread(self.createGtkWindow, tuple())
                
                if not self.getVideoContainer() == 'WEBM':
                    v_rend = self.DEC_VIDEO_H264
                else:
                    v_rend = self.DEC_VIDEO_VP8
                    
                if self.vr:
                    v_sink = self.DEC_VIDEO_VR_SINK
                    v_rend = v_rend + self.VIDEO_VR
                desc = self.PIPELINE % (demux) + self.VIDEO_DEC % (parse, q, v_rend) + v_sink
            else:
                desc = self.PIPELINE % (demux) + self.VIDEO_NODEC % (q, v_sink)
            debug(DEBUG, '%s pipeline: %s', self, desc)


            Gst.init(None)
            self.pipeline = Gst.parse_launch(desc)
            self.pipeline.set_state(Gst.State.PLAYING)
            
            if (self.vr and self.decode_video):
                shader     = self.pipeline.get_by_name('glshader')
                fragShader = self.fragmentShaderPattern.format(display_width=1920, display_height=1080, n_views=self.n_views, side_ratio=float(self.side_scaled/self.side_original))
                shader.set_property("fragment", fragShader)
                
                if (self.n_views > 1):
                    struct_uniform = Gst.Structure.new_empty("uniforms")
                    struct_uniform.set_value("noroi_width_ratio", GObject.Value(GObject.TYPE_FLOAT, float(self.side_scaled / (2.0 * self.side_scaled + self.side_original))))
                    struct_uniform.set_value("roi_width_ratio", GObject.Value(GObject.TYPE_FLOAT, float(1.0/3.0)))
                    struct_uniform.fixate()
                    shader.set_property("uniforms", struct_uniform)
                
                # this work for glimagesink
                self.sink = self.pipeline.get_by_name('sink')
                xid = self.wnd_handler.get_window().get_xid()
                self.sink.set_window_handle(xid)
                self.sink.set_property("force-aspect-ratio", True)
                
                # update head position
                self.updateShaderPosition()
                
            self.GstQueue = self.pipeline.get_by_name('queue_v')
            self.status = self.PAUSED
            self.pipeline.set_state(Gst.State.PAUSED)
            
            self.onRunning()
            
            # manage events on the bus
            self.bus = self.pipeline.get_bus()
            self.bus.add_signal_watch()
            self.bus.enable_sync_message_emission()
            self.bus.connect('message', self.gstMessageHandler)
            self.bus.connect('sync-message::element', self.gstMessageHandler)
        except Exception as e:
            traceback.print_exc()
            Gtk.main_quit
            self.stop()
            
    def checkGstbuffer(self):
        if (len(self.pushed_segments) > 0 and self.GstQueue.get_property('current-level-time') * 1e-9 < 5.0):
            try:
                segment           = self.pushed_segments.pop(0)
                size              = segment["len_segment"]
                fragment_duration = segment["dur_segment"]
                data              = segment["data"]
                buf               = Gst.Buffer.new_wrapped(data)
                buf.duration      = int(fragment_duration * 1e9)
                # buf.pts         = self.ind * buf.duration
                #debug(DEBUG, '%s pushData: pushed %s of data (duration= %ds) for level %s', self,
                    #format_bytes(len(data)),
                    #fragment_duration,
                    #level)
                # print "QUEUED TIME: " + str(self.getQueuedTime()) + "\nIS PLAYING: " + str(self.PLAYING)
                self.pipeline.get_by_name('src').emit('push-buffer', buf)
                del buf
                del segment
                
                self.queue['sec'] = max(0, self.queue['sec'] - fragment_duration)
                self.queue['byte'] = max(0, self.queue['byte'] - floor(size))
                
            except Exception as e:
                traceback.print_exc()
                Gtk.main_quit
                self.stop()
                
        elif (self.status == self.PLAYING and self.GstQueue.get_property('current-level-time') * 1e-9 == 0.0):
            self.pipeline.set_state(Gst.State.PAUSED)
            self.status = self.PAUSED
            self.emit('status-changed')
                
        

    def onRunning(self):
        self.checkGstbuffer()
        if (self.status == self.PLAYING):
            self.playtime += 0.1
            
        # should be calculated as following but all other calculations in 
        # TAPAS360 are done wrt fragment_duration sent by manifest and not from actual chunk value
        #if (self.status == self.PLAYING):
            #self.playtime = self.pipeline.query_position(Gst.Format.TIME)[1] * 10 ** -9
            
        #print(self.pipeline.query_duration(Gst.Format.TIME)[1] * 10 ** -9)#convert into second
            
        #print("Playback time: {0!s}, Duration: {1!s}".format(self.playtime, self.video_duration))
        if (self.getQueuedTime() >= self.min_queue_time and self.status == self.PAUSED):
            self.pipeline.set_state(Gst.State.PLAYING)
            self.status = self.PLAYING
            self.emit('status-changed')
        elif (self.getQueuedTime() == 0 and self.status == self.PLAYING):
            self.pipeline.set_state(Gst.State.PAUSED)
            self.status = self.PAUSED
            self.emit('status-changed')
        elif (self.playtime > self.video_duration and self.getQueuedTime() == 0):
            # stream is finished, close all
            Gtk.main_quit
            self.stop()
        reactor.callLater(0.1, self.onRunning)

    def stop(self):
        BaseMediaEngine.stop(self)
        #
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline = None
        reactor.stop()

    def pushData(self, data, fragment_duration, level, view, caps_data):
        debug(DEBUG, '%s pushData: pushed %s of data for level %s', self, 
            format_bytes(len(data)),
            level)
        self.evicted_segment = 0
        self.checkGstbuffer()
        
        # check view change for playout buffer eviction
        if (view != self.current_view):
            # check if gstreamer has enough data (for limiting rebuffering events)
            self.checkGstbuffer()
            # flush playout buffer
            byte = 0
            sec  = 0
            self.evicted_segment = len(self.pushed_segments)
            for segment in self.pushed_segments:
                byte += segment["len_segment"]
                sec  += segment["dur_segment"]
                
            self.queue['byte']   -= byte
            self.queue['sec']    -= sec
            del self.pushed_segments
            self.pushed_segments  = []
            self.playtime        -= sec
            
            # set new current view
            self.current_view = view
        
        # fill playout buffer
        self.queue['byte'] +=len(data)
        self.queue['sec']  +=fragment_duration
        self.pushed_segments.append(dict(len_segment=len(data), dur_segment=fragment_duration, data=data))

    def _on_video_buffer(self, pad, buf):
        if isinstance(buf, Gst.Buffer):
            buf.set_caps(self.video_caps)
        return True

    def getQueuedTime(self):
        #print("Queue time: {0!s}".format(self.queue['sec']))
        #print("Buffer time: {0!s}".format(self.GstQueue.get_property('current-level-time') * 1e-9))
        #print("Chunks: {0!s}".format(len(self.pushed_segments)))
        return round(self.queue['sec'], 3) + self.GstQueue.get_property('current-level-time') * 1e-9

    def getQueuedBytes(self):
        return self.queue['byte'] + self.GstQueue.get_property('current-level-bytes')

    def gstMessageHandler(self, bus, message):
        debug(DEBUG, '%s gstMessageHandler: %s',self, Gst.message_type_get_name(message.type))
        
        if (message.type == Gst.MessageType.ELEMENT):
            # parse element message
            if message.get_structure().get_name() == "prepare-window-handle":
                # this work for xvimagesink
                #print('----------> prepare-window-handle')
                self.sink = message.src
                self.sink.set_property("force-aspect-ratio", True)
                self.sink.set_window_handle(self.wnd_handler.get_window().get_xid())
            elif message.get_structure().get_name() == "have-window-handle":
                pass 
                #print('----------> have-window-handle - XWindowID:' + str(message.get_structure().get_value('window-handle')))
                #self.sink.set_window_handle(self._wnd_hnd)
        #elif (message.type == Gst.MessageType.STATE_CHANGED):
            ## parse state_changed message
            #print (message.parse_state_changed())
            ##if (Gst.Element.state_get_name(message.type) == ):
                
        
    def updateShaderPosition(self):
        pitch_angle = self.HMDEmulator.getPitchAngle()
        self.uniforms_pitch_angle_u = GObject.Value(GObject.TYPE_FLOAT, pitch_angle[0])
        self.uniforms_pitch_angle_v = GObject.Value(GObject.TYPE_FLOAT, pitch_angle[1])
        shader = self.pipeline.get_by_name('glshader')
        
        struct_uniform = Gst.Structure.new_empty("uniforms")
        struct_uniform.set_value("pitch_angle_u", self.uniforms_pitch_angle_u)
        struct_uniform.set_value("pitch_angle_v", self.uniforms_pitch_angle_v)
        struct_uniform.fixate()
        shader.set_property("uniforms", struct_uniform)
        
        reactor.callLater(0.1, self.updateShaderPosition)


    def createGtkWindow(self):
        self.window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        self.window.connect("destroy", Gtk.main_quit)
        #self.window.connect("delete-event", self.stop)
        self.window.set_default_size(1920, 1080)
        self.window.set_title("TAPAS360 PLAYER")

        self.wnd_handler = Gtk.DrawingArea()
        #self.wnd_handler.set_double_buffered(True)
        self.window.add(self.wnd_handler)

        self.window.show_all()
        self.window.realize()
        Gtk.main()

    def setViews(self, n_views):
        self.n_views = n_views
        
    def getNextVideoSegmentToBeFetched(self, currentIndex):
        return currentIndex + 1 - self.evicted_segment
    
    def getScaledSideWidth(self):
        return self.side_scaled
        
    def getOriginalSideWidth(self):
        return self.side_original
    
    def setScaledSideWidth(self, side_scaled):
        self.side_scaled = side_scaled
        
    def setOriginalSideWidth(self, side_original):
        self.side_original = side_original
