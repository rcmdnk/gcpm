# -*- coding: utf-8 -*-

"""
    Module to manage HTCondor information
"""


import htcondor


class Condor(object):

    def __init__(self, test=False):
        self.test = test

    def get_param(self, param):
        if self.test:
            return (-1, "", "")
        return htcondor.param.get(param)

    def update_collector_wn_list(self, wn_list):
        for coll_ad in htcondor.Collector().locateAll(
                htcondor.DaemonTypes.Collector):
            htcondor.send_command(coll_ad, htcondor.DaemonCommands.Reconfig)
            param = htcondor.RemoteParam(coll_ad)
            param.update('WNS', wn_list)

    def reconfig_collector(self, opt=[]):
        if self.test:
            return (-1, "", "")
        for coll_ad in htcondor.Collector().locateAll(
                htcondor.DaemonTypes.Collector):
            htcondor.send_command(coll_ad, htcondor.DaemonCommands.Reconfig)

    def wns(self):
        if self.test:
            return ["gcp-test-wn-1core-000001"]
        wns = htcondor.Collector().query(
            htcondor.AdTypes.Startd,
            projection=['Name'])
        wn_candidates = [x.get('Name').split(".")[0] for x in wns.split()]
        wn_candidates2 = []
        for wn in wn_candidates:
            if "@" in wn:
                wn_candidates2.append(wn.split("@")[1])
            else:
                wn_candidates2.append(wn)
        wn_list = list(set(wn_candidates2))
        return wn_list

    def wn_exist(self, wn_name):
        if self.test:
            if wn_name == "gcp-test-wn-1core-000001":
                return True
            return False

        if wn_name in self.wns():
            return True
        return False

    def wn_status(self):
        if self.test:
            return 0, {"gcp-test-wn-1core-000001": "Claimed"}
        wns = htcondor.Collector().query(
            htcondor.AdTypes.Startd,
            projection=['Name', 'State'])
        status_dict = {}
        for wn in wns:
            name = wn.get('Name')
            status = wn.get('State')
            name = name.split(".")[0]
            if "@" in name:
                name = name.split("@")[1]
            status_dict[name] = status
        return status_dict

    def idle_jobs(self, owners=[], exclude_owners=[]):
        if self.test:
            return [{1: 1}, {}]
        qinfo = []
        for schedd_ad in \
                htcondor.Collector().locateAll(htcondor.DaemonTypes.Schedd):
            schedd = htcondor.Schedd(schedd_ad)
            qinfo += schedd.xquery(
                projection=['RequestCpus', 'Owner'],
                requirements='JobStatus=1')

        full_idle_jobs = {}
        selected_idle_jobs = {}
        for q in qinfo:
            core = int(q.get('RequestCpus'))
            owner = q.get('Owner')
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
