#! /usr/bin/env python2.7
# -*- coding: UTF-8 -*-
# Copyright 2011 Clément Mondon

import argparse, ConfigParser
import hashlib
import readline
import os
from sys import stdout


#---------------------------------
# $1 Core functions (sync process, ...)
# $2 Main Actions (parsearg and co)
# $3 Action class
# $4 Other functions (tools)
# $5 Synchromizer definition 
# $6 Main  
#---------------------------------

#---------------------------------
# $1 Core functions (sync process, ...)
#---------------------------------


def build_filelist(sync1,sync2):
    """
    Build filelist with only files concerned by the synchromization
    """

    #TODO : rewrite it
    for filename, hashlist in sync1.synchromelist.iteritems():
        if  sync2.synchromelist.has_key(filename):
            sync1.filelist[filename] = hashlist
            sync2.filelist[filename] = sync2.synchromelist[filename]


def search_remove_differences(filelist1, filelist2):
    """
    Search the differences between the filelists for the same files, 
    remove and add them to conflicts list
    """ 

    for filename, hashlist in filelist1.items():
        if filelist2.has_key(filename) and hashlist[0] != filelist2[filename][0]:  
            conflicts[filename] = (hashlist,filelist2[filename])
            del filelist1[filename]
            del filelist2[filename]


def resolve_modified_list(sync1, sync2):
    """
    Treate modified lists : modified file become an action or a conflict
    """ 
    # Search action sync1 -> sync2  
    for filename, hashlist in sync1.modified.items():

        # Basic conflict : Both files have been being modified
        if filename in sync2.modified:
            conflicts[filename] = (hashlist,sync2.modified[filename])
            del sync2.modified[filename]
        else:
            # If old hashs are equal, we can copy
            if hashlist[1] == sync2.filelist[filename][0]:
                actionlist.append( Action(filename,hashlist,sync2.fct_copy,sync1, sync2, comment="auto") )
            else:
                conflicts[filename] = (hashlist,sync2.filelist[filename])
            del sync2.filelist[filename]

        del sync1.modified[filename]


    # There are not basic conflict, Search action sync1 -> sync2 or conflict
    for filename, hashlist in sync2.modified.items():

        # If old hashs are equal, we can copy
        if hashlist[1] == sync1.filelist[filename][0]:
            actionlist.append( Action(filename,hashlist,sync2.fct_copy,sync2, sync1, comment="auto") )
        else:
            conflicts[filename] = (sync1.filelist[filename],hashlist)
        del sync2.modified[filename]
        del sync1.filelist[filename]


def try_history(conflicts, sync1, sync2):
    """
    Trying to resolve conflicts with history
    """

    for filename, (hashlist1, hashlist2) in conflicts.items():

        if hashlist2[0] == hashlist1[0]:
            print "No change, I don't know why I do that %s" % filename
            del conflicts[filename]
            continue

        for currenthash in hashlist2:
            if currenthash == hashlist1[0]:
                actionlist.append (Action (filename, hashlist2, sync2.fct_copy, sync2, sync1, comment="history 1"))
                del conflicts[filename]
                break
        else:
            for currenthash in hashlist1:
                if currenthash == hashlist2[0]:
                    actionlist.append (Action (filename, hashlist1, sync2.fct_copy, sync1, sync2, comment="history 2"))
                    del conflicts[filename]
                    break


def prompt_conflict(sync1,sync2,conflictlist):
    """
    Prompt conflicts to user
    """

    print "Conflict resolution :"
    for filename, (hashlist1, hashlist2) in conflicts.items():
        print "%s : [%s] ? [%s] ( <, >, or p for pass )" % (filename, sync1.name, sync2.name)
        response = raw_input()
        if response == ">":
            actionlist.append (Action (filename, hashlist1, sync2.fct_copy, sync1, sync2, comment="user"))
            del conflicts[filename]
        elif response == "<":
            actionlist.append (Action (filename, hashlist2, sync2.fct_copy, sync2, sync1, comment="user"))
            del conflicts[filename]
        elif response == "p":
            pass
        else:
            print "I don't understand you"


