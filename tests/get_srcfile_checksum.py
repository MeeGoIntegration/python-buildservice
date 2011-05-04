#!/usr/bin/env python

from buildservice import BuildService

def _get_spec_meta(spec, *args):
    """ This method returns a dictionary which contains the
        requested data.
    """
    import re

    tags = []
    sections = []
    spec_data = {}

    for itm in args:
        if itm.startswith('%'):
            sections.append(itm)
        else:
            tags.append(itm)

    tag_pat = '(?P<tag>^%s)\s*:\s*(?P<val>.*)'
    for tag in tags:
        m = re.compile(tag_pat % tag, re.I | re.M).search(''.join(spec))
        if m and m.group('val'):
            spec_data[tag] = m.group('val').strip()

    section_pat = '^%s\s*?$'
    for section in sections:
        m = re.compile(section_pat % section, re.I | re.M).search(''.join(spec))
        if m:
            start = spec.index(m.group()+'\n') + 1
        data = []
        for line in spec[start:]:
            if line.startswith('%'):
                break
            data.append(line)
        spec_data[section] = data

    return spec_data

def _get_tarball_checksum(obs, prj, pkg):
    """ _get_tarball_checksum(obs, prj, pkg) -> string
        this method firstly get the current name-version of tarball,
        and then return its md5 checksum string
    """
    md5 = ''
    tarball = []
    fl = obs.getSrcFileList(prj, pkg)
    for f in fl:
        if f.endswith('.spec'):
            lines = obs.getSrcFileContent(prj, pkg, f)
        if f.endswith('.tar.gz') or f.endswith('.tar.bz2'):
            tarball.append(f)

    spec_data = _get_spec_meta(lines, 'Name', 'Version')
    for tar in tarball:
        if tar.startswith(spec_data['Name'] + '-' + spec_data['Version']):
            md5 = obs.getSrcFileChecksum(prj, pkg, tar)
            return md5

bs = BuildService(apiurl='http://api.meego.com', oscrc='/etc/boss/oscrc' )

print _get_tarball_checksum(bs, 'Trunk', 'cvs')

