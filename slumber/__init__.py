import posixpath
import urllib

import httplib2

from slumber.serialize import JsonSerializer

__all__ = ["Resource", "Api"]


def uri_join(base, *args):
    """
    Helper function to join an arbitrary number of uri segments together.
    """
    path = base if len(base) else "/"
    path = posixpath.join(path, *[str(x) for x in args])
    return path

class ResourceOptions(object):
    """
    A configuration class for ``Resource``.

    Supplies usable defaults except for ``domain``.
    """

    http = httplib2.Http
    protocol = "http"
    domain = None
    port = None
    uri = "/"
    serializer = JsonSerializer
    append_slash = True

    def __new__(cls, meta=None):
        """
        Override defaults for ``ResourceOptions`` based on an
        arbitrary *class* passed through ``meta``
        """

        attrs = cls.__dict__.copy()

        if meta:
            attrs.update(meta.__dict__.copy())


        return super(ResourceOptions, cls).__new__(type('ResourceOptions', (cls,), attrs))

class ResourceBase(type):

    def __new__(cls, name, bases, attrs):
        # Create a ResourceOptions class from Meta classes, following
        # MRO
        opts = {}
        metas = list(reversed([klass.Meta for klass in bases if hasattr(klass, "Meta")]))
        if 'Meta' in attrs:
            metas.append(attrs.pop('Meta'))
        for meta in metas:
            opts.update(meta.__dict__.copy())

        new_class = super(ResourceBase, cls).__new__(cls, name,
                bases, attrs)
        new_class._meta = ResourceOptions(type('ResourceOptions', (ResourceOptions,), opts))

        return new_class

class Resource(object):
    """
    Resource provides the main functionality behind slumber. It handles the
    attribute -> url, kwarg -> query param, and other related behind the scenes
    python to HTTP transformations. It's goal is to represent a single resource
    which may or may not have children.

    It assumes that a Meta class exists at self._meta with all the required
    attributes.
    """

    __metaclass__ = ResourceBase

    def __getattr__(self, item):
        try:
            return object.__getattr__(item)
        except AttributeError:
            meta = {'uri': uri_join(self._meta.uri, item)}
            clone = self._clone(**meta)
            return clone

    def __call__(self, *args, **kwargs):
        meta = {'uri': uri_join(self._meta.uri, *args)}
        clone = self._clone(**meta)

        return clone

    def build_url(self, foo="bar"):
        base = "%s://%s" % (self._meta.protocol, self._meta.domain)
        if self._meta.port:
            base = "%s:%s" % (base, self._meta.port)

        return "%s%s" % (base, self._meta.uri)

    def _clone(self, **kwargs):
        meta_cls = self._meta.__class__
        meta_attrs = meta_cls.__dict__.copy()
        meta_attrs.update(kwargs)
        meta = type('ResourceOptions', (meta_cls,), meta_attrs)

        cls = self.__class__
        cls_attrs = cls.__dict__.copy()
        cls_attrs['Meta'] = meta
        clone = type('Resource', (cls,), cls_attrs)

        return clone()

    def _get_client(self):
        return self._meta.http()

    def _get_serializer(self):
        return self._meta.serializer()

    def request(self, method, raw=False, **kwargs):
        url = self.build_url()
        client = self._get_client()
        s = self._get_serializer()

        if self._meta.append_slash and not url.endswith("/"):
            url = url + "/"

        headers = {}
        if "headers" in kwargs:
            headers = kwargs.pop("headers")

        body = None
        if "body" in kwargs:
            headers['Content-Type'] = s.get_content_type()
            body = s.dumps(kwargs.pop("body"))

        if kwargs:
            url = "?".join([url, urllib.urlencode(kwargs)])

        # TODO: Throw an exception like the old slumber, but make
        # the exception class act likle urlib2.HTTPErrror
        # See http://docs.python.org/library/urllib2.html#urllib2.HTTPError
        # and also read the source.
        resp, raw_content = client.request(url, method, body=body, headers=headers)
        if raw:
            content = raw_content
        else:
            if raw_content:
                content = s.loads(raw_content)
            else:
                content = None

        return resp, content

    def get(self, **kwargs):
        return self.request("GET", **kwargs)

    def post(self, data, **kwargs):
        return self.request("POST", body=data, **kwargs)

    def put(self, data, **kwargs):
        return self.request("PUT", body=data, **kwargs)

    def delete(self, **kwargs):
        return self.request("DELETE", **kwargs)

def Api(domain, resource_class=Resource, **kwargs):
    # Let's build a ResourceOptions
    meta_attrs =  {'domain': domain}
    meta_attrs.update(kwargs)
    meta = type('ResourceOptions', (ResourceOptions,), meta_attrs)

    cls = type('Resource', (resource_class,), {'Meta': meta})

    return cls()