def prompt_actions(sync1,sync2,actionlist):
    """
    Prompt actions to user, return true if action
    """

    print "Action list :"
    for action in actionlist:
        if action.sync1 == sync1:
            direction = "->"
        else:
            direction = "<-"
        print "%s : %s %s %s (%s)" % (action.filename, sync1.name, direction, sync2.name, action.comment) 
        
    response = raw_input("Are you agree ? (Y/n)")

    if response in ["n", "N"]:
        #TODO : regexp to select filenames -> conflicts 
        print_running("Exiting ...\n")
        exit(os.EX_NOUSER)

       


def synchro(synchromizer1, synchromizer2):
    """
    Synchromization between two Synchromizers
    """
    global conflicts, actionlist
    conflicts = {} #List of conflicts
    actionlist = [] #List of actions

    # Build filelist with only files concerned by the synchromization
    # Reduce the filelists
    build_filelist(synchromizer1, synchromizer2)

    # Search and remove the differences between .synchrome list and reality
    # Expanding modified list
    synchromizer1.test_local_changes()
    synchromizer2.test_local_changes()

    # Search and remove the differences between the .synchrome lists
    # Expanding conflicts list
    search_remove_differences(synchromizer1.filelist,synchromizer2.filelist)

    # Expand actions list and conflicts list
    # Emptying modified list
    resolve_modified_list(synchromizer1, synchromizer2)

    # Try to use history to solve conflicts automatically
    try_history(conflicts,synchromizer1,synchromizer2)

    if conflicts:
        # Ask user to take a decision
        prompt_conflict(synchromizer1, synchromizer2, conflicts)

    if actionlist:
        # Ask user to take a decision, return True if action performed
        prompt_actions(synchromizer1, synchromizer2, actionlist)

        # Run actions
        [ action.run(synchromizer1.filelist, synchromizer2.filelist) for action in actionlist ]

        synchromizer1.save()
        synchromizer2.save()

        return True # = actions performed

    else:
        return False # = no action



def build_local_sync():
    """
    Return local synchromizer object
    """
    local = Synchromizer("(local)")
    return synchromizer_type(local.name)


#---------------------------------
# $2 Main Actions (parsearg and co)
#---------------------------------

def init(args):
    """
    Init new synchromizer
    """

    cur_dir = os.getcwd().rpartition('/')[2]
    config = ConfigParser.ConfigParser()

    name = raw_input("Enter new name (%s): " % cur_dir)

    if not name:
        name = cur_dir

    if not os.path.isdir(dir_index):
        os.mkdir(dir_index)

    config = ConfigParser.ConfigParser()
    config.add_section(name)
    f = open(dir_index+os.sep+file_index, "w")
    config.write(f)
    f.close()

    local = Synchromizer("(local)", path=os.getcwd())
    local.registre()
    local.local_add(open(dir_index+synchromizer_index))
    local.save()


def add(args):
    """
    Add command : add file to all enabled synchromizers
    """
    sync_local = build_local_sync() 
    md5 = sync_local.local_add(args.file_added) 
    for synchromizer in args.synchromizers:
        print_sync_name(synchromizer.name)
        print_running("Adding %s ..." % args.file_added.name)
        synchromizer.remote_add(args.file_added.name, md5)
        print_done()
    sync_local.save()
    [ synchromizer.save() for synchromizer in args.synchromizers ]


def sync(args):
    """
    Sync command : run synchro function between all enabled synchromizers
    """
    sync_local = build_local_sync() 
    args.synchromizers.append(sync_local)
    #TODO verif local != synchromizers

    needed = True
    while needed:
    
        synchromizers_list = args.synchromizers
        needed = False

        for synchromizer1 in synchromizers_list:
            synchromizers_list.remove(synchromizer1)
            for synchromizer2 in synchromizers_list:
                print "Synchromization between %s and %s" % (synchromizer1.name, synchromizer2.name)
                needed = synchro(synchromizer1, synchromizer2) or needed
                synchromizer1.load()
                synchromizer2.load()

    print_running("End of sync process\n")

