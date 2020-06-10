Parser
======

The main task of a parser is to populate and update the ``playlists`` data structure, which is used by ``Tapas360Player``.

The ``playlists`` data structure is a list of dictionaries, one for each available video representation. This data structure is populated with the information retrieved by the Manifest. The dictionary has to include the following keys:
    1) ``url``: the video level base URL;
    2) ``is_live``: true if the video is a live stream;
    3) ``segments``: a list of dictionaries. Each dictionary contains: the ``segment_url``; the ``segment_duration``; and the ``byterange``, when the video segmentation is logic.
    4) ``start_index``: index of the first chunk to be downloaded by the *Downlaoder*;
    5) ``end_index``: index of the last chunk of the current playlist;
    6) ``duration``: the duration (in seconds) of the playlist;
    7) ``view``: the viewpoint identifier referring to the specific viewpoint representation;
    8) ``level``: the level identifier referring to the specific level.
    
The ``levels`` data structure corredates the information contained in ``playlists`` with additional information about the video levels. It is a list of dictionaries, one for each available video level. The dictionary has to include the following keys: 
	1) ``rate``: is the encoding rate of the video level measured in bytes/s; 
	2) ``resolution``: is the video level resolution.
	
The ``views`` data structure corredates the information contained in ``playlists`` with additional information about the viewpoint representations. It is a list of dictionaries, one for each available viewpoint representation. In this way, it is possible to reflect accurately the information contained in the parsed Manifest.
As an example, optional fields can be defined specifically for allowing the immersive content management. In the current implementation, the following fields are added, reflecting the immersive video management as described in detail `here`_.   
    1) ``central_width``: the width (in pixel) of the RoI contained by the viewpoint representation;
    2) ``side_width``: the width (in pixel) on the non-RoI area;
    3) ``yaw_angle``: the yaw angle at which the RoI is centered. 

.. _here: https://onlinelibrary.wiley.com/doi/full/10.1002/itl2.118

Base class methods
------------------

.. autoclass:: parsers.BaseParser.BaseParser
   :members:
