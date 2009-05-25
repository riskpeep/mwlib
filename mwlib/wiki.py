#! /usr/bin/env python

# Copyright (c) 2007-2009 PediaPress GmbH
# See README.txt for additional licensing information.

import os
from ConfigParser import ConfigParser
import StringIO

from mwlib.log import Log

log = Log('mwlib.utils')


def wiki_mwapi(
    base_url=None,
    template_blacklist=None,
    template_exclusion_category=None,
    username=None,
    password=None,
    domain=None,
    script_extension=None,
    **kwargs):
    from mwlib import mwapidb
    return mwapidb.WikiDB(base_url,
        template_blacklist=template_blacklist,
        template_exclusion_category=template_exclusion_category,
        username=username,
        password=password,
        domain=domain,
        script_extension=script_extension,
    )

def wiki_zip(path=None, url=None, name=None, **kwargs):
    from mwlib import zipwiki
    if kwargs:
        log.warn('Unused parameters: %r' % kwargs)
    return zipwiki.Wiki(path)

def wiki_net(articleurl=None, url=None, name=None, imagedescriptionurls=None,
             templateurls=None, templateblacklist=None,
             defaultauthors=None, **kwargs):
    from mwlib import netdb
    
    if templateurls:
        templateurls = [x for x in templateurls.split() if x]
    else:
        raise RuntimeError("templateurls parameter for netdb not set in [wiki] section")
    
    if imagedescriptionurls:
        imagedescriptionurls = [x for x in imagedescriptionurls.split() if x]
    else:
        raise RuntimeError("imagedescriptionurls parameter for netdb not set in [wiki] section")
    
    if defaultauthors:
        defaultauthors = [a.strip() for a in defaultauthors.split(',')]
    
    return netdb.NetDB(articleurl,
        imagedescriptionurls=imagedescriptionurls,
        templateurls=templateurls,
        templateblacklist=templateblacklist,
        defaultauthors=defaultauthors,
    )

def wiki_obsolete_cdb(path=None,  **kwargs):
    raise RuntimeError("cdb file format has changed. please rebuild with mw-buildcdb")

def wiki_nucdb(path=None, lang="en", **kwargs):
    from mwlib import cdbwiki,  nuwiki
    path = os.path.expanduser(path)
    db=cdbwiki.WikiDB(path, lang=lang)
    return nuwiki.adapt(db)

def image_mwapi(
    base_url=None,
    username=None,
    password=None,
    domain=None,
    script_extension=None,
    **kwargs
):
    from mwlib import mwapidb
    return mwapidb.ImageDB(base_url,
        username=username,
        password=password,
        domain=domain,
        script_extension=script_extension,
    )

def image_download(url=None, localpath=None, knownlicenses=None, **kwargs):
    assert url, "must supply url in [images] section"
    from mwlib import netdb

    if localpath:
        localpath = os.path.expanduser(localpath)
    urls = [x for x in url.split() if x]
    assert urls
    
    if knownlicenses:
        knownlicenses = [x for x in knownlicenses.split() if x]
    else:
        knownlicenses = None
    
    imgdb = netdb.ImageDB(urls, cachedir=localpath, knownLicenses=knownlicenses)    
    return imgdb

def image_zip(path=None, **kwargs):
    from mwlib import zipwiki
    if kwargs:
        log.warn('Unused parameters: %r' % kwargs)
    return zipwiki.ImageDB(path)



dispatch = dict(
    images = dict(mwapi=image_mwapi, download=image_download, zip=image_zip),
    wiki = dict(mwapi=wiki_mwapi, cdb=wiki_obsolete_cdb, nucdb=wiki_nucdb, net=wiki_net, zip=wiki_zip)
)

_en_license_url = 'http://en.wikipedia.org/w/index.php?title=Wikipedia:Text_of_the_GNU_Free_Documentation_License&action=raw'
wpwikis = dict(
    de = dict(baseurl='http://de.wikipedia.org/w/', 
              mw_license_url='http://de.wikipedia.org/w/index.php?title=Hilfe:Buchfunktion/Lizenz&action=raw'),
    en = dict(baseurl='http://en.wikipedia.org/w/', mw_license_url=_en_license_url),
    fr = dict(baseurl='http://fr.wikipedia.org/w/', mw_license_url=None),
    es = dict(baseurl='http://es.wikipedia.org/w/', mw_license_url=None),
    pt = dict(baseurl='http://pt.wikipedia.org/w/', mw_license_url=None),
    enwb = dict(baseurl='http://en.wikibooks.org/w', mw_license_url=_en_license_url),
    commons = dict(baseurl='http://commons.wikimedia.org/w/', mw_license_url=_en_license_url)
    )


