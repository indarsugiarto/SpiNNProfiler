TEMPLATE = app
CONFIG += console c++11
CONFIG -= app_bundle
CONFIG -= qt

SOURCES += \
    profiler.c

INCLUDEPATH += /opt/spinnaker_tools_134/include

DISTFILES += \
    Makefile \
    profiler.ybug \
    stopProfiler.py \
    readReport.py \
    startRptStream.py \
    stopRptStream.py \
    setFreq.py

HEADERS += \
    profiler.h
