#! /usr/bin/env python2.7
# -*- coding: UTF-8 -*-
# Copyright 2011 Clément Mondon

import argparse, ConfigParser
import os
from synchromizers import Synchromizer
import  synchromizers
from synchromizers import dir_index, file_index, synchromizer_index
from tools import print_done, print_failed, print_sync_name, print_running
from actions import Action


def build_filelist(sync1,sync2):
    """
    Build filelist with only files concerned by the synchromization
    """
    for filename, hashlist in sync1.synchromelist.iteritems():
        if  filename in sync2.synchromelist:
            sync1.filelist[filename] = hashlist
            sync2.filelist[filename] = sync2.synchromelist[filename]


def search_remove_differences(filelist1, filelist2):
    """
    Search the differences between the filelists for the same files, 
    remove and add them to conflicts list
    """ 
    for filename, hashlist in filelist1.items():
        if hashlist[0] != filelist2[filename][0]:  
            conflicts[filename] = (hashlist,filelist2[filename])
            del filelist1[filename]
            del filelist2[filename]


def resolve_modified_list(sync1, sync2):
    """
    Treate modified lists : modified file become an action or a conflict
    """ 
    #Search action sync1 -> sync2  
    for filename, hashlist in sync1.modified.items():

        #Basic conflict : Both files have been being modified
        if filename in sync2.modified:
            conflicts[filename] = (hashlist,sync2.modified[filename])
            del sync2.modified[filename]
        else:

            #If old hashs are equal, we can copy
            if hashlist[0] == sync2.filelist[filename][0]:
                actionlist.append( Action(filename,hashlist,sync2.fct_copy,sync1, sync2) )
            else:
                conflicts[filename] = (hashlist,sync2.filelist[filename])
            del sync2.filelist[filename]

        del sync1.modified[filename]


    #There are not basic conflict, Search action sync1 -> sync2 , or conflict
    for filename, hashlist in sync2.modified.items():
        #If old hashs are equal, we can copy
        if hashlist[0] == sync1.modified[filename][0]:
            actionlist.append( Action(filename,hashlist,sync2.fct_copy,sync1, sync2) )
        else:
            conflicts[filename] = (hashlist,sync1.modified[filename])
        del sync2.modified[filename]
        del sync1.filelist[filename]


def try_history(conflicts, sync1, sync2):
    """
    Trying to resolve conflicts with history
    """
    for filename, (hashlist1, hashlist2) in conflicts.items():

        if hashlist2[0] == hashlist1[0]:
            del conflicts[filename]
            continue

        for currenthash in hashlist2:
            if currenthash == hashlist1[0]:
                actionlist.append (Action (filename, hashlist2, sync2.fct_copy, sync2, sync1))
                del conflicts[filename]
                print "%s : Resolved with history" % filename
                break
        else:
            for currenthash in hashlist1:
                if currenthash == hashlist2[0]:
                    actionlist.append (Action (filename, hashlist1, sync2.fct_copy, sync1, sync2))
                    del conflicts[filename]
                    print "%s : Resolved with history" % filename
                    break


def prompt_conflict(sync1,sync2,conflictlist):
    """
    Prompt conflicts to user
    """
    for filename, (hashlist1, hashlist2) in conflicts.items():
        print "%s : [%s] ? [%s] ( <, >, or p for pass )" % (filename, sync1.name, sync2.name)
        response = raw_input()
        if response == ">":
            actionlist.append (Action (filename, hashlist1, sync2.fct_copy, sync1, sync2))
            del conflicts[filename]
        elif response == "<":
            actionlist.append (Action (filename, hashlist2, sync2.fct_copy, sync2, sync1))
            del conflicts[filename]
        elif response == "p":
            pass
        else:
            print "I don't understand you"


