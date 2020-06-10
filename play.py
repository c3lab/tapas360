#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Copyright (c) Giuseppe Ribezzo <giuseppe.ribezzo@poliba.it>
# Copyright (c) Luca De Cicco <luca.decicco@poliba.it>

# This file may be distributed and/or modified under the terms of
# the GNU General Public License version 3 as published by
# the Free Software Foundation.
# This file is distributed without any warranty; without even the implied
# warranty of merchantability or fitness for a particular purpose.
# See "LICENSE" in the source distribution for more information.
import os, sys, csv
import traceback
from twisted.python import usage, log


class Options(usage.Options):
    optParameters = [
        ('controller', 'a', 'conventional', 'Adaptive Algorithm [conventional|max|bytes|bba0]'),
        ('view_controller', 'b', 'conventional', 'Viewport Adaptive Algorithm [conventional]'),
        ('url', 'u', 'http://devimages.apple.com/iphone/samples/bipbop/bipbopall.m3u8',
         'The playlist url. It determines the parser for the playlist'),
        ('media_engine', 'm', 'gst', 'Player type [gst|nodec|fake]'),
        ('log_sub_dir', 'l', None, 'Log sub-directory'),
        ('stress_test', 's', False, 'Enable stress test. Switch level for each segment, cyclically.'),
        ('hmd_trace', 'f', 'hmd_trace.csv', 'position of the csv file which contains the user angles '),
        ('vr', 'r', False, 'Enable vr visualization'),
        ('save_chunks', 'k', False, 'Save downloaded video chunks')
    ]


options = Options()
try:
    options.parseOptions()
except Exception as e:
    pass
    #print '%s: %s' % (sys.argv[0], e)
    #print '%s: Try --help for usage details.' % (sys.argv[0])
    #sys.exit(1)


def select_player():
    # try:
    log.startLogging(sys.stdout)

    persistent_conn = False
    check_warning_buffering = True

    # vr
    HMDEmulator = None
    vr=options['vr']
    if (vr and vr.startswith('T')):
        vr = True
        from hmdEmulator.HMDEmulator import HMDEmulator
        hmd_trace = options['hmd_trace']
        HMDEmulator = HMDEmulator(hmd_trace)
        
    else:
        vr = False
       
    
    save_chunks=options['save_chunks']
    if (save_chunks and save_chunks.startswith('T')):
        save_chunks = True
    else:
        save_chunks = False

    # MediaEngine
    if options['media_engine'] == 'gst':
        # gst_init()
        from media_engines.GstMediaEngine import GstMediaEngine
        media_engine = GstMediaEngine(decode_video=True, vr=vr, HMDEmulator=HMDEmulator)
    elif options['media_engine'] == 'nodec':
        # gst_init()
        from media_engines.GstMediaEngine import GstMediaEngine
        media_engine = GstMediaEngine(decode_video=False, vr=vr, HMDEmulator=HMDEmulator)
    elif options['media_engine'] == 'fake':
        from media_engines.FakeMediaEngine import FakeMediaEngine
        media_engine = FakeMediaEngine()
    else:
        print('Error. Unknown Media Engine')
        sys.exit()

    from twisted.internet import reactor

    # Controller
    if options['controller'] == 'conventional':
        from controllers.ConventionalController import ConventionalController
        controller = ConventionalController()
    else:
        print('Error. Unknown Control Algorithm')
        sys.exit()

    if not options['log_sub_dir']:
        log_sub_dir = options['controller']
    else:
        log_sub_dir = options['log_sub_dir']

        # View Controller
    if options['view_controller'] == 'conventional':
        from viewControllers.ConventionalViewController import ConventionalViewController
        view_controller = ConventionalViewController()
    else:
        print('Error. Unknown Viewport Control Algorithm')
        sys.exit()

    # Parser
    url_playlist = options['url']

    if ".mpd" in url_playlist:
        from parsers.DASH_mp4Parser import DASH_mp4Parser
        parser = DASH_mp4Parser(url_playlist)
    elif ".m3u8" in url_playlist:
        from parsers.HLS_mpegtsParser import HLS_mpegtsParser
        parser = HLS_mpegtsParser(url_playlist)
    else:
        print('Error. Unknown Parser')
        sys.exit()

    # set max_buffer_time
    if options['controller'] == 'bba0':
        mbt = 240
    else:
        mbt = 80

    # StartPlayer
    from TapasPlayer import TapasPlayer
    player = TapasPlayer(controller=controller, view_controller=view_controller, parser=parser,
                         media_engine=media_engine,
                         log_sub_dir=log_sub_dir, log_period=0.1,
                         max_buffer_time=mbt,
                         inactive_cycle=1, initial_level=1,
                         use_persistent_connection=persistent_conn,
                         check_warning_buffering=check_warning_buffering,
                         stress_test=options['stress_test'],
                         HMDEmulator=HMDEmulator,
                         vr=vr,
                         save_chunks=save_chunks
                         )
    print('Ready to play')

    # try:
    player.play()
    # except Exception, e:
    #    print(">>>>>>>>>>>> EXCEPTION: " + str(e))
    #    sys.exit(1)#HARD, better to do return

    try:
        reactor.run()
    except Exception as e:
        print(str(e))
        traceback.print_exc()
        pass




if __name__ == '__main__':
    try:
        select_player()
    except Exception as e:
        print(str(e))
        traceback.print_exc()
        sys.exit()
