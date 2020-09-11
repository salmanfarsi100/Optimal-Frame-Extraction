# -*- coding: utf-8 -*-
"""
Created on Thu Aug 20 00:11:35 2020

@author: nabeel.tahir
"""
#!/usr/bin/env python3
from configparser import ConfigParser
from openalpr import Alpr
import sys
import json
class NplateExtraction:
    def __init__(self, confgpath):
        self.confgpath=confgpath
        config = ConfigParser()
        config.read(self.confgpath)
        self.confsect  = config['NPEConfig']
        self.alprconfig  =   self.confsect['alprconfig']
        self.alprruntime =   self.confsect['alprruntime']
        self.imagepath   =   self.confsect['objImage']
        self.alpr = Alpr("us",self.alprconfig,self.alprruntime)
        self.alpr.set_top_n(4)
        #self.alpr.set_default_region("us")
        print(self.alpr.is_loaded())
        if not self.alpr.is_loaded():
             print("Error loading OpenALPR")
             sys.exit(1)
        #print(self.alprconfig)
    def getplate(self, imagepath):
        results = self.alpr.recognize_file(imagepath)
        xtop=results['results'][0]['coordinates'][0]['x']
        ytop=results['results'][0]['coordinates'][0]['y']
        width=int(results['results'][0]['coordinates'][1]['x'])-int(xtop)
        height=int(results['results'][0]['coordinates'][3]['x'])-int(ytop)

        retresult={ "plate":results['results'][0]['candidates'][0]['plate'],
                    "confidence":results['results'][0]['candidates'][0]['confidence'], "xtop": xtop, "ytop": ytop, "width": width, "height": height

        }
        return json.dumps(retresult, indent=4)#(results['results'][0]['candidates'][0],results['results'][0]['coordinates'])
        #print(json.dumps(results, indent=4))
        #self.alpr.unload()
