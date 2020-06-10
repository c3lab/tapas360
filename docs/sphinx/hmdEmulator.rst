HMDEmulator
===========

Immersive video contents are 360° videos capturing the real scene in all directions simultaneously. An HMD gives the users the possibility to explore the recorded environment, tracking the head user position time by time. Tracking is possible by means of devices such as gyroscope and accelerometer, catching the viewer's movement. Usually, to conduct performance evaluation on the designed Viewpoint Adaptive algorithm, researchers have to buy the real equipment and involve real viewer into the experimentation. 

In TAPAS-360, the design of ViewController requires in input to receive the current angular position from an HMD to perform the viewpoint selection strategy. HMDEmulator is the module that takes care of emulating the reading of the accelerometer data.

The implementation of the HMDEmulator requires the implementation of the getCurrentViewAngle() method, which accepts the playback timestamp and returns the angular data about the current position of the user's head. Such information could be useful for viewport adaptive control algorithms based on saliency maps. The emulation of the user's head movement is obtained by reading a Comma-Separated Values (.csv) file which contains the angular data relating to the user's head movement for each millisecond of playback. Such information could be useful for viewport adaptive control algorithms based on saliency maps. In this way, publicly available datasets can be easily integrated. This method has the undoubted convenience in the massive experimental tests of not having to use a viewer.


Base class methods
------------------

.. autoclass:: hmdEmulator.HMDEmulator.HMDEmulator
   :members:

Rapid prototyping
-----------------

Now we consider an example, named *HMDEmulator*, showing how to simply emulate tracking the user head's position.

.. code-block:: python
   :linenos:
	
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
        cur_angles = self.getCurrentAngles(time.time() - self.t_experiment_started)
        
        self.pitch_angle[0] = math.radians(cur_angles[0] / math.pi)
        self.pitch_angle[1] = math.radians(cur_angles[1] / math.pi)
        self.pitch_angle[2] = math.radians(cur_angles[2] / math.pi)
        
        reactor.callLater(sampling_time, self.updateHMDPosition)
        
        
    def getPitchAngle(self):
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
        # Search the idx
        timestamp = timestamp % np.amax(self.t)
        idx = (np.abs(self.t - timestamp)).argmin()
        return idx

    def getCurrentAngles(self, time):
        idx = self.get_time_idx(time)
        return [self.alpha[idx], self.beta[idx], self.gamma[idx]]


