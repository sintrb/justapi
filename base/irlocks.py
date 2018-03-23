# -*- coding: UTF-8 -*
'''
Created on 2017年5月11日

@author: RobinTang
'''

import multiprocessing, time
class Lock:
    lockmap = {
        }
    globallock = multiprocessing.Lock()
    MAX_LOCK = 300
    DEFAULT_TIMEOUT = 60
    def __init__(self, name='default', timeout=DEFAULT_TIMEOUT):
#         import threading
        self.name = name
        Lock.globallock.acquire()
        if name not in Lock.lockmap:
            print 'new lock', name
            lockd = {
               'lock':multiprocessing.Lock()
            }
            Lock.lockmap[name] = lockd
        else:
            lockd = Lock.lockmap[name]
        lockd['extime'] = time.time() + timeout
        self.lock = lockd['lock']
        Lock.globallock.release()
    @classmethod
    def gc(clz):
        nowtime = time.time()
        Lock.globallock.acquire()
        if len(Lock.lockmap) > Lock.MAX_LOCK:
            keys = list(Lock.lockmap.keys())
            for k in keys:
                ld = Lock.lockmap[k]
                if ld['extime'] <= nowtime:
#                     print 'delete', k, ld['extime']
                    del Lock.lockmap[k]
        Lock.globallock.release()
    def __enter__(self):
#         print 'getting', self.name
        self.lock.acquire()
#         print 'locked', self.name
    def __exit__(self, *unused):
#         print 'released', self.name
        self.lock.release()
        if len(Lock.lockmap) > Lock.MAX_LOCK:
            Lock.gc()


def testrun(name, tid):
#     while True:
    with Lock(tid):
        print name
        time.sleep(1)

if __name__ == '__main__':
    import threading
    for x in range(100):
        threading.Thread(target=testrun, args=(x, 'L%d' % (x))).start()
    for x in range(100):
        threading.Thread(target=testrun, args=(x, 'L%d' % (x * 2))).start()
    for x in range(100):
        threading.Thread(target=testrun, args=(x, 'L%d' % (x * 3))).start()
#     time.sleep(20)
#     for x in range(100):
#         threading.Thread(target=testrun, args=(x, 'L%d' % (x / 2))).start()
#     print len(Lock.lockmap)
    time.sleep(5)
    
    Lock.gc()
    print 'xx', len(Lock.lockmap)
    
