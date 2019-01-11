# -*- coding: utf-8 -*-

"""
    Module to manage HTCondor information
"""


from .utils import proc


class Condor(object):

    def __init__(self, test=False):
        self.test = test

    def condor_q(self, opt=[]):
        return proc(["condor_q"] + opt)

    def condor_status(self, opt=[]):
        if self.test:
            return (0, "", "")
        return proc(["condor_status"] + opt)

    def condor_config_val(self, opt=[]):
        if self.test:
            return (0, "", "")
        return proc(["condor_config_val"] + opt)

    def condor_reconfig(self, opt=[]):
        if self.test:
            return (0, "", "")
        return proc(["condor_reconfig"] + opt)

    def condor_wn(self):
        if self.test:
            return (0, "gcp-test-wn-1core-0001\ngcp-wn-8core-0001", "")
        wn_candidates = self.condor_status(["-autoformat", "Name"])[1].split()
        wn_candidates = [x.split(".")[0] for x in wn_candidates]
        wn_candidates2 = []
        for wn in wn_candidates:
            if "@" in wn:
                wn_candidates2.append(wn.split("@")[1])
            else:
                wn_candidates2.append(wn)
        wn_list = list(set(wn_candidates2))
        return wn_list

    def condor_wn_exist(self, wn_name):
        if wn_name in self.condor_wn():
            return True
        else:
            return False

    def condor_wn_status(self):
        status_ret = self.condor_status(["-autoformat", "Name", "State"])[1]
        if self.test:
            return (
                0,
                "gcp-test-wn-1core-0001 Claimed\ngcp-wn-8core-0001 Claimed",
                ""
            )
        status_dict = {}
        for line in status_ret.splitlines():
            name, status = line.split()
            name = name.split(".")[0]
            if "@" in name:
                name = name.split("@")[1]
            status_dict[name] = status
        return status_dict

    def condor_idle_jobs(self):
        if self.test:
            return (0, "1 1\n2 1\n1 8\n2 8", "")
        qinfo = self.condor_q(["-allusers", "-global", "-autoformat",
                               "JobStatus", "RequestCpus"])[1]
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