def check(args):
    """
    Check command : display synchromizers
    """

    if not args.synchromizers:
        sync = build_local_sync()
        args.synchromizers.append(sync)

        print_info("Available synchromizers :") 
        for sync, param in synchromizers_available.items(): 
            print_sync_name(sync+" :")
            print ""
            [ print_desc(key+" : "+info) for key, info in param.items() ]

    for sync in args.synchromizers:
        print_sync_name(sync.name+" (%s):"  % len(sync))
        print ""
        [ print_desc(info) for info in sync.synchromelist.keys() ]


def read_synchromizers_definition():
    """
    Read the INI file with configparse, build a list of available synchromizers and return it
    """

    result = {}
    print_global_running("Reading synchromizers definitions ...")

    try:
        f = open(dir_index+os.sep+synchromizer_index, "r")
        config = ConfigParser.ConfigParser()
        config.readfp(f)
        f.close()
        
        for synchromizer in config.sections():
            opts = {}
            for opt in config.options(synchromizer):
                opts[opt]=config.get(synchromizer, opt) 
            result[synchromizer] = opts
        print_done()


    except (IOError , EOFError, IndexError, AssertionError) as (msg) :
            print_failed()

            dirpath = '.'+os.sep+dir_index
            if not os.path.isdir(dirpath):
                os.makedirs(dirpath)
            
            #If error, attempting to create file
            response = raw_input("I can't read synchromizer definition. It is a problem. \nYou should certainly copy SYNCHOME_PATH/%s%s of another synchromizer. \nIf you want init a new file, press 'y', press 'n' to quit  (y/N)" % (dir_index,synchromizer_index))

            if response in ["y", "Y"]:
                open(dirpath+os.sep+synchromizer_index, 'w').close()
            else:
                exit(os.EX_DATAERR)
    return result 


def synchromizer_type(synchromizer_name):
    """
    Return new synchromizer object or raise exception ; used by argparse
    """
    if synchromizer_name in synchromizers_available.keys():
        return eval(synchromizers_available[synchromizer_name]['class']+"(synchromizer_name, synchromizers_available[synchromizer_name]['path'])")
    else:
        raise(Exception('Unable to find this Synchromizer : %s \n Synchromizers availables : %s' % (synchromizer_name, synchromizers_available.keys()) ))
    #argparse.ArgumentTypeError(msg)


#---------------------------------
# $3 Action class
#---------------------------------

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



#---------------------------------
# $4 Other functions (tools)
#---------------------------------

#Static definitions

try : 
    COLUMNS = int(os.popen('stty size', 'r').read().split()[1])
except Exception:
    COLUMNS = 80

if COLUMNS < 80:
    COLUMNS=80

SYNC_LEN = 15
RESULT_LEN = 8
RUNNING_LEN = COLUMNS - RESULT_LEN - SYNC_LEN - 7  


def print_done(string="[ Done ]"):
    print "\033[32m %s\033[00m" % string

def print_failed(string="[Failed]"):
    print "\033[01;31m %s\033[00m" % string

def print_sync_name(name):
    print "\033[34m","\r%s" % name[:SYNC_LEN].rjust(SYNC_LEN), "\033[00m",

def print_running(msg):
    print "\033[33m","%s" % msg[:RUNNING_LEN].ljust(RUNNING_LEN), "\033[00m",

def print_file(msg):
    print "\033[36m","%s" % msg[-RUNNING_LEN:].ljust(RUNNING_LEN), "\033[00m",

def print_info(msg):
    print "\033[35m","\r%s" % msg[-RUNNING_LEN:].ljust(RUNNING_LEN), "\033[00m"

def print_desc(msg):
    print " "*SYNC_LEN+"\033[36m","%s" % msg[-RUNNING_LEN:].ljust(RUNNING_LEN), "\033[00m"

def print_global_running(msg):
    print "\033[33m","\r%s" % msg[:RUNNING_LEN].ljust(RUNNING_LEN), "\033[00m"+" "*(SYNC_LEN+3),



#---------------------------------
# $5 Synchromizer definition 
#---------------------------------

