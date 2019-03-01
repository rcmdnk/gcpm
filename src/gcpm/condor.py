# -*- coding: utf-8 -*-

"""
    Module to manage HTCondor information
"""


from .utils import proc


class Condor(object):

    def __init__(self, test=False):
        self.test = test

    def q(self, opt=[]):
        return proc(["condor_q"] + opt)

    def status(self, opt=[]):
        if self.test:
            return (0, "", "")
        return proc(["condor_status"] + opt)

    def config_val(self, opt=[]):
        if self.test:
            return (-1, "", "")
        return proc(["condor_config_val"] + opt)

    def reconfig(self, opt=[]):
        if self.test:
            return (-1, "", "")
        return proc(["condor_reconfig"] + opt)

    def wn(self):
        if self.test:
            return ["gcp-test-wn-1core-0001"]
        ret, wn_candidates, err = self.status(
            ["-autoformat", "Name"])
        if ret != 0:
            return ret, []
        wn_candidates = [x.split(".")[0] for x in wn_candidates.split()]
        wn_candidates2 = []
        for wn in wn_candidates:
            if "@" in wn:
                wn_candidates2.append(wn.split("@")[1])
            else:
                wn_candidates2.append(wn)
        wn_list = list(set(wn_candidates2))
        return ret, wn_list

    def wn_exist(self, wn_name):
        if self.test:
            if wn_name == "gcp-test-wn-1core-0001":
                return True
            else:
                return False

        if wn_name in self.wn():
            return True
        else:
            return False

    def wn_status(self):
        if self.test:
            return {"gcp-test-wn-1core-0001": "Claimed"}
        ret, status, err = self.status(["-autoformat", "Name", "State"])
        if ret != 0:
            return ret, {}
        status_dict = {}
        for line in status.splitlines():
            name, status = line.split()
            name = name.split(".")[0]
            if "@" in name:
                name = name.split("@")[1]
            status_dict[name] = status
        return ret, status_dict

    def idle_jobs(self, owners=[], exclude_owners=[]):
        if self.test:
            return [{1: 1}, {}]
        qinfo = self.q(["-allusers", "-global", "-autoformat", "JobStatus",
                        "RequestCpus", "RequestMemory", "Owner"])[1]
        full_idle_jobs = {}
        selected_idle_jobs = {}
        if qinfo == "All queues are empty\n":
            return [full_idle_jobs, selected_idle_jobs]
        for line in qinfo.splitlines():
            status, core, memory, owner = line.split()
            status = int(status)
            core = int(core)
            if status != 1:
                continue
            if core not in full_idle_jobs:
                full_idle_jobs[core] = 0
            full_idle_jobs[core] += 1
            if len(owners) == 0 and len(exclude_owners) == 0:
                continue
            if len(owners) > 0:
                is_owner = 0
                for o in owners:
                    if owner.startswith(o):
                        is_owner = 1
                        break
                if is_owner == 0:
                    continue
            if len(exclude_owners) > 0:
                is_owner = 1
                for o in exclude_owners:
                    if owner.startswith(o):
                        is_owner = 0
                        break
                if is_owner == 0:
                    continue
            if core not in selected_idle_jobs:
                selected_idle_jobs[core] = 0
            selected_idle_jobs[core] += 1
        return [full_idle_jobs, selected_idle_jobs]
