import psutrischp.wsgi
from twisted.application import internet, service, strports
from twisted.internet import reactor
from twisted.python import threadpool
from twisted.web import resource, server, static, vhost, wsgi


def createWsgiThreadPool():
    wsgiThreadPool = threadpool.ThreadPool()
    reactor.addSystemEventTrigger('after', 'shutdown', wsgiThreadPool.stop)
    wsgiThreadPool.start()
    return wsgiThreadPool


def createRootResource():
    wsgiAsResource = wsgi.WSGIResource(reactor,
                                       createWsgiThreadPool(),
                                       psutrischp.wsgi.application)
    root = resource.Resource()
    root.putChild('', wsgiAsResource)
    root.putChild('freemoney', wsgiAsResource)
    root.putChild('static', static.File('./freemoney/static'))
    return root


def createVirtualHostResource():
    virtual_root = vhost.NameVirtualHost()
    #virtual_root.default = static.File('/var/www/html')
    virtual_root.default = createRootResource() # TODO: set back
    virtual_root.addHost('development.psutrianglescholarship.org',
                         createRootResource())
    return virtual_root


application = service.Application('psutrischp')
sc = service.IServiceCollection(application)
factory = server.Site(createVirtualHostResource())
i = strports.service("tcp:8080", factory)
i.setServiceParent(sc)
