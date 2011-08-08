# -*- coding: UTF-8 -*-
# Copyright 2011 Clément Mondon

import os
import hashlib 
from sys import stdout
from tools import print_done, print_failed, print_sync_name, print_running
import ConfigParser


dir_index = ".synchrome/"
file_index = ".synchrome.cfg"
synchromizer_index = ".synchromizers.cfg"

class Synchromizer():
    """ Synchomizer entitie """

    def __init__(self, name, path='.', hostname="localhost"):
        "Build Synchromizer"
        self.name = name
        self.path = path
        self.hostname = hostname
        self.filelist = {}
        self.synchromelist = {}
        self.modified = {}
       
        try : 
            read_name = self.load()
            assert( read_name == self.name or  self.name == "(local)")
            self.name = read_name
        except (IOError , EOFError, IndexError, AssertionError) as (msg) :
            print_failed()
            print_failed(msg)
            
            #If error, attempting to create file
            response = raw_input("Do you want to init %s ? (y/N)" % self.name)
            
            if self.name == "(local)":
                self.name = raw_input("Enter new name : ")
                self.path = os.getcwd()
                self.registre()

            if response in ["y", "Y"]: 
                dirpath = self.path+os.sep+dir_index
                if not os.path.isdir(dirpath):
                    os.makedirs(dirpath)
                self.save()
            else:
                exit(os.EX_DATAERR)
        except TypeError as msg:
            print_failed(msg)
            print "Type erro"
            self.synchromelist = {}


    def local_add(self,file_added):
        "Add a file to synchromizer"
        print_sync_name(self.name)
        print_running("Adding local file %s ..." % file_added.name)
        try:
            md5 = [hashlib.md5(file_added.read()).hexdigest(),]
            self.filelist[file_added.name] = md5
            print_done()
            return md5
        except Exception as msg:
            print_failed("Failed")
            print_failed(msg)
            exit(os.EX_DATAERR)

    def remote_add(self, filepath, md5sum):
        #self.put(filepath)
        self.fct_copy(filepath, '.', self.path)
        self.filelist[filepath] = md5sum

    def load(self):
        "Read filelist file"
        print_sync_name(self.name)
        print_running(": Reading file ..."),
        f = open(self.path+os.sep+dir_index+os.sep+file_index, "r")
        config = ConfigParser.ConfigParser()
        config.readfp(f)
        f.close()
        read_name = config.sections()[0]
        for opt in config.options(read_name):
            self.synchromelist[opt]=config.get(read_name, opt) 
        print_done()
        return read_name


    def save(self):
        "Write filelist file"
        print_sync_name(self.name)
        print_running(": Saving %s ..." % self.name),
        config = ConfigParser.ConfigParser()
        config.add_section(self.name)
        self.synchromelist.update(self.filelist)
        [ config.set(self.name, filename, hashlist) for filename, hashlist in self.synchromelist.items() ]
        f = open(self.path+os.sep+dir_index+os.sep+file_index, "w")
        config.write(f)
        f.close()
        print_done()

    def registre(self):
        "Registre synchromizer to synchromizer_index file"
        print_running("Registring %s ..." % self.name),
        config = ConfigParser.ConfigParser()
        config.add_section(self.name)
        config.set(self.name, "class", self.__class__)
        config.set(self.name, "path", self.path)
        f = open(self.path+os.sep+dir_index+os.sep+synchromizer_index, "a")
        config.write(f)
        f.close()
        print_done()










    def test_local_changes(self):
        "Update modified filelist"
        stdout.write("Verifying local changes")
        stdout.write("Verifying local changes")
        stdout.flush()
        for filename, hashlist in self.filelist.items():

            stdout.write(" "*30)
            stdout.flush()
            stdout.write("\rVerifying %s" % filename)

            try:
                md5 = md5sum(self.path+os.sep+filename) 
            except Exception as (msg):
                print msg

            if md5 == hashlist[0]:
                stdout.write(" OK")
            else:
                stdout.write(" KO")
                self.modified[filename] = [md5] + eval(hashlist+"[:10]")
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

    def fct_remove(self, filename, path1, path2):
        import subprocess 
        subprocess.call(["rm", "-f",path1+os.sep+filename, path2+os.sep])
        return None


    def isMe(self):
        "return true if it is me that runs synchrome execution "

    def isAvailable(self):
        "return true if i am synchromizable "

    def __str__(self):
        return self.name + "\nManaged : " + str(self.synchromelist.keys()) + "\nUnchanged : "+ str(self.filelist.keys()) + "\n" + "Modified : " + str(self.modified.keys())

    def __len__(self):
        return len(self.synchromelist)


def md5sum(path):
    try:
        f=open(path,'r')
        md5 = hashlib.md5(f.read()).hexdigest()
        f.close()
        return md5
    except:
        print_failed("Md5sum of %s failed" % path)
        return None

