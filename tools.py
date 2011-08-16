#! /usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright 2011 Clément Mondon

sync_name_len=10
msg_running_len=30


def print_done(string="[ Done ]"):
    print "\033[32m %s\033[00m" % string

def print_failed(string="[Failed]"):
    print "\033[01;31m %s\033[00m" % string

def print_sync_name(name):
    print "\033[34m","%s".ljust(sync_name_len-len(name)) % name, "\033[00m",

def print_running(msg):
    print "\033[33m","%s".ljust(msg_running_len-len(msg)) % msg, "\033[00m",
