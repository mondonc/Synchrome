# -*- coding: UTF-8 -*-
# Copyright 2011 Amandine Degand, Clément Mondon

import os
import pickle
import hashlib 
from sys import stdout

dir_index = ".synchrome/"
file_index = ".synchrome"

class Synchromizer():
    """ Synchomizer entitie """

    def __init__(self, name, path='.'):
        "Build Synchromizer"
        self.name = name
        self.path = path
        self.filelist = {}
        self.synchromelist = {}
        self.modified = {}
        try:
            print "Reading file ...",
            f = open(self.path+os.sep+dir_index+os.sep+file_index, "r")
            try : 
                self.synchromelist = dict(pickle.load(f))
                print " [ Done ]"
            finally:
                f.close()
        except (IOError , EOFError):
            print " [ Failed ! ]"
            #If error, attempting to create file
            response = raw_input("Do you want to init %s ? (y/N)" % self.name)
            if response in ["y", "Y"]: 
                dirpath = self.path+os.sep+dir_index
                if not os.path.isdir(dirpath):
                    os.makedirs(dirpath)
                f = open(dirpath+os.sep+file_index, "w")
                try:
                    pickle.dump({}, f) 
                finally:
                    f.close()
        except TypeError:
            self.synchromelist = {}


    def add(self,filepath):
        "Add a file to synchromizer"
        self.synchromelist[filepath] = [md5sum(filepath),]

    def save(self):
        "Write filelist file"
        f = open(self.path+os.sep+dir_index+os.sep+file_index, "w")
        pickle.dump(self.synchromelist.update(self.filelist), f) 
        #pickle.dump(self.filelist, f) 
        f.close()

    def test_local_changes(self):
        "Update modified filelist"
        stdout.write("Verifying local changes")
        stdout.write("Verifying local changes")
        stdout.flush()
        for filename, hashlist in self.filelist.items():

            stdout.write(" "*30)
            stdout.flush()
            stdout.write("\rVerifying %s" % filename)
            md5 = md5sum(self.path+os.sep+filename) 
            if md5 == hashlist[0]:
                stdout.write(" OK")
            else:
                stdout.write(" KO")
                self.modified[filename] = [md5] + hashlist[:10]
                del self.filelist[filename]

        stdout.write("\rVerifying finished")
        stdout.write(" "*30+"\n")
        stdout.flush()

    def read(self, filepath):
        try:
            f = open(self.path+os.sep+os.sep+filepath, "r")
            content = f.read()
            f.close()
            return content
        except (IOError , EOFError):
            print "Error, can't write file %s" % filepath
            return None


    def update(self, filepath, content):
        try:
            f = open(self.path+os.sep+os.sep+filepath, "w")
            f.write(content)
            f.close()
        except (IOError , EOFError):
            print "Error, can't write file %s" % filepath

    def fct_copy(self, filename, path1, path2):
        import subprocess 
        subprocess.call(["cp", path1+os.sep+filename, path2+os.sep])
        return None

    def isMe(self):
        "return true if it is me that runs synchrome execution "

    def isAvailable(self):
        "return true if i am synchromizable "

    def __str__(self):
        return self.name + "\nManaged : " + str(self.synchromelist.keys()) + "\nUnchanged : "+ str(self.filelist.keys()) + "\n" + "Modified : " + str(self.modified.keys())


def md5sum(path):
    try:
        f=open(path,'r')
        md5 = hashlib.md5(f.read()).hexdigest()
        f.close()
        return md5
    except:
        print "! Md5sum of %s failed" % path
        return None

