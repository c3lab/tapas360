ViewController
==============

The ViewController is a new component that immersive video streaming systems are required to implement. Its goal is to select the best viewpoint representation, among those advertised in the manifest files, based on the user's head position reported by the HMD device. 

The implementation of the ViewController requires that the BaseViewController class be inherited, and the definition of the getView() method, which implements the viewpoint selection strategy. Such information could be useful for viewport adaptive control algorithms based on saliency maps.

The default ``feedback`` dictionary, that ``Tapas360Player`` updates before calling any new ``getView()``, is presented in the following table:

+------------------------+------------------------+
| Key                    | Unit                   |
+========================+========================+
| yaw_angles             | degrees                |
+------------------------+------------------------+
| threshold_angle        | degrees                |
+------------------------+------------------------+
| delta                  | degrees                |
+------------------------+------------------------+
| n_views                | [ ]                    |
+------------------------+------------------------+
| cur_view               | [ ]                    |
+------------------------+------------------------+

Base class methods
------------------

.. autoclass:: viewControllers.BaseViewController.BaseViewController
   :members:

Rapid prototyping
-----------------

Now we consider an example showing how a viewpoint adaptive controller can be implemented. To the purpose we consider a simple controller, named *ConventionalViewController*, that is described in details `here`_.

.. _here: http://arxiv.org/pdf/1305.0510.pdf

.. code-block:: python
   :linenos:
	
    class ConventionalViewController(BaseViewController):

        def __init__(self):
            super(ConventionalViewController, self).__init__()
            

        def __repr__(self):
            return '<ConventionalViewController-%d>' %id(self)
        
        
        def getView(self, cur_view, cur_angles):
            alpha      = cur_angles[0]
            new_view   = cur_view
            roi_center = self.feedback['yaw_angles'][cur_view]
            
            if (abs(roi_center - alpha) > (self.feedback['threshold_angle'] + self.feedback['delta'])):
                new_view = int((cur_view - math.copysign(1.0, roi_center - alpha)) % self.feedback['n_views'])
            return new_view

After that, we associate a string to this controller (e.g 'conventional') and update the options and imports in ``play.py`` to use this controller with TAPAS-360° from command line.
