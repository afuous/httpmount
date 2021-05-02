#!/usr/bin/env python3

import fuse
import errno
import os
import stat
import requests
import json
import threading
import collections
import time
import dateutil.parser

fuse.fuse_python_api = (0, 2)

class MyStat(fuse.Stat):
    def __init__(self):
        self.st_mode = 0
        self.st_ino = 0
        self.st_dev = 0
        self.st_nlink = 0
        self.st_uid = 0
        self.st_gid = 0
        self.st_size = 0
        self.st_atime = 0
        self.st_mtime = 0
        self.st_ctime = 0

class Httpmount(fuse.Fuse):

    def __init__(self, *args, **kw):
        fuse.Fuse.__init__(self, *args, **kw)

        self.parser.add_option('-u', '--url', dest='baseurl', help='URL of the httpmount server (required)')
        self.parser.add_option('-p', '--password', dest='password', help='Password for the httpmount server (required)')

        self._baseurl = None
        self._password = None

        self._sess = requests.Session()
        self._cache = {}
        self._cv = threading.Condition()
        self._cacheItems = collections.deque()
        self._cacheExpirationTime = 1.0 # second
        self._uid = os.getuid()
        self._gid = os.getgid()

    def main(self):
        options = self.cmdline[0]
        if (options.baseurl is None) or (options.password is None):
            self.parser.print_help()
        else:
            self._baseurl = options.baseurl
            if self._baseurl[-1] == '/':
                self._baseurl = self._baseurl[:-1]
            self._password = options.password
        fuse.Fuse.main(self)

    def cached_request(self, path):
        started = None
        with self._cv:
            minTime = time.time() - self._cacheExpirationTime
            while len(self._cacheItems) > 0:
                cachedPath, insertTime = self._cacheItems[0]
                if insertTime < minTime and self._cache[cachedPath] is not None:
                    self._cacheItems.popleft()
                    self._cache.pop(cachedPath, None)
                else:
                    break
            if path in self._cache:
                if self._cache[path] is not None:
                    if isinstance(self._cache[path], Exception):
                        raise self._cache[path]
                    else:
                        return self._cache[path]
                else:
                    started = True
            else:
                started = False
                self._cache[path] = None
        if started:
            with self._cv:
                # hack: if request fails, self._cache[path] is set to an exception
                while self._cache[path] is None:
                    self._cv.wait()
                if isinstance(self._cache[path], Exception):
                    raise self._cache[path]
                else:
                    return self._cache[path]
        else:
            res = None
            try:
                res = self._sess.get(self._baseurl + path, headers={'Authorization': self._password}, timeout=5)
            except:
                res = Exception()
            with self._cv:
                # caching errors seems sketchy
                self._cache[path] = res
                self._cacheItems.append((path, time.time()))
                self._cv.notifyAll()
            if isinstance(res, Exception):
                raise res
            else:
                return res


    def open(self, path, flags):
        if (flags & (os.O_RDONLY | os.O_WRONLY | os.O_RDWR)) != os.O_RDONLY:
            return -errno.EACCES
        return 0

    def getattr(self, path):
        st = MyStat()
        st.st_uid = self._uid
        st.st_gid = self._gid
        if path == '/':
            st.st_mode = stat.S_IFDIR | 0o555
            st.st_nlink = 2
        else:
            slash = path.rfind('/')
            dirname = path[:slash]
            basename = path[slash + 1:]
            res = None
            try:
                res = self.cached_request(dirname + '/')
            except:
                return -errno.ETIMEDOUT
            if res.status_code // 100 != 2:
                return -errno.ENOENT
            data = json.loads(res.text)
            found = False
            for obj in data:
                if obj['name'] == basename:
                    if obj['directory']:
                        st.st_mode = stat.S_IFDIR | 0o555
                        st.st_nlink = 2
                    else:
                        st.st_mode = stat.S_IFREG | 0o400
                        st.st_nlink = 1
                        st.st_size = obj['size']
                    if ('atime' in obj) and ('mtime' in obj) and ('ctime' in obj):
                        try:
                            atime = dateutil.parser.parse(obj['atime']).timestamp()
                            mtime = dateutil.parser.parse(obj['mtime']).timestamp()
                            ctime = dateutil.parser.parse(obj['ctime']).timestamp()
                            st.st_atime = atime
                            st.st_mtime = mtime
                            st.st_ctime = ctime
                        except:
                            pass
                    found = True
                    break
            if not found:
                return -errno.ENOENT
        return st

    def read(self, path, size, offset):
        res = None
        try:
            res = self._sess.get(self._baseurl + path, headers={'Authorization': self._password, 'Range': 'bytes=' + str(offset) + '-' + str(offset + size - 1)}, timeout=5)
        except:
            return -errno.ETIMEDOUT
        if res.status_code // 100 != 2:
            return -errno.ENOENT
        return res.content

    def readdir(self, path, offset):
        yield fuse.Direntry('.')
        yield fuse.Direntry('..')
        if path != '/':
            path += '/'
        res = None
        try:
            res = self.cached_request(path)
        except:
            return -errno.ETIMEDOUT
        data = json.loads(res.text)
        for obj in data:
            yield fuse.Direntry(obj['name'])

def main():
    server = Httpmount()
    server.parse(errex=1)
    server.main()

if __name__ == '__main__':
    main()
