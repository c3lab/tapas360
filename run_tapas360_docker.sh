#!/bin/bash

echo "

----------------------------------------------------------------------------
| Running TAPAS-360° docker container. Notice that logs will be stored in    |
| the host filesystem and will be available after stopping the container in  |
|  the 'logs/' directory                                                     |
 ----------------------------------------------------------------------------
 
"

docker run --user $(users) --network host -v /tmp/.X11-unix:/tmp/.X11-unix:rw --volume="$XAUTH:$XAUTH" -env="XAUTHORITY=$XAUTH" -e DISPLAY=$DISPLAY -v "$PWD/logs":/python_code/logs --rm -it --entrypoint bash tapas-360:latest
