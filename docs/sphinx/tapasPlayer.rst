Tapas360Player
==============

.. image:: _static/tapas-workflow.png
   :scale: 40 %
   :alt: tapas-workflow
   :align: center

`Tapas360Player`_ is the central module that deals with orchestrating the operations of all TAPAS-360° components. This module implements the player logic and updates the log files that are populated during the experiments and that can be used in the post-processing phase for analyzing the performance of the implemented algorithms. The communication between modules is implemented through the exchange of a feedback dictionary. This dictionary contains all the pieces of information that are useful for performing the experiments and to pass data from one module to the other.
The ``play()`` method is used to start the experiment and manages the user interaction, initializes the feedback dictionary, and orchestrates the operational flow of the various modules composing TAPAS-360°.
   
   
When the `Tapas360Player`_'s ``play()`` method is issued the `Parser`_ downloads the manifest and populates the ``playlists`` dictionary.
At this point two concurrent threads are started: 1) a thread that fills the playout buffer by fetching the video segments from the HTTP server and 2) a thread that drains the playout buffer to play the videostream.
Let us now focus on the thread that fills the buffer. The following operations are executed in a loop until the last video segment has been played:
	1) The ``Downloader`` fetches from the HTTP server the current segment at the selected video level. 
	2) When the download is completed the following operations are performed:
		(a) The segment is enqueued in the playout buffer handled by the `MediaEngine`_ component.
		(b) The player gets from the `MediaEngine`_ the queue length and other feedbacks and builds the player ``feedback`` dictionary with this information. Then player ``feedback`` is passed to the `QualityController`_.
		(c) The `QualityController`_ computes two values: 1) the control action, i.e. the video level rate of the next segment to be downloaded; 2) the idle duration, possibly equal to zero, that is the time interval that has to elapse before the next video segment can be fetched.
		(d) In the case of immersive contents, the player gets from the `HMDEmulator`_ the current user's head position and other feedbacks and adds this information to the player ``feedback`` dictionary. Then player ``feedback`` is passed to the `ViewController`_.
		(e) Then, `ViewController`_ uses the ``feedback`` dictionary just received to select the viewpoint representation to be downloaded.
		(f) If decoding capabilities are enabled, `Tapas360Player`_ continously updates the `MediaEngine`_ component with the piece of information about the user's head position and the currently visualized viewpoint representation.
	3) A timer of duration ``idle duration`` is started. When the timer expires the loop repeats from step 1.
Finally, the thread draining the playout buffer is handled by the `MediaEngine`_ that decodes the compressed video frames, and plays the raw video.

.. _Parser: parser.html
.. _MediaEngine: mediaEngine.html
.. _QualityController: controller.html
.. _ViewController: viewController.html
.. _HMDEmulator: hmdEmulator.html

Methods
-------

.. autoclass:: TapasPlayer.TapasPlayer
   :members:
