#! /usr/bin/env python

import heapq
import gevent
from gevent import event

class job(object):
    serial = None
    jobid=None
    result=None
    error=None
    done=False
    
    def __init__(self, method, payload=None, priority=0, channel="default", jobid=None):
        self.method = method
        self.payload = payload
        self.priority = priority
        self.channel = channel
        self.progress = {}
        self.jobid = jobid
        self.finish_event = event.Event()
        
    def __cmp__(self, other):
        return cmp((self.priority, self.serial), (other.priority, other.serial))

    def _json(self):
        d = self.__dict__.copy()
        del d["finish_event"]
        return d
    
class workq(object):
    def __init__(self):
        self.channel2q = {}
        
        self.count = 0
        self._waiters = []
        self.id2job = {}

    def report(self):
        import time
        print "=== report %s ===" % (time.ctime(), )
        print "count:", self.count
        busy = []
        for c, todo in self.channel2q.items():
            if todo:
                busy.append((c, len(todo)))
        if busy:
            print "busy channels:"
            todo.sort()
            for c, todo in busy:
                print c, todo
        else:
            print "all channels idle"
            
        print
        
    def waitjobs(self, jobids):
        jobs = [self.id2job[j] for j in jobids]
        for j in jobs:
            j.finish_event.wait()

        return jobs
            
    def finishjob(self, jobid, result=None, error=None):
        j = self.id2job[jobid]
        j.result = result
        j.error = error
        j.done = True
        j.finish_event.set()
        
        
    def updatejob(self, jobid, progress):
        j = self.id2job[jobid]
        j.progress.update(progress)
        
    
                  
    def pushjob(self, job):
        if job.serial is None:
            self.count += 1
            job.serial = self.count
            
        if job.jobid is None:
            job.jobid = job.serial

        self.id2job[job.jobid] = job
        
        channel = job.channel
        
        for i, (watching, ev) in enumerate(self._waiters):
            if channel in watching or not watching:
                del self._waiters[i]
                ev.set(job)
                return job.jobid

        try:
            q = self.channel2q[channel]
        except KeyError:
            q = self.channel2q[channel] = []
            
        heapq.heappush(q, job)
        return job.jobid
        
    def push(self, method, payload=None, priority=0, channel="default", jobid=None):
        if jobid is not None:
            if jobid in self.id2job:
                return jobid
            
        return self.pushjob(job(method=method, payload=payload, priority=priority, channel=channel, jobid=jobid))
        
    def pop(self, channels):
        if not channels:
            try_channels = self.channel2q.keys()
        else:
            try_channels = channels
            
        jobs = []
        for c in try_channels:
            try:
                q = self.channel2q[c]
            except KeyError:
                continue
            if q:
                jobs.append(q[0])
                
        if jobs:
            j = min(jobs)
            heapq.heappop(self.channel2q[j.channel])
        else:
            ev = event.AsyncResult()
            self._waiters.append((channels, ev))
            j = ev.get()
            
        return j