################################################################################
# Copyright (c) 2019, NVIDIA CORPORATION. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
################################################################################

#!/usr/bin/env python

import json
import numpy as np
import statistics
import sys
sys.path.append('../')
import platform
import configparser
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
from common.is_aarch_64 import is_aarch64
from common.bus_call import bus_call
import pyds

PGIE_CLASS_ID_VEHICLE = 0
PGIE_CLASS_ID_BICYCLE = 1
PGIE_CLASS_ID_PERSON = 2
PGIE_CLASS_ID_ROADSIGN = 3

########## Gate Class ##########

class Gate:
    def __init__(self, vehicle_id, x_smallest, x_largest, y_smallest, y_largest, frames_list=[], x_list=[], y_list=[], xc_list=[], yc_list=[], lane=[]):
        self.vehicle_id = vehicle_id
        self.x_smallest = x_smallest
        self.x_largest = x_largest
        self.y_smallest = y_smallest
        self.y_largest = y_largest
        self.frames_list = frames_list
        self.x_list = x_list
        self.y_list = y_list
        self.xc_list = xc_list
        self.yc_list = yc_list
        self.lane = lane

########## Gate Class ##########

stream_width = 1920     # horizontal scale of inference geometry as opposed to the width of input stream
stream_height = 1080    # vertical scale of inference geometry as opposed to the height of input stream
total_cars = 0  # total cars detected in the stream, i.e., total cars assigned unique tracking IDs
x11 = 540     # leftmost 'vertical' segment top
x12 = 840     
x13 = 1110
x14 = 1410
x21 = 340
x22 = 760
x23 = 1170     
x24 = 1610     # rightmost 'vertical' segment bottom
y1 = 384    # optimal range filter start
y2 = 633    # optimal range filter end
gate_list = []  # list for the detected vehicles and their frames

