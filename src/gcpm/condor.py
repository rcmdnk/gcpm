# -*- coding: utf-8 -*-

"""
    Module to manage HTCondor information
"""


from .utils import proc


def condor_q(opt=[]):
    return proc(["condor_q"] + opt)


def condor_status(opt=[]):
    return proc(["condor_status"] + opt)


def condor_config_val(opt=[]):
    return proc(["condor_config_val"] + opt)


def condor_reconfig(opt=[]):
    return proc(["condor_reconfig"] + opt)
    pass


def condor_wn():
    wn_candidates = condor_status(["-autoformat", "Name"])[1].split()
    wn_candidates = [x.split(".")[0] for x in wn_candidates]
    wn_candidates2 = []
    for wn in wn_candidates:
        if "@" in wn:
            wn_candidates2.append(wn.split("@")[1])
        else:
            wn_candidates2.append(wn)
    wn_list = list(set(wn_candidates2))
    return wn_list


def condor_wn_exist(wn_name):
    if wn_name in condor_wn():
        return True
    else:
        return False


def condor_wn_status():
    status_ret = condor_status(["-autoformat", "Name", "State"])[1]
    status_dict = {}
    for line in status_ret.splitlines():
        name, status = line.split()
        name = name.split(".")[0]
        if "@" in name:
            name = name.split("@")[1]
        status_dict[name] = status
    return status_dict


def condor_idle_jobs():
    qinfo = condor_q(["-allusers", "-global", "-autoformat", "JobStatus",
                      "RequestCpus"])[1]
    idle_jobs = {}
    for line in qinfo.splitlines():
        status, core = line.split()
        status = int(status)
        core = int(core)
        if status == 1:
            if core not in idle_jobs:
                idle_jobs[core] = 0
            idle_jobs[core] += 1
    return idle_jobs