def synchro(synchromizer1, synchromizer2):
    """
    Synchromization between two Synchromizers
    """

    # REDUCE THE FILELISTS
    #Build filelist with only files concerned by the synchromization
    build_filelist(synchromizer1, synchromizer2)

    #Search and remove the differences between .synchrome list and reality
    # Expanding modified list
    synchromizer1.test_local_changes()
    synchromizer2.test_local_changes()

    #Search and remove the differences between the .synchrome lists
    # Expanding conflicts list
    search_remove_differences(synchromizer1.filelist,synchromizer2.filelist)

    # BUILD ACTION LIST
    # Expand actions list and conflicts list
    # Emptying modified list
    resolve_modified_list(synchromizer1, synchromizer2)

    #Try to use history to solve conflicts automatically
    try_history(conflicts,synchromizer1,synchromizer2)

    #Ask user to take a decision
    prompt_conflict(synchromizer1, synchromizer2, conflicts)

    #Run actions
    [ action.run(synchromizer1.filelist, synchromizer2.filelist) for action in actionlist ]

def build_local_sync():
    local = Synchromizer("(local)")
    return synchromizer_type(local.name)

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
    #"\n".join([synchromizer.add(args.file_added.name) for synchromizer in args.synchromizers])
    #"###\n".join([synchromizer.add(args.file_added.name) for synchromizer in args.synchromizers])

def sync(args):
    """
    Sync command : run synchro function between all enabled synchromizers
    """
    global sync_local 
    sync_local = build_local_sync() 
    args.synchromizers.append(sync_local)
    
    synchromizers_list = args.synchromizers

    for synchromizer1 in synchromizers_list:
        for synchromizer2 in synchromizers_list:
            synchro(synchromizer1, synchromizer2) 
        synchromizers_list.remove(synchromizer1)


def check(args):
    """
    Check command : display synchromizers
    """
    if args.synchromizers:
        [ print_sync_name(sync.name+" %s \n %s" % (len(sync), sync.synchromelist.keys() )) for sync in args.synchromizers ]
    #Print local synchromizer only
    else:
        sync = build_local_sync()
        print_sync_name(sync.name+" %s \n %s" % (len(sync), sync.synchromelist.keys() ))

def read_synchromizers_definition():
    """
    Read the INI file with configparse, build a list of available synchromizers and return it
    """

    result = {}
    print_running("Reading synchromizers definitions ...")

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
            response = raw_input("I can't read synchromizer defintion. It is a problem. \nIf you want init a new file, press 'y'. \nYou should certainly copy SYNCHOME_PATH/%s%s of another synchromizer. \nPress 'n' to quit  (y/N)" % (dir_index,synchromizer_index))

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

if __name__ == "__main__":

    synchromizers_available = read_synchromizers_definition() #{ "home":"/home/clem", "tmp":"/tmp/"}  #TODO configparse  #List of available synchromizers
    conflicts = {} #List of conflicts
    actionlist = [] #List of actions

    #PARSE COMMAND LINE
    parser = argparse.ArgumentParser(description='Synchronization of Synchromizers -> «Synchromization»')
    subparsers = parser.add_subparsers(help='sub-command')
    #Add
    add_parser = subparsers.add_parser('add')
    add_parser.add_argument('file_added', metavar='filename', type=file, help='Filename (path)')
    add_parser.add_argument('synchromizers', metavar='synchromizers', type=synchromizer_type, nargs='+', 
            help='one or more sychromizer to deal with')
    add_parser.set_defaults(func=add)
    #Sync
    sync_parser = subparsers.add_parser('sync')
    sync_parser.add_argument('synchromizers', metavar='synchromizers', type=synchromizer_type, nargs='+',
            help='one or more sychromizer to deal with')
    sync_parser.set_defaults(func=sync)
    #check
    check_parser = subparsers.add_parser('check')
    check_parser.add_argument('synchromizers', metavar='synchromizers', type=synchromizer_type, nargs='*',
            help='one or more sychromizer to deal with')
    check_parser.set_defaults(func=check)



    #RUN APROPRIATE SUB-COMMAND
    #try:
    args = parser.parse_args()
    args.func(args)
    #except Exception as (msg):
    #    print_failed("\nERROR : %s " % (msg))
    #    exit(os.EX_DATAERR)