def osd_sink_pad_buffer_probe(pad, info, u_data):
    
    # Intiallizing object counter with 0.
    obj_counter = {
        PGIE_CLASS_ID_VEHICLE: 0,
        PGIE_CLASS_ID_PERSON: 0,
        PGIE_CLASS_ID_BICYCLE: 0,
        PGIE_CLASS_ID_ROADSIGN: 0
    }
    
    num_rects = 0
    global total_cars  # explicit mention of the global variable inside the function
    global x11, x12, x13, x14, x21, x22, x23, x24   # lanes
    gst_buffer = info.get_buffer()
    if not gst_buffer:
        print("Unable to get GstBuffer ")
        return

    # Retrieve batch metadata from the gst_buffer
    # Note that pyds.gst_buffer_get_nvds_batch_meta() expects the
    # C address of gst_buffer as input, which is obtained with hash(gst_buffer)
    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
    l_frame = batch_meta.frame_meta_list
    while l_frame is not None:
        try:
            # Note that l_frame.data needs a cast to pyds.NvDsFrameMeta
            # The casting is done by pyds.glist_get_nvds_frame_meta()
            # The casting also keeps ownership of the underlying memory
            # in the C code, so the Python garbage collector will leave
            # it alone.
            frame_meta = pyds.glist_get_nvds_frame_meta(l_frame.data)
        except StopIteration:
            break

        frame_number = frame_meta.frame_num
        num_rects = frame_meta.num_obj_meta
        l_obj = frame_meta.obj_meta_list
        while l_obj is not None:
            try:
                # Casting l_obj.data to pyds.NvDsObjectMeta
                obj_meta = pyds.glist_get_nvds_object_meta(l_obj.data)
                if obj_meta.class_id == PGIE_CLASS_ID_VEHICLE:
                    if obj_meta.rect_params.top >= y1 and obj_meta.rect_params.top <= y2:
                        car_found = 0
                        for x in gate_list:
                            if x.vehicle_id == obj_meta.object_id:
                                x.frames_list.append(frame_number)
                                x.x_list.append(obj_meta.rect_params.left)
                                x.y_list.append(obj_meta.rect_params.top)
                                x.xc_list.append(int(obj_meta.rect_params.left + (obj_meta.rect_params.width / 2)))
                                x.yc_list.append(int(obj_meta.rect_params.top + (obj_meta.rect_params.height / 2)))
                                x.x_smallest = min(x.x_list)
                                x.x_largest = max(x.x_list)
                                x.y_smallest = min(x.y_list)
                                x.y_largest = max(x.y_list)
                                x_center = int(obj_meta.rect_params.left + (obj_meta.rect_params.width / 2))
                                y_center = int(obj_meta.rect_params.top + (obj_meta.rect_params.height / 2))
                                if x_center > min(x13, x23):
                                    x.lane.append('fast')
                                elif x_center > min(x12, x22):
                                    x.lane.append('medium')
                                elif x_center > min(x11, x21):
                                    x.lane.append('slow')
                                else:
                                    x.lane.append('shoulder')
                                car_found = 1
                                break
    
                        if car_found == 0:
                            frame_temp_list = []
                            frame_temp_list.append(frame_number)
                            x_temp_list = []
                            x_temp_list.append(obj_meta.rect_params.left)
                            y_temp_list = []
                            y_temp_list.append(obj_meta.rect_params.top)
                            xc_temp_list = []
                            xc_temp_list.append(int(obj_meta.rect_params.left + (obj_meta.rect_params.width / 2)))
                            yc_temp_list = []
                            yc_temp_list.append(int(obj_meta.rect_params.top + (obj_meta.rect_params.height / 2)))
                            x_center = int(obj_meta.rect_params.left + (obj_meta.rect_params.width / 2))
                            y_center = int(obj_meta.rect_params.top + (obj_meta.rect_params.height / 2))
                            lane_temp_list = []
                            if x_center > min(x13, x23):
                                lane_temp_list.append('fast')
                            elif x_center > min(x12, x22):
                                lane_temp_list.append('medium')
                            elif x_center > min(x11, x21):
                                lane_temp_list.append('slow')
                            else:
                                lane_temp_list.append('shoulder')
                            gate_list.append(Gate(obj_meta.object_id, min(x_temp_list), max(x_temp_list), min(y_temp_list), max(y_temp_list), frame_temp_list, x_temp_list, y_temp_list, xc_temp_list, yc_temp_list, lane_temp_list))
                     
                    if obj_meta.object_id > total_cars:
                        total_cars = obj_meta.object_id  # total cars assigned unique tracing IDs
                  
                    print('Vehicle ID = ', obj_meta.object_id, ', Frame Number = ', frame_number, ', Top X = ', obj_meta.rect_params.left,
                          ', Top Y = ', obj_meta.rect_params.top, ', Width = ', obj_meta.rect_params.width, ', Height = ', obj_meta.rect_params.height)
                    
            except StopIteration:
                break
            obj_counter[obj_meta.class_id] += 1
            try:
                l_obj = l_obj.next
            except StopIteration:
                break

        # Acquiring a display meta object. The memory ownership remains in
        # the C code so downstream plugins can still access it. Otherwise
        # the garbage collector will claim it when this probe function exits.
        display_meta = pyds.nvds_acquire_display_meta_from_pool(batch_meta)
        display_meta.num_labels = 1
        py_nvosd_text_params = display_meta.text_params[0]
        
        # Setting display text to be shown on screen
        # Note that the pyds module allocates a buffer for the string, and the
        # memory will not be claimed by the garbage collector.
        # Reading the display_text field here will return the C address of the
        # allocated string. Use pyds.get_string() to get the string content.
        py_nvosd_text_params.display_text = "Frame Number={} Number of Objects={} Vehicles in Frame={} Total Objects in Stream={}".format(
            frame_number, num_rects, obj_counter[PGIE_CLASS_ID_VEHICLE], total_cars)

        # Now set the offsets where the string should appear
        py_nvosd_text_params.x_offset = 10
        py_nvosd_text_params.y_offset = 12

        # Font , font-color and font-size
        py_nvosd_text_params.font_params.font_name = "Serif"
        py_nvosd_text_params.font_params.font_size = 10
        # set(red, green, blue, alpha); set to White
        py_nvosd_text_params.font_params.font_color.set(1.0, 1.0, 1.0, 1.0)

        # Text background color
        py_nvosd_text_params.set_bg_clr = 1
        # set(red, green, blue, alpha); set to Black
        print(pyds.get_string(py_nvosd_text_params.display_text))
        pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)
        
        # Draw x11_x21
        py_nvosd_line_params = display_meta.line_params[0]
        py_nvosd_line_params.x1 = x11
        py_nvosd_line_params.y1 = y1
        py_nvosd_line_params.x2 = x21
        py_nvosd_line_params.y2 = y2
        py_nvosd_line_params.line_width = 5
        py_nvosd_line_params.line_color.set(0.0, 1.0, 0.0, 1.0)
        display_meta.num_lines = display_meta.num_lines + 1
        pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)
        x11 = py_nvosd_line_params.x1
        x21 = py_nvosd_line_params.x2
        
        # Draw x12_x22
        py_nvosd_line_params = display_meta.line_params[1]
        py_nvosd_line_params.x1 = x12
        py_nvosd_line_params.y1 = y1
        py_nvosd_line_params.x2 = x22
        py_nvosd_line_params.y2 = y2
        py_nvosd_line_params.line_width = 5
        py_nvosd_line_params.line_color.set(0.0, 1.0, 0.0, 1.0)
        display_meta.num_lines = display_meta.num_lines + 1
        pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)
        x12 = py_nvosd_line_params.x1
        x22 = py_nvosd_line_params.x2
        
        # Draw x13_x23
        py_nvosd_line_params = display_meta.line_params[2]
        py_nvosd_line_params.x1 = x13
        py_nvosd_line_params.y1 = y1
        py_nvosd_line_params.x2 = x23
        py_nvosd_line_params.y2 = y2
        py_nvosd_line_params.line_width = 5
        py_nvosd_line_params.line_color.set(0.0, 1.0, 0.0, 1.0)
        display_meta.num_lines = display_meta.num_lines + 1
        pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)
        x13 = py_nvosd_line_params.x1
        x23 = py_nvosd_line_params.x2
        
        # Draw x14_x24
        py_nvosd_line_params = display_meta.line_params[3]
        py_nvosd_line_params.x1 = x14
        py_nvosd_line_params.y1 = y1
        py_nvosd_line_params.x2 = x24
        py_nvosd_line_params.y2 = y2
        py_nvosd_line_params.line_width = 5
        py_nvosd_line_params.line_color.set(0.0, 1.0, 0.0, 1.0)
        display_meta.num_lines = display_meta.num_lines + 1
        pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)
        x14 = py_nvosd_line_params.x1
        x24 = py_nvosd_line_params.x2
        
        try:
            l_frame = l_frame.next
        except StopIteration:
            break
    return Gst.PadProbeReturn.OK

