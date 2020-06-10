#!/usr/bin/env python
# -*- Mode: Python -*-
# -*- encoding: utf-8 -*-
# Copyright (c) Vito Caldaralo <vito.caldaralo@gmail.com>
# Copyright (c) Luca De Cicco <luca.decicco@poliba.it>

# This file may be distributed and/or modified under the terms of
# the GNU General Public License version 3 as published by
# the Free Software Foundation.
# This file is distributed without any warranty; without even the implied
# warranty of merchantability or fitness for a particular purpose.
# See "LICENSE" in the source distribution for more information.
import os, sys
from twisted.internet import defer, reactor
from pprint import pformat
from utils_py.util import debug, getPage
from .BaseParser import BaseParser
from TapasPlayer import TapasPlayer 

DEBUG = 2
USER_AGENT = 'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10'

def hasGetIndex(url):
    if url.startswith("http"):
        url = url.split('/')[5]
    return int(url.split('_')[1].split('.')[0])

#http://quavstreams.quavlive.com/hls/f4b49e3aa1127db19e46e98dab809072.m3u8

class HLS_mpegtsParser(BaseParser):
    
    def __init__(self,url,playlist_type='HLS',video_container='MPEGTS'):
        super(HLS_mpegtsParser, self).__init__(url, playlist_type, video_container)
        self.start_time = 0
        self.views      = 1

    def __repr__(self):
        return '<HLS_mpegtsParser-%d>' %id(self)
    
    def getLevels(self):
        return self.levels

    def getViews(self):
        return self.views

    def loadPlaylist(self):
        self.levels         = []
        self.playlists      = []
        self.caps_demuxer   = []
        
        def got_page(data, factory):
            debug(DEBUG, '%s loadHlsPlaylist from %s:\n%s', self, factory.url.decode('utf-8'), data)
            view_flag   = False
            is_live     = False
            urls        = []
            id_level    = 0
            id_view     = 0
            i           = 0
            j           = 0
            playlist    = None
            data        = data.decode('utf-8').replace("\n\n","")


            for line in data.split('\n'):
                line = line.strip()
                line = line.replace(", ",",")
                url  = None

                #print line
                if line.startswith('#EXT-X-STREAM-INF:'):
                    id_view = 0
                    line    = line.replace('#EXT-X-STREAM-INF:', '')
                    vr      = None
                    res     = None
                    for field in line.split(','):
                        if field.startswith('BANDWIDTH='):
                            field = field.replace('BANDWIDTH=', '')
                            vr = int(field)/8.  #in B/s
                        elif field.startswith('RESOLUTION='):
                            field = field.replace('RESOLUTION=', '')
                            res = field
                    self.levels.append(dict(rate=vr,resolution=res))
                    continue

                    # Case of view playlist
                elif line.startswith('#EXT-X-MEDIA:'):
                    view_flag = True
                    central_width = -1
                    side_width    = -1
                    v_scale       = -1
                    yaw_angle     = -1
                    line = line.replace('#EXT-X-STREAM-INF:', '')
                    for field in line.split(','):
                        if field.startswith('URI='):
                            field = str(field.replace('URI=', '')).replace('"','')
                            url = os.path.join(os.path.dirname(factory.url.decode('utf-8')), field)
                        elif field.startswith('CENTRAL_WIDTH='):
                            field = field.replace('CENTRAL_WIDTH=', '')
                            central_width = int(field)
                        elif field.startswith('SIDE_WIDTH='):
                            field = field.replace('SIDE_WIDTH=', '')
                            side_width = int(field)
                        elif field.startswith('V_SCALE='):
                            field = field.replace('V_SCALE=', '')
                            v_scale = int(field)
                        elif field.startswith('ROTATION='):
                            field = field.replace('ROTATION=', '')
                            yaw_angle = int(field)
                            
                            """ elif field.startswith('DEFAULT='):
                            #TODO
                            print "TODO" """
                    if (central_width == -1 or side_width == -1 or v_scale == -1 or yaw_angle == -1):
                        sys.exit(0)
                    
                    cur  = dict(url   = url,
                        is_live       = is_live,
                        segments      = [], 
                        start_index   = -1, 
                        end_index     = -1,
                        type          = "level", 
                        duration      = 0.0, 
                        view          = id_view, 
                        level         = id_level,
                        central_width = central_width,
                        side_width    = side_width,
                        v_scale       = v_scale,
                        yaw_angle     = yaw_angle)
                    self.playlists.append(cur)
                    id_view = id_view + 1
                    self.views = max(self.views, id_view)
                    continue

                elif not line.startswith('#'):
                    """ if len(urls) != 0: """
                    if not view_flag:
                        if not line.startswith('http') and line != '':
                            url = os.path.join(os.path.dirname(factory.url.decode('utf-8')), line)
                            cur  = dict(url = url,
                                is_live = is_live,
                                segments    = [], 
                                start_index = -1, 
                                end_index   = -1,
                                type        = "level", 
                                duration    = 0.0, 
                                view        = id_view, 
                                level       = id_level)
                            self.playlists.append(cur)
                            id_level = id_level + 1
                            continue
                        else:
                            id_level = id_level + 1
                            continue
                    else:
                        id_level = id_level + 1
                        continue
                else:
                    continue
                
            #if self.cur_level >= len(self.playlists):
            #    self.cur_level = max(self.cur_level, len(self.playlists)-1)
            deferredList = []
            for i in range(0, len(self.levels)):
                for j in range(0, self.views):
                    print("i: ", i, "j: ", j)
                    deferredList.append(self.updateLevelSegmentsList(i,j))
            dl = defer.DeferredList(deferredList)
            def _on_done(res):
                self.deferred.callback(True)    
            dl.addCallback(_on_done)
        # error handling
        def got_error(e):
            debug(0, '%s loadHlsPlaylist error: %s', self, e)
        #
        d = getPage(self.url, agent=USER_AGENT)
        d.deferred.addCallback(got_page, d)
        d.deferred.addErrback(got_error)

    def createEmptyPlaylist(self, playlist):
        if playlist["segments"]:
            del playlist["segments"]
            
        playlist["segments"]    = {}
        playlist["start_index"] = -1
        playlist["end_index"]   = -1
        playlist["duration"]    = 0.0
        return playlist

    def getSinglePlaylist(self, level, view):
        playlist = None
        for p in self.playlists:
            if p['view'] == view and p['level'] == level:
                playlist = p
        return playlist

    
    def updateLevelSegmentsList(self, level, view):

        '''Updater playlist for current level'''
        playlist = self.getSinglePlaylist(level, view)
        self.playlists.remove(playlist)
        
        playlist = self.createEmptyPlaylist(playlist)    #Only for VOD and Live. Not for Live+REC 
        c = defer.Deferred()
        debug(DEBUG-1, '%s updateLevelSegmentsList: %s', self, playlist['url'])
        
        def got_init(data, factory):
            debug(DEBUG+1, 'updateLevelSegmentsList: %s', data)
            #print str(playlist)
            playlist["initSegment"] = data
            
        
        # page callback
        def got_playlist(data, factory):
            debug(DEBUG+1, 'updateLevelSegmentsList: %s', data)
            cur_index = start_index = 0
            # FIXME for live streams
            #cur_index = playlist.get('end_index', -1) + 1
            for line in data.decode('utf-8').split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith('#EXT-X-TARGETDURATION:'):
                    # FIXME: THIS LABEL MEANS MAXIMUM SEGMENT DURATION, EQUALS TO THE FOLLOWING IN CBR CASE
                    self.fragment_duration = float(line.replace('#EXT-X-TARGETDURATION:', ''))
                    #setIdleDuration(fragment_duration)
                
                elif line.startswith('#EXTINF:'):
                    line = line.replace('#EXTINF:', '')
                    segment_duration = float(line.split(',')[0])
                    # FIXME: THIS LABEL MEANS SEGMENT DURATION, EQUALS TO THE PREVIOUS IN CBR CASE
                    self.fragment_duration = segment_duration
                    
                elif line.startswith('#EXT-X-MEDIA-SEQUENCE:'):
                    line = line.replace('#EXT-X-MEDIA-SEQUENCE:', '')
                    cur_index = start_index = int(line)
                    
                elif line.startswith('#EXT-X-MAP:'):
                    # line pointing to init file in fmp4 hls
                    line = line.replace('#EXT-X-MAP:', '')
                    for field in line.split(','):
                        if field.startswith('URI='):
                            # hls mp4
                            self.video_container = 'MP4'
                            
                            field               = str(field.replace('URI=', '')).replace('"','')
                            url                 = os.path.join(os.path.dirname(factory.url.decode('utf-8')), field)
                            playlist["initURL"] = url
                            #print("initURL PLAYLIST: " + str(playlist))
                            
                            # fetch init segment data
                            d = getPage(url, agent=USER_AGENT)
                            d.deferred.addCallback(got_init, d)
                            d.deferred.addErrback(got_error, d)
                            
                elif not line.startswith('#'):
                    try:
                        index       = hasGetIndex(line)
                    except Exception:
                        index       = cur_index
                        cur_index   += 1
                        
                    # first segments, set start_time
                    if len(playlist['segments']) == 0:
                        playlist['start_index'] = index
                        self.start_time = max(self.start_time, index*self.fragment_duration)
                        #playlist['duration'] = self.start_time
                    if index > playlist['end_index']:
                        if not line.startswith('http'):
                            line = os.path.join(os.path.dirname(factory.url.decode('utf-8')), line)
                            
                        _c = dict(url = line, byterange = '', dur = segment_duration)
                        playlist['segments'][index] = _c
                        playlist['end_index']       = index
                        playlist['duration']        += segment_duration
                elif line.startswith('#EXT-X-ENDLIST'):
                    """
                    You can't remove anything from the playlist when using the EVENT tag; 
                    you may only append new segments to the end of the file. 
                    New segments are added to the end of the file until the event has concluded, 
                    at which time the EXT-X-ENDLIST tag is appended. 
                    """
                    duration = playlist['duration']
                    #playlist['is_live'] = True 
                    playlist['is_live'] = False
                    
            self.playlists.append(playlist)
            #self.playlists[level] = playlist
            c.callback(1)
        # error handling
        def got_error(e, factory):
            debug(0, '%s updateLevelSegmentsList url: %s error: %s', self, factory.url.decode('utf-8'), e)
            reactor.callLater(self.fragment_duration*0.5, 
                self.updateLevelSegmentsList, level)
            
        d = getPage(playlist['url'], agent=USER_AGENT)
        d.deferred.addCallback(got_playlist, d)
        d.deferred.addErrback(got_error, d)
        return c