dir_index = ".synchrome/"
file_index = "files.cfg"
synchromizer_index = "synchromizers.cfg"

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
        except (IOError , EOFError, IndexError, AssertionError, TypeError) as (msg) :
            print_failed()
            print_failed(msg)
            print_failed("You should certainly run 'init' subcommand")
            exit(os.EX_DATAERR)


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
        print_running("Reading file ..."),
        f = open(self.path+os.sep+dir_index+os.sep+file_index, "r")
        config = ConfigParser.ConfigParser()
        config.readfp(f)
        f.close()
        read_name = config.sections()[0]
        for opt in config.options(read_name):
            self.synchromelist[opt]=eval(config.get(read_name, opt)) 
        print_done()
        return read_name


    def save(self):
        "Write filelist file"
        print_sync_name(self.name)
        print_running("Saving ..."),
        config = ConfigParser.ConfigParser()
        config.add_section(self.name)
        self.synchromelist.update(self.filelist)
        [ config.set(self.name, filename, hashlist[:10]) for filename, hashlist in self.synchromelist.items() ]
        f = open(self.path+os.sep+dir_index+os.sep+file_index, "w")
        config.write(f)
        f.close()
        print_done()

    def registre(self):
        "Registre synchromizer to synchromizer_index file"

        print_sync_name(self.name)
        print_running("Registring ...")
        
        config = ConfigParser.ConfigParser()

        f = open(dir_index+os.sep+synchromizer_index, "r")
        config.readfp(f)
        f.close()

        config.add_section(self.name)
        config.set(self.name, "class", self.__class__.__name__)
        config.set(self.name, "path", self.path)
        f = open(dir_index+os.sep+synchromizer_index, "w")
        config.write(f)
        f.close()
        print_done()

    def test_local_changes(self):
        "Update modified filelist"
        
        for filename, hashlist in self.filelist.items():

            print_sync_name(self.name)
            print_file(filename)
            stdout.flush()

            try:
                md5 = md5sum(self.path+os.sep+filename) 
            except Exception as (msg):
                print msg

            if md5 == hashlist[0]:
                stdout.write(" OK")
            else:
                stdout.write(" KO")
                hashlist.insert(0, md5)
                self.modified[filename] = hashlist
                del self.filelist[filename]

        print_sync_name(self.name)
        print_running("Verifying local changes ... (%d)" % len(self.modified))
        print_done()
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
        directories = filename.rpartition('/')[0]

        if directories and not os.access(path2+os.sep+directories, os.W_OK):
            os.makedirs(directories)

        subprocess.call(["cp", path1+os.sep+filename, path2+os.sep+filename])
        return None

    def fct_remove(self, filename, path1, path2):
        import subprocess 
        subprocess.call(["rm", "-f",path1+os.sep+filename, path2+os.sep])
        return None

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


#---------------------------------
# $6 Main
#---------------------------------


if __name__ == "__main__":

    synchromizers_available = read_synchromizers_definition() 


    # PARSE COMMAND LINE
    parser = argparse.ArgumentParser(description='Synchronization of Synchromizers -> «Synchromization»')
    subparsers = parser.add_subparsers(help='sub-command')
    
    # Add
    add_parser = subparsers.add_parser('add')
    add_parser.add_argument('file_added', metavar='filename', type=file, help='Filename (path)')
    add_parser.add_argument('synchromizers', metavar='synchromizers', type=synchromizer_type, nargs='+', 
            help='one or more sychromizer to deal with')
    add_parser.set_defaults(func=add)
    
    # Sync
    sync_parser = subparsers.add_parser('sync')
    sync_parser.add_argument('synchromizers', metavar='synchromizers', type=synchromizer_type, nargs='+',
            help='one or more sychromizer to deal with')
    sync_parser.set_defaults(func=sync)
    
    # Check
    check_parser = subparsers.add_parser('check')
    check_parser.add_argument('synchromizers', metavar='synchromizers', type=synchromizer_type, nargs='*',
            help='one or more sychromizer to deal with')
    check_parser.set_defaults(func=check)

    # Init
    init_parser = subparsers.add_parser('init')
    init_parser.set_defaults(func=init)


    #RUN APROPRIATE SUB-COMMAND
    #args = parser.parse_args()
    #args.func(args)
    try:
        args = parser.parse_args()
        args.func(args)
    except Exception as (msg):
        print_failed("\nERROR : %s " % (msg))
        exit(os.EX_DATAERR)