class Environment(object):
    def __init__(self, metabook=None):
        self.metabook = metabook
        self.images = None
        self.wiki = None
        self.configparser = ConfigParser()
        defaults=StringIO.StringIO("""
[wiki]
name=
url=
""")
        self.configparser.readfp(defaults)
        
    # __getitem__, __setitem__ for compatability (make it look like a dict)
    def __getitem__(self, name):
        if name=='images':
            return self.images
        if name=='wiki':
            return self.wiki
        raise KeyError("Environment.__getitem__ only works for 'wiki' or 'images', not %r" % (name,))
    
    def __setitem__(self, name, val):
        if name=='images':
            self.images = val
        elif name=='wiki':
            self.wiki = val
        else:
            raise KeyError("Environment.__setitem__ only works for 'wiki' or 'images', not %r" % (name,))
    

def _makewiki(conf,
    metabook=None,
    username=None, password=None, domain=None,
    script_extension=None,
):
    res = Environment(metabook)
    
    url = None
    if conf.startswith(':'):
        if conf[1:] not in wpwikis:
            wpwikis[conf[1:]] =  dict(baseurl = "http://%s.wikipedia.org/w/" % conf[1:],
                                      mw_license_url =  None)
            

        url = wpwikis.get(conf[1:])['baseurl']

    if conf.startswith("http://") or conf.startswith("https://"):
        url = conf

    if url:
        res.wiki = wiki_mwapi(url,
            username=username,
            password=password,
            domain=domain,
            script_extension=script_extension,
        )
        res.images = image_mwapi(url,
            username=username,
            password=password,
            domain=domain,
            script_extension=script_extension,
        )
        return res

    if os.path.exists(os.path.join(conf, "siteinfo.json")):
        from mwlib import nuwiki
        res.images = res.wiki = nuwiki.adapt(conf)
        if metabook is None:
            res.metabook = res.wiki.metabook
        
        return res
    
    # yes, I really don't want to type this everytime
    wc = os.path.join(conf, "wikiconf.txt")
    if os.path.exists(wc):
        conf = wc 
        
    if conf.lower().endswith(".zip"):
        import zipfile
        try:
            import simplejson as json
        except ImportError:
            import json
        conf = os.path.abspath(conf)
        
        zf = zipfile.ZipFile(conf)
        try:
            format = json.loads(zf.read("nfo.json"))["format"]
        except KeyError:
            format = "zipwiki"
            
        if format=="nuwiki":
            from mwlib import nuwiki
            res.images = res.wiki = nuwiki.adapt(zf)
            if metabook is None:
                res.metabook = res.wiki.metabook
            return res
        elif format=="zipwiki":
            from mwlib import zipwiki
            res.wiki = zipwiki.Wiki(conf)
            res.images = zipwiki.ImageDB(conf)
            if metabook is None:
                res.metabook = res.wiki.metabook
            return res
        else:
            raise RuntimeError("unknown format %r" % (format,))
        
    

    cp = res.configparser
    
    if not cp.read(conf):
        raise RuntimeError("could not read config file %r" % (conf,))

        
    for s in ['images', 'wiki']:
        if not cp.has_section(s):
            continue
        
        args = dict(cp.items(s))
        if "type" not in args:
            raise RuntimeError("section %r does not have key 'type'" % s)
        t = args['type']
        del args['type']
        try:
            m = dispatch[s][t]
        except KeyError:
            raise RuntimeError("cannot handle type %r in section %r" % (t, s))
        
        res[s] = m(**args)
    
    assert res.wiki is not None, '_makewiki should have set wiki attribute'
    return res

def makewiki(conf,
    metabook=None,
    username=None, password=None, domain=None,
    script_extension=None,
):
    res = _makewiki(conf, metabook,
        username=username,
        password=password,
        domain=domain,
        script_extension=script_extension,
    )
    res.wiki.env = res
    if res.images:
        res.images.env = res
    
    return res
