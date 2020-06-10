# TAPAS-360°: a Tool for the Design and Experimental Evaluation of 360° Video Streaming Systems

TAPAS is a tool that allows rapid prototyping of Adaptive Streaming control algorithms.
If you are a developer and you want to design an test a new Adaptive Streaming control algorithm
you should check the documentation placed in the doc/ directory.

If you are a user and you want to experiment with the control algorithms made available
by TAPAS you can follow the instructions given below. 

## Installation 

For Ubuntu-based Linux distributions install the following building dependencies (see ``dependencies.txt``):

```
apt-get install --no-install-recommends python3-twisted
apt-get install --no-install-recommends python3-twisted-bin
apt-get install --no-install-recommends python3-twisted-core
apt-get install --no-install-recommends python3-twisted-web
apt-get install --no-install-recommends gstreamer1.0-plugins-*
apt-get install --no-install-recommends gstreamer1.0-tools
apt-get install --no-install-recommends gstreamer1.0-libav
apt-get install --no-install-recommends libgstreamer1.0-dev
apt-get install --no-install-recommends python3-gst-1.0
apt-get install --no-install-recommends python3-gobject
apt-get install --no-install-recommends python3-numpy
apt-get install --no-install-recommends python3-scipy
apt-get install --no-install-recommends python3-psutil
apt-get install --no-install-recommends gir1.2-gtk-3.0
```


## Building TAPAS-360° docker image

TAPAS-360° is shipped with easy-to-use scripts that help with building and running a docker image to perform experiments with the tool.

To build the tapas-360 docker image simply run:

```sh
./build_tapas360_dockerimage.sh
```

Then, use the helper script 

```sh
./run_tapas360_docker.sh
```

to run TAPAS-360°. Notice that the last script assumes you can run  ``docker`` without ``sudo`` (see the [Docker documentation](https://docs.docker.com/engine/install/linux-postinstall/)). 

## Usage

Play a default playlist: ::
    
    $ python3 play.py

Play a default playlist with a "conventional" adaptive controller: ::
    
    $ python3 play.py --controller conventional
    
Play a playlist specified by its URL: ::

    $ python3 play.py --url http://mysite.com/myplaylist.m3u8

Play a sample MPEG-DASH video: ::
    
    $ python3 play.py --url http://yt-dash-mse-test.commondatastorage.googleapis.com/media/car-20120827-manifest.mpd

Play an omnidirectional content: ::
Play a MPEG-DASH omnidirectional content (DASH playlist is courtesy of Bitmovin): ::
    
    $ python3 play.py --vr True --url https://bitmovin-a.akamaihd.net/content/playhouse-vr/mpds/105560.mpd

Play omnidirectional content using the provided "conventional" viewport adaptive strategy (HLS playlist is courtesy of Bitmovin): ::
    
    $ python3 play.py --vr True --view_controller conventional --url https://bitmovin-a.akamaihd.net/content/playhouse-vr/m3u8s/105560.m3u8

Play a playlist for logs, without decoding video: ::

	$ python3 play.py --media_engine nodec

Play a playlist with a fake player (emulated playout buffer and no decoding): ::

	$ python3 play.py --media_engine fake

Play only the highest quality of the playlist: ::

	$ python3 play.py --controller max

Player options: ::

	$ python3 play.py --help

Enable debug: ::
    
    $ DEBUG=2 python3 play.py


## Publicly available HMD dataset

TAPAS-360° allows to emulate the user's head position by reading a Comma Separated Values (.csv) file containing the angular data
jointly with a timestamp related to playback time. The format is simply

    time,alpha,beta,gamma

where:
* _time_ is the timestamp in seconds
* _alpha_ is the yaw angle in degrees
* _beta_ is the pitch angle in degrees
* _gamma_ is the roll angle in degrees

A list of publicly available datasets that can be easily used with TAPAS-360° includes:

1. http://dash.ipv6.enstb.fr/headMovements/
2. https://www.interdigital.com/data_sets/salient-360-dataset
3. https://github.com/V-Sense/VR_user_behaviour

## Documentation
Documentation can be build using ``sphinx``. To build the documentation in HTML format:

    cd docs/sphinx
	make html
	
The documentation will be made available in ``docs/sphinx/_build/html``.
