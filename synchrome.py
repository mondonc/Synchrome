#! /usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright 2011 Amandine Degand, Clément Mondon

import argparse
from synchromizers import *


class Action():
    """ Action entitie """
    def __init__(self, filename, hashlist, fctcopy, sync1, sync2):
        self.filename = filename
        self.sync1 = sync1
        self.sync2 = sync2
        self.fct_copy = fctcopy
        self.hashlist = hashlist

    def run(self, filelist1, filelist2):
        "Run copy function and update filelists"
        self.fct_copy(self.filename,self.sync1.path, self.sync2.path)
        filelist1[self.filename] = self.hashlist
        filelist2[self.filename] = self.hashlist

    def __str__(self):
        return self.filename + " : [" + self.sync1.name + "] -> [" + self.sync2.name + "]"


def build_filelist(sync1,sync2):
    for filename, hashlist in sync1.synchromelist.iteritems():
        if  filename in sync2.synchromelist:
            sync1.filelist[filename] = hashlist
            sync2.filelist[filename] = sync2.synchromelist[filename]

def search_remove_differences(filelist1, filelist2):
    "Search the differences between the filelists, remove and add them to conflicts list" 
    for filename, hashlist in filelist1.items():
        if hashlist[0] != filelist2[filename][0]:  
            conflicts[filename] = (hashlist,filelist2[filename])
            del filelist1[filename]
            del filelist2[filename]

def resolve_modified_list(sync1, sync2):
    "Treate modified lists" 

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
    "Trying to resolve conflicts "

    for filename, (hashlist1, hashlist2) in conflicts.items():

        if hashlist2[0] == hashlist1[0]:
                del conflicts[filename]
                break

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
    "Prompt conflicts"
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

    # REDUCE THE FILELISTS
    ########################

    #Remove the files not concerned by the synchromization
    build_filelist(synchromizer1, synchromizer2)

    #Search and remove the differences between .synchrome list and reality
    # Expanding modified list
    synchromizer1.test_local_changes()
    synchromizer2.test_local_changes()

    #Search and remove the differences between the .synchrome lists
    # Expanding conflicts list
    search_remove_differences(synchromizer1.filelist,synchromizer2.filelist)

    # BUILD ACTION LIST
    ########################

    # Expand actions list and conflicts list
    # Emptying modified list
    resolve_modified_list(synchromizer1, synchromizer2)

    #Try to use history to solve conflicts automatically
    try_history(conflicts,synchromizer1,synchromizer2)
    
    #Ask user to take a decision
    prompt_conflict(synchromizer1, synchromizer2, conflicts)

    #Run actions
    for action in actionlist:
        action.run(synchromizer1.filelist, synchromizer2.filelist)


def add(synchromizers):
    print "SALUT"



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Synchronization of Synchromizers -> «Synchromization»')
    subparsers = parser.add_subparsers(help='commands')

    add_parser = subparsers.add_parser('add')
    add_parser.add_argument('synchromizers', metavar='synchromizers', type=str, nargs='+',
                   help='one or more sychromizer to deal with')

    #parser.add_argument('synchromizers', metavar='N', type=str, nargs='*',
                   #help='one or more sychromizer to deal with')
    #parser.add_argument('--add', dest='addfile', action='store', default=None, 
                   #help='Add file to synchromizer')
    #parser.add_argument('--get', dest='addfile', action='store', default=None, 
                   #help='Get file from a synchromizer')
    #parser.add_argument('--list', dest='addfile', action='store_true', default=False, 
                   #help='List file of synchromizer')

    args = parser.parse_args()
    arguments = dict(args._get_kwargs())
    print arguments

    #print args.synchromizers
    #print args.addfile
    print args
    print add_parser

    actionlist = [] 
    conflicts = {}
    local = Synchromizer("home",".")
    test = Synchromizer("test","/tmp")
    #test.add(".bashrc")
    #local.add("toto")
    #test.add("toto")
    #synchro(local,test)
    print  local
    print  test
    print "CONFLICT"
    print  conflicts
    print "Actions : "
    for action in actionlist:
        print action
    #local.save()
    #test.save()