def main(args):
    # Check input arguments
    if len(args) != 2:
        sys.stderr.write("usage: %s <media file or uri>\n" % args[0])
        sys.exit(1)

    # Standard GStreamer initialization
    GObject.threads_init()
    Gst.init(None)

    # Create gstreamer elements
    # Create Pipeline element that will form a connection of other elements
    print("Creating Pipeline \n ")
    pipeline = Gst.Pipeline()

    if not pipeline:
        sys.stderr.write(" Unable to create Pipeline \n")

    # Source element for reading from the file
    print("Creating Source \n ")
    source = Gst.ElementFactory.make("filesrc", "file-source")
    if not source:
        sys.stderr.write(" Unable to create Source \n")

    # Since the data format in the input file is elementary h264 stream,
    # we need a h264parser
    print("Creating H264Parser \n")
    h264parser = Gst.ElementFactory.make("h264parse", "h264-parser")
    if not h264parser:
        sys.stderr.write(" Unable to create h264 parser \n")

    # Use nvdec_h264 for hardware accelerated decode on GPU
    print("Creating Decoder \n")
    decoder = Gst.ElementFactory.make("nvv4l2decoder", "nvv4l2-decoder")
    if not decoder:
        sys.stderr.write(" Unable to create Nvv4l2 Decoder \n")

    # Create nvstreammux instance to form batches from one or more sources.
    streammux = Gst.ElementFactory.make("nvstreammux", "Stream-muxer")
    if not streammux:
        sys.stderr.write(" Unable to create NvStreamMux \n")

    # Use nvinfer to run inferencing on decoder's output,
    # behaviour of inferencing is set through config file
    pgie = Gst.ElementFactory.make("nvinfer", "primary-inference")
    if not pgie:
        sys.stderr.write(" Unable to create pgie \n")

    tracker = Gst.ElementFactory.make("nvtracker", "tracker")
    if not tracker:
        sys.stderr.write(" Unable to create tracker \n")

    sgie1 = Gst.ElementFactory.make("nvinfer", "secondary1-nvinference-engine")
    if not sgie1:
        sys.stderr.write(" Unable to make sgie1 \n")

    sgie2 = Gst.ElementFactory.make("nvinfer", "secondary2-nvinference-engine")
    if not sgie1:
        sys.stderr.write(" Unable to make sgie2 \n")

    sgie3 = Gst.ElementFactory.make("nvinfer", "secondary3-nvinference-engine")
    if not sgie3:
        sys.stderr.write(" Unable to make sgie3 \n")

    nvvidconv = Gst.ElementFactory.make("nvvideoconvert", "convertor")
    if not nvvidconv:
        sys.stderr.write(" Unable to create nvvidconv \n")

    # Create OSD to draw on the converted RGBA buffer
    nvosd = Gst.ElementFactory.make("nvdsosd", "onscreendisplay")

    if not nvosd:
        sys.stderr.write(" Unable to create nvosd \n")

    # Finally render the osd output
    if is_aarch64():
        transform = Gst.ElementFactory.make(
            "nvegltransform", "nvegl-transform")

    print("Creating EGLSink \n")
    sink = Gst.ElementFactory.make("nveglglessink", "nvvideo-renderer")
    if not sink:
        sys.stderr.write(" Unable to create egl sink \n")

    print("Playing file %s " % args[1])
    source.set_property('location', args[1])
    streammux.set_property('width', stream_width)
    streammux.set_property('height', stream_height)
    streammux.set_property('batch-size', 1)
    streammux.set_property('batched-push-timeout', 4000000)

    # Set properties of pgie and sgie
    pgie.set_property('config-file-path', "dstest2_pgie_config.txt")
    sgie1.set_property('config-file-path', "dstest2_sgie1_config.txt")
    sgie2.set_property('config-file-path', "dstest2_sgie2_config.txt")
    sgie3.set_property('config-file-path', "dstest2_sgie3_config.txt")

    # Set properties of tracker
    config = configparser.ConfigParser()
    config.read('dstest2_tracker_config.txt')
    config.sections()

    for key in config['tracker']:
        if key == 'tracker-width':
            tracker_width = config.getint('tracker', key)
            tracker.set_property('tracker-width', tracker_width)
        if key == 'tracker-height':
            tracker_height = config.getint('tracker', key)
            tracker.set_property('tracker-height', tracker_height)
        if key == 'gpu-id':
            tracker_gpu_id = config.getint('tracker', key)
            tracker.set_property('gpu_id', tracker_gpu_id)
        if key == 'll-lib-file':
            tracker_ll_lib_file = config.get('tracker', key)
            tracker.set_property('ll-lib-file', tracker_ll_lib_file)
        if key == 'll-config-file':
            tracker_ll_config_file = config.get('tracker', key)
            tracker.set_property('ll-config-file', tracker_ll_config_file)
        if key == 'enable-batch-process':
            tracker_enable_batch_process = config.getint('tracker', key)
            tracker.set_property('enable_batch_process',
                                 tracker_enable_batch_process)

    print("Adding elements to Pipeline \n")
    pipeline.add(source)
    pipeline.add(h264parser)
    pipeline.add(decoder)
    pipeline.add(streammux)
    pipeline.add(pgie)
    pipeline.add(tracker)
    pipeline.add(sgie1)
    pipeline.add(sgie2)
    pipeline.add(sgie3)
    pipeline.add(nvvidconv)
    pipeline.add(nvosd)
    pipeline.add(sink)
    if is_aarch64():
        pipeline.add(transform)

    # we link the elements together
    # file-source -> h264-parser -> nvh264-decoder ->
    # nvinfer -> nvvidconv -> nvosd -> video-renderer
    print("Linking elements in the Pipeline \n")
    source.link(h264parser)
    h264parser.link(decoder)

    sinkpad = streammux.get_request_pad("sink_0")
    if not sinkpad:
        sys.stderr.write(" Unable to get the sink pad of streammux \n")
    srcpad = decoder.get_static_pad("src")
    if not srcpad:
        sys.stderr.write(" Unable to get source pad of decoder \n")
    srcpad.link(sinkpad)
    streammux.link(pgie)
    pgie.link(tracker)
    tracker.link(nvvidconv)
    nvvidconv.link(nvosd)
    if is_aarch64():
        nvosd.link(transform)
        transform.link(sink)
    else:
        nvosd.link(sink)

    # create and event loop and feed gstreamer bus mesages to it
    loop = GObject.MainLoop()

    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, loop)

    # Lets add probe to get informed of the meta data generated, we add probe to
    # the sink pad of the osd element, since by that time, the buffer would have
    # had got all the metadata.
    osdsinkpad = nvosd.get_static_pad("sink")
    if not osdsinkpad:
        sys.stderr.write(" Unable to get sink pad of nvosd \n")
    osdsinkpad.add_probe(Gst.PadProbeType.BUFFER, osd_sink_pad_buffer_probe, 0)

    print("Starting pipeline \n")

    # start play back and listed to events
    pipeline.set_state(Gst.State.PLAYING)
    try:
        loop.run()
    except:
        pass

    print("\n******************** Statistical Analysis of Video Stream ********************\n")
    x_min_list = []
    x_max_list = []
    y_min_list = []
    y_max_list = []
    id_list = []
    print('Data of all vehicles detected after a quarter of the maximum pixel height:')
    for car_objects in gate_list:
        x_min_list.append(car_objects.x_smallest)
        x_max_list.append(car_objects.x_largest)
        y_min_list.append(car_objects.y_smallest)
        y_max_list.append(car_objects.y_largest)
        id_list.append(car_objects.vehicle_id)
        print(car_objects.vehicle_id, car_objects.frames_list, car_objects.x_list, car_objects.y_list, car_objects.xc_list, car_objects.yc_list, car_objects.lane, car_objects.x_smallest, car_objects.x_largest, car_objects.y_smallest, car_objects.y_largest, sep=' ')
            
    print('\n','Tracking IDs of all vehicles detected after (below) a quarter of the maximum pixel height:', id_list, len(id_list), '\n')
    
    x_min_list.sort()
    x_max_list.sort()
    y_min_list.sort()
    y_max_list.sort()
    print('x_min:', x_min_list, len(x_min_list), '\n')
    print('x_max:', x_max_list, len(x_max_list), '\n')
    print('y_min:', y_min_list, len(y_min_list), '\n')
    print('y_max:', y_max_list, len(y_max_list), '\n')
    print('Optimal Frame Range:')
    print('x:', min(x_min_list), max(x_max_list))
    print('y:', min(y_max_list), max(y_min_list))
    midpoint = (min(y_max_list) + max(y_min_list)) / 2
    midpoint = int(midpoint)
    print('Midpoint of y = ', midpoint)
    id_list_gate = []
    for c in gate_list:
        for y in c.yc_list:
            if c.vehicle_id not in id_list_gate:
                id_list_gate.append(c.vehicle_id)            
                
    print('\n', 'Tracking IDs of all vehicles detected in the optimal frame range:', id_list_gate)
    print('\n', 'Number of vehicles =', len(id_list_gate), '\n')
    
    for f in gate_list:
        if f.vehicle_id in id_list_gate:
            my_array = np.array(f.yc_list)
            pos = (np.abs(my_array - midpoint)).argmin()
            print('tracking id =', f.vehicle_id, ', optimal frame number =', f.frames_list[pos], ', optimal coordinate = (', f.xc_list[pos], ',', f.yc_list[pos], ')', ', lane =', f.lane[pos])
            
    optimal_frame = {
         "x1": min(x_min_list),
         "x2": max(x_max_list),
         "y1": min(y_max_list),
         "y2": max(y_min_list),
         "x11": x11,
         "x12": x12,
         "x13": x13,
         "x14": x14,
         "x21": x21,
         "x22": x22,
         "x23": x23,
         "x24": x24
     }
    
    with open("optimal_frame.json", "w") as write_file:
        json.dump(optimal_frame, write_file)
    
    # cleanup
    pipeline.set_state(Gst.State.NULL)

if __name__ == '__main__':
    sys.exit(main(sys.argv))