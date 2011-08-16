# -*- coding: UTF-8 -*-
# Copyright 2011 Clément Mondon


class Action():
    """ 
    Action apply defined function between synchromizers 
    """

    def __init__(self, filename, hashlist, fctcopy, sync1, sync2, comment=""):
        self.filename = filename
        self.sync1 = sync1
        self.sync2 = sync2
        self.fct_copy = fctcopy
        self.hashlist = hashlist
        self.comment = comment

    def run(self, filelist1, filelist2):
        "Run copy function and update filelists"
        self.fct_copy(self.filename,self.sync1.path, self.sync2.path)
        filelist1[self.filename] = self.hashlist
        filelist2[self.filename] = self.hashlist

    def __str__(self):
        return self.filename + " : [" + self.sync1.name + "] -> [" + self.sync2.name + "]"


