bind = '0.0.0.0:5050'

def pre_request(worker, req):
    worker.log.debug("pre-request-hook pid={} method={} path={}".format(worker.pid, req.method, req.path))

workers = 3
worker_class = 'gthread'
threads = 3
loglevel = 'info'
errorlog = '-'
accesslog = '-'
timeout = 1000
access_log_format = '%(h)s %(l)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s | %(M)s"'
