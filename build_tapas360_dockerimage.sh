#!/bin/bash

DOCKERFILE="FROM ubuntu:bionic

RUN apt-get update && \
    apt-get install -y --no-install-recommends apt-utils \
    python3-twisted \
    python3-twisted-bin \
    gstreamer1.0-plugins-* \
    gstreamer1.0-tools \
    gstreamer1.0-libav \
    gstreamer1.0-gl \
    gstreamer1.0-python3-plugin-loader \
    libgstreamer1.0-dev \
    python3-gst-1.0 \
    python3-gi gobject-introspection gir1.2-gtk-3.0 \
    python3-numpy \
    python3-scipy \
    python3-psutil && \
    apt-get clean
    
WORKDIR /python_code
CMD mkdir -p logs
ADD parsers /python_code/parsers
ADD media_engines /python_code/media_engines
ADD controllers /python_code/controllers
ADD viewControllers /python_code/viewControllers
ADD hmdEmulator /python_code/hmdEmulator
ADD utils_py /python_code/utils_py
COPY *.py /python_code/
COPY *.csv /python_code/

RUN groupadd -g $(id -g $(users)) $(users)
RUN useradd -d ${HOME} -s /bin/bash -m $(users) -u $(id -u $(users)) -g $(id -g $(users))
USER $(users)
ENV HOME ${HOME}"

echo "${DOCKERFILE}" | docker build -t tapas-360 -f - . 
