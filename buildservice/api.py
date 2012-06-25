#
# buildservice.py - Buildservice API support for Yabsc
#

# Copyright (C) 2008 James Oakley <jfunk@opensuse.org>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

import os
import tempfile
import time
import urlparse
import urllib2
import xml.etree.cElementTree as ElementTree
from urllib2 import HTTPError
from osc import conf, core
from urllib import quote

prj_link_template = """\
<project name="%(name)s">

  <title>%(title)s</title>
  <description>%(description)s</description>

  <person role="maintainer" userid="%(user)s" />
  <person role="bugowner" userid="%(user)s" />

  <link project="%(link_source)s"/>

  %(repositories)s

</project>
"""

repo_link_template = """\
  <repository name="%(repository)s" linkedbuild="%(build_mech)s">
    <path project="%(link_source)s" repository="%(repository)s" />
    %(archs)s
  </repository>
"""

def flag2bool(flag):
    """
    flag2bool(flag) -> Boolean

    Returns a boolean corresponding to the string 'enable', or 'disable'
    """
    if flag == 'enable':
        return True
    elif flag == 'disable':
        return False

def bool2flag(b):
    """
    bool2flag(b) -> String

    Returns 'enable', or 'disable' according to boolean value b
    """
    if b == True:
        return 'enable'
    elif b == False:
        return 'disable'


class metafile:
    """
    metafile(url, input, change_is_required=False, file_ext='.xml')

    Implementation on osc.core.metafile that does not print to stdout
    """
    def __init__(self, url, input, change_is_required=False, file_ext='.xml'):
        self.url = url
        self.change_is_required = change_is_required

        (fd, self.filename) = tempfile.mkstemp(prefix = 'osc_metafile.', suffix = file_ext, dir = '/tmp')

        f = os.fdopen(fd, 'w')
        f.write(''.join(input))
        f.close()

        self.hash_orig = core.dgst(self.filename)

    def sync(self):
        hash = core.dgst(self.filename)
        if self.change_is_required == True and hash == self.hash_orig:
            os.unlink(self.filename)
            return True

        # don't do any exception handling... it's up to the caller what to do in case
        # of an exception
        core.http_PUT(self.url, file=self.filename)
        os.unlink(self.filename)
        return True

class BuildService():
    "Interface to Build Service API"
    def __init__(self, apiurl=None, oscrc=None):

        try:
            if oscrc:
                conf.get_config(override_conffile = oscrc)
            else:
                conf.get_config()

        except OSError, e:
            if e.errno == 1:
                # permission problem, should be the chmod(0600) issue
                raise RuntimeError, 'Current user has no write permission for specified oscrc: %s' % oscrc

            raise # else

        if apiurl:
            self.apiurl = conf.config['apiurl_aliases'].get(apiurl, apiurl)
        else:
            self.apiurl = conf.config['apiurl']

        if not self.apiurl:
            raise RuntimeError, 'No apiurl "%s" found in %s' % (apiurl, oscrc)

        # Add a couple of method aliases
        self.copyPackage = core.copy_pac
        self.addPerson   = core.addPerson

    def getAPIServerList(self):
        """getAPIServerList() -> list

        Get list of API servers configured in .oscrc
        """
        apiservers = []
        for host in conf.config['api_host_options'].keys():
            apiurl = "%s://%s" % (conf.config['scheme'], host)
        return apiservers

    # the following two alias api are added temporarily for compatible safe
    def is_new_package(self, dst_project, dst_package):
        return self.isNewPackage(dst_project, dst_package)
    def gen_req_info(self, reqid, show_detail = True):
        return self.genRequestInfo(reqid, show_detail)

    def isNewPackage(self, dst_project, dst_package):
        # Check whether the dst pac is a new one
        new_pkg = False
        try:
            core.meta_exists(metatype = 'pkg',
                        path_args = (core.quote_plus(dst_project), core.quote_plus(dst_package)),
                        create_new = False,
                        apiurl = self.apiurl)
        except urllib2.HTTPError, e:
            if e.code == 404:
                new_pkg = True
            else:
                raise e
        return new_pkg

    def genRequestInfo(self, reqid, show_detail = True):
        # helper routine to cat remote file
        def get_source_file_content(apiurl, prj, pac, path, rev):
            revision = core.show_upstream_xsrcmd5(apiurl, prj, pac, revision=rev)
            if revision:
                query = { 'rev': revision }
            else:
                query = None

            u = core.makeurl(apiurl, ['source', prj, pac, core.pathname2url(path)], query=query)

            content = ''
            for buf in core.streamfile(u, core.http_GET, core.BUFSIZE):
                content += buf

            # return unicode str
            return content.decode('utf8')

        req = core.get_request(self.apiurl, reqid)
        try:
            reqinfo = unicode(req)
        except UnicodeEncodeError:
            reqinfo = u''

        if not show_detail:
            return reqinfo

        src_project = req.actions[0].src_project
        src_package = req.actions[0].src_package
        tgt_project = req.actions[0].tgt_project
        tgt_package = req.actions[0].tgt_package
        src_rev = req.actions[0].src_rev

        # Check whether the tgt pac is a new one
        new_pkg = False
        try:
            core.meta_exists(metatype = 'pkg',
                        path_args = (core.quote_plus(tgt_project), core.quote_plus(tgt_package)),
                        create_new = False,
                        apiurl = self.apiurl)
        except urllib2.HTTPError, e:
            if e.code == 404:
                new_pkg = True
            else:
                raise e

        if new_pkg:
            src_fl = core.meta_get_filelist(self.apiurl, src_project, src_package, expand=True, revision=src_rev)

            spec_file = None
            yaml_file = None
            for f in src_fl:
                if f.endswith(".spec"):
                    spec_file = f
                elif f.endswith(".yaml"):
                    yaml_file = f

            reqinfo += 'This is a NEW package in %s project.\n' % tgt_project

            reqinfo += 'The files in the new package:\n'
            reqinfo += '%s/\n' % src_package
            reqinfo += '  |__  ' + '\n  |__  '.join(src_fl)

            if yaml_file:
                reqinfo += '\n\nThe content of the YAML file, %s:\n' % (yaml_file)
                reqinfo += '===================================================================\n'
                reqinfo += get_source_file_content(self.apiurl, src_project, src_package, yaml_file, src_rev)
                reqinfo += '\n===================================================================\n'

            if spec_file:
                reqinfo += '\n\nThe content of the spec file, %s:\n' % (spec_file)
                reqinfo += '===================================================================\n'
                reqinfo += get_source_file_content(self.apiurl, src_project, src_package, spec_file, src_rev)
                reqinfo += '\n===================================================================\n'
            else:
                reqinfo += '\n\nspec file NOT FOUND!\n'

        else:
            try:
                diff = core.server_diff(self.apiurl,
                                    tgt_project, tgt_package, None,
                                    src_project, src_package, src_rev, False)

                try:
                    reqinfo += diff.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        reqinfo += diff.decode('iso-8859-1')
                    except UnicodeDecodeError:
                        pass

            except urllib2.HTTPError, e:
                e.osc_msg = 'Diff not possible'

        # the result, in unicode string
        return reqinfo

    def getUserData(self, user, *tags):
        """getUserData() -> str

        Get the user data
        """
        return core.get_user_data(self.apiurl, user, *tags)

    def getUserName(self):
        """getUserName() -> str

        Get the user name associated with the current API server
        """
        return conf.config['api_host_options'][self.apiurl]['user']

    def getProjectList(self):
        """getProjectList() -> list

        Get list of projects
        """
        return [project for project in core.meta_get_project_list(self.apiurl) if project != 'deleted']

    def getWatchedProjectList(self):
        """getWatchedProjectList() -> list

        Get list of watched projects
        """
        username = self.getUserName()
        tree = ElementTree.fromstring(''.join(core.get_user_meta(self.apiurl, username)))
        projects = []
        watchlist = tree.find('watchlist')
        if watchlist:
            for project in watchlist.findall('project'):
                projects.append(project.get('name'))
        homeproject = 'home:%s' % username
        if not homeproject in projects and homeproject in self.getProjectList():
            projects.append(homeproject)
        return projects

    def watchProject(self, project):
        """
        watchProject(project)

        Watch project
        """
        username = self.getUserName()
        data = core.meta_exists('user', username, create_new=False, apiurl=self.apiurl)
        url = core.make_meta_url('user', username, self.apiurl)

        person = ElementTree.fromstring(''.join(data))
        watchlist = person.find('watchlist')
        if not watchlist:
            watchlist = ElementTree.SubElement(person, 'watchlist')
        ElementTree.SubElement(watchlist, 'project', name=str(project))

        f = metafile(url, ElementTree.tostring(person))
        f.sync()

    def unwatchProject(self, project):
        """
        watchProject(project)

        Watch project
        """
        username = self.getUserName()
        data = core.meta_exists('user', username, create_new=False, apiurl=self.apiurl)
        url = core.make_meta_url('user', username, self.apiurl)

        person = ElementTree.fromstring(''.join(data))
        watchlist = person.find('watchlist')
        for node in watchlist:
            if node.get('name') == str(project):
                watchlist.remove(node)
                break

        f = metafile(url, ElementTree.tostring(person))
        f.sync()

    def getRepoState(self, project):
        targets = {}
        results = core.show_prj_results_meta(self.apiurl, project)
        if not results:
            return {}
        tree = ElementTree.fromstring(''.join(results))
        for result in tree.findall('result'):
            target = '%s/%s' % (result.get('repository'), result.get('arch'))
            if result.get("dirty") == "true":
                # If the repository is dirty state needs recalculation and
                # cannot be trusted
                state = "dirty"
            else:
                state = result.get('state')
            targets[target] = state
        return targets

    def getResults(self, project):
        """getResults(project) -> (dict, list)

        Get results of a project. Returns (results, targets)

        results is a dict, with package names as the keys, and lists of result codes as the values

        targets is a list of targets, corresponding to the result code lists
        """
        results = core.show_prj_results_meta(self.apiurl, project)
        tree = ElementTree.fromstring(''.join(results))
        results = {}
        targets = []
        for result in tree.findall('result'):
            targets.append('/'.join((result.get('repository'), result.get('arch'))))
            for status in result.findall('status'):
                package = status.get('package')
                code = status.get('code')
                if not package in results:
                    results[package] = []
                results[package].append(code)
        return (results, targets)

    def getDiff(self, sprj, spkg, dprj, dpkg, rev):
        diff = ''
        diff += core.server_diff(self.apiurl, sprj, spkg, None,
                 dprj, dpkg, rev, False, True)
        return diff

    def getTargets(self, project):
        """
        getTargets(project) -> list

        Get a list of targets for a project
        """
        targets = []
        tree = ElementTree.fromstring(''.join(core.show_project_meta(self.apiurl, project)))
        for repo in tree.findall('repository'):
            for arch in repo.findall('arch'):
                targets.append('%s/%s' % (repo.get('name'), arch.text))
        return targets

    def getPackageStatus(self, project, package):
        """
        getPackageStatus(project, package) -> dict

        Returns the status of a package as a dict with targets as the keys and status codes as the
        values
        """
        status = {}
        tree = ElementTree.fromstring(''.join(core.show_results_meta(self.apiurl, project, package)))
        for result in tree.findall('result'):
            target = '/'.join((result.get('repository'), result.get('arch')))
            statusnode = result.find('status')
            if statusnode is not None:
                code = statusnode.get('code')
                details = statusnode.find('details')
                if details is not None:
                    code += ': ' + details.text
            else:
                code = "unknown"
            status[target] = code
        return status

    def getProjectDiff(self, src_project, dst_project):
        packages = self.getPackageList(src_project)
        for src_package in packages:
            diff = core.server_diff(self.apiurl,
                                dst_project, src_package, None,
                                src_project, src_package, None, False)
            print diff

    def getPackageList(self, prj, deleted=None):
        query = {}
        if deleted:
           query['deleted'] = 1

        u = core.makeurl(self.apiurl, ['source', prj], query)
        f = core.http_GET(u)
        root = ElementTree.parse(f).getroot()
        return [ node.get('name') for node in root.findall('entry') ]

    def getBinaryList(self, project, target, package):
        """
        getBinaryList(project, target, package) -> list

        Returns a list of binaries for a particular target and package
        """
        (repo, arch) = target.split('/')
        return core.get_binarylist(self.apiurl, project, repo, arch, package)

    def getBinary(self, project, target, package, file, path):
        """
        getBinary(project, target, file, path)

        Get binary 'file' for 'project' and 'target' and save it as 'path'
        """
        (repo, arch) = target.split('/')
        core.get_binary_file(self.apiurl, project, repo, arch, file, target_filename=path, package=package)

    def getBinaryInfo(self, project, target, package, binary, ext=False):
        """
        getBinaryInfo(project, target, package, binary, ext=False)

        Get binary info for 'project', 'package' and 'target'

        If ext=True get the info from build result (slower)
        """
        (repo, arch) = target.split('/')
        cmd = "?view=fileinfo"
        if ext:
            cmd += "_ext"
        u = core.makeurl(self.apiurl, ['build', project, repo, arch,
                package, binary, cmd])
        f = core.http_GET(u)
        fileinfo = ElementTree.parse(f).getroot()
        result = {"provides": []}
        for node in fileinfo.getchildren():
            if node.tag == "provides":
                result[node.tag].append(node.text)
            else:
                result[node.tag] = node.text
        return result

    def getBuildLog(self, project, target, package, offset=0):
        """
        getBuildLog(project, target, package, offset=0) -> str

        Returns the build log of a package for a particular target.

        If offset is greater than 0, return only text after that offset. This allows live streaming
        """
        (repo, arch) = target.split('/')
        u = core.makeurl(self.apiurl, ['build', project, repo, arch, package, '_log?nostream=1&start=%s' % offset])
        return core.http_GET(u).read()

    def getWorkerStatus(self):
        """
        getWorkerStatus() -> list of dicts

        Get worker status as a list of dictionaries. Each dictionary contains the keys 'id',
        'hostarch', and 'status'. If the worker is building, the dict will additionally contain the
        keys 'project', 'package', 'target', and 'starttime'
        """
        url = core.makeurl(self.apiurl, ['build', '_workerstatus'])
        f = core.http_GET(url)
        tree = ElementTree.parse(f).getroot()
        workerstatus = []
        for worker in tree.findall('building'):
            d = {'id': worker.get('workerid'),
                 'status': 'building'}
            for attr in ('hostarch', 'project', 'package', 'starttime'):
                d[attr] = worker.get(attr)
            d['target'] = '/'.join((worker.get('repository'), worker.get('arch')))
            d['started'] = time.asctime(time.localtime(float(worker.get('starttime'))))
            workerstatus.append(d)
        for worker in tree.findall('idle'):
            d = {'id': worker.get('workerid'),
                 'hostarch': worker.get('hostarch'),
                 'status': 'idle'}
            workerstatus.append(d)
        return workerstatus

    def getWaitStats(self):
        """
        getWaitStats() -> list

        Returns the number of jobs in the wait queue as a list of (arch, count)
        pairs
        """
        url = core.makeurl(self.apiurl, ['build', '_workerstatus'])
        f = core.http_GET(url)
        tree = ElementTree.parse(f).getroot()
        stats = []
        for worker in tree.findall('waiting'):
            stats.append((worker.get('arch'), int(worker.get('jobs'))))
        return stats

    def getSubmitRequests(self):
        """
        getSubmitRequests() -> list of dicts

        """
        url = core.makeurl(self.apiurl, ['search', 'request', '?match=submit'])
        f = core.http_GET(url)
        tree = ElementTree.parse(f).getroot()
        submitrequests = []
        for sr in tree.findall('request'):
            if sr.get('type') != "submit":
                continue

            d = {'id': int(sr.get('id'))}
            sb = sr.findall('submit')[0]
            src = sb.findall('source')[0]
            d['srcproject'] = src.get('project')
            d['srcpackage'] = src.get('package')
            dst = sb.findall('target')[0]
            d['dstproject'] = dst.get('project')
            d['dstpackage'] = dst.get('package')
            d['state'] = sr.findall('state')[0].get('name')

            submitrequests.append(d)
        submitrequests.sort(key=lambda x: x['id'])
        return submitrequests

    def rebuild(self, project, package, target=None, code=None):
        """
        rebuild(project, package, target, code=None)

        Rebuild 'package' in 'project' for 'target'. If 'code' is specified,
        all targets with that code will be rebuilt
        """
        if target:
            (repo, arch) = target.split('/')
        else:
            repo = None
            arch = None
        return core.rebuild(self.apiurl, project, package, repo, arch, code)

    def abortBuild(self, project, package=None, target=None):
        """
        abort(project, package=None, target=None)

        Abort build of a package or all packages in a project
        """
        if target:
            (repo, arch) = target.split('/')
        else:
            repo = None
            arch = None
        return core.abortbuild(self.apiurl, project, package, arch, repo)

    def getBuildHistory(self, project, package, target):
        """
        getBuildHistory(project, package, target) -> list

        Get build history of package for target as a list of tuples of the form
        (time, srcmd5, rev, versrel, bcnt)
        """
        (repo, arch) = target.split('/')
        u = core.makeurl(self.apiurl, ['build', project, repo, arch, package, '_history'])
        f = core.http_GET(u)
        root = ElementTree.parse(f).getroot()

        r = []
        for node in root.findall('entry'):
            rev = int(node.get('rev'))
            srcmd5 = node.get('srcmd5')
            versrel = node.get('versrel')
            bcnt = int(node.get('bcnt'))
            t = time.localtime(int(node.get('time')))
            t = time.strftime('%Y-%m-%d %H:%M:%S', t)

            r.append((t, srcmd5, rev, versrel, bcnt))
        return r

    def getCommitLog(self, project, package, revision=None):
        """
        getCommitLog(project, package, revision=None) -> list

        Get commit log for package in project. If revision is set, get just the
        log for that revision.

        Each log is a tuple of the form (rev, srcmd5, version, time, user,
        comment)
        """
        u = core.makeurl(self.apiurl, ['source', project, package, '_history'])
        f = core.http_GET(u)
        root = ElementTree.parse(f).getroot()

        r = []
        revisions = root.findall('revision')
        revisions.reverse()
        for node in revisions:
            rev = int(node.get('rev'))
            if revision and rev != int(revision):
                continue
            srcmd5 = node.find('srcmd5').text
            version = node.find('version').text
            user = node.find('user').text
            try:
                comment = node.find('comment').text
            except:
                comment = '<no message>'
            t = time.localtime(int(node.find('time').text))
            t = time.strftime('%Y-%m-%d %H:%M:%S', t)

            r.append((rev, srcmd5, version, t, user, comment))
        return r

    def getProjectMeta(self, project):
        """
        getProjectMeta(project) -> string

        Get XML metadata for project
        """
        return ''.join(core.show_project_meta(self.apiurl, project))

    def getProjectData(self, project, tag):
        """
        getProjectData(project, tag) -> list
        
        Return a string list if node has text, else return the values dict list
        """
        data = []
        tree = ElementTree.fromstring(self.getProjectMeta(project))
        nodes = tree.findall(tag)
        if nodes:
            for node in nodes:
                node_value = {}
                for key in node.keys():
                    node_value[key] = node.get(key)

                if node_value:
                    data.append(node_value)
                else:
                    data.append(node.text)

        return data

    def getProjectPersons(self, project, role):
        """
        getProjectPersons(project, role) -> list
        
        Return a userid list in this project with this role
        """
        userids = []
        persons = self.getProjectData(project, 'person')
        for person in persons:
            if person.has_key('role') and person['role'] == role:
                userids.append(person['userid'])

        return userids

    def getProjectDevel(self, project):
        """
        getProjectDevel(project) -> tuple (devel_prj, devel_pkg)

        Return the devel tuple of a project if it has the node, else return None
        """
        devels = self.getProjectData(project, 'devel')
        for devel in devels:
            if devel.has_key('project') and devel.has_key('package'):
                return (devel['project'], devel['package'])

        return None

    def deleteProject(self, project):
        """
        deleteProject(project)
        
        Delete the specific project
        """
        try:
            core.delete_project(self.apiurl, project)
        except Exception:
            return False
            
        return True

    def getPackageMeta(self, project, package):
        """
        getPackageMeta(project, package) -> string

        Get XML metadata for package in project
        """
        return ''.join(core.show_package_meta(self.apiurl, project, package))

    def getPackageData(self, project, package, tag):
        """
        getPackageData(project, package, tag) -> list
        
        Return a string list if node has text, else return the values dict list
        """
        data = []
        tree = ElementTree.fromstring(self.getPackageMeta(project, package))
        nodes = tree.findall(tag)
        if nodes:
            for node in nodes:
                node_value = {}
                for key in node.keys():
                    node_value[key] = node.get(key)

                if node_value:
                    data.append(node_value)
                else:
                    data.append(node.text)

        return data

    def getPackagePersons(self, project, package, role):
        """
        getPackagePersons(project, package, role) -> list
        
        Return a userid list in the package with this role
        """
        userids = []
        persons = self.getPackageData(project, package, 'person')
        for person in persons:
            if person.has_key('role') and person['role'] == role:
                userids.append(person['userid'])

        return userids

    def getPackageDevel(self, project, package):
        """
        getPackageDevel(project, package) -> tuple (devel_prj, devel_pkg)
        
        Return the devel tuple of a package if it has the node, else return None
        """
        devels = self.getPackageData(project, package, 'devel')
        for devel in devels:
            if devel.has_key('project') and devel.has_key('package'):
                return (devel['project'], devel['package'])

        return None

    def deletePackage(self, project, package):
        """
        deletePackage(project, package)
        
        Delete the specific package in project
        """
        try:
            core.delete_package(self.apiurl, project, package)
        except Exception:
            return False
            
        return True

    def projectFlags(self, project):
        """
        projectFlags(project) -> ProjectFlags

        Return a ProjectFlags object for manipulating the flags of project
        """
        return ProjectFlags(self, project)

    def getUserEmail(self, user):
        """
        getUserEmail(userid) -> string

        Get email of a user ID
        """
        user_data = self.getUserData(user, "email")
        if user_data:
            return user_data[0]
        else:
            return ""

    def getProjectMaintainers(self, project):
        """
        getProjectMaintainers(project) -> list

        Get a list of userids who are maintainers of a project
        """
        tree = ElementTree.fromstring(''.join(core.show_project_meta(self.apiurl,
                                      project)))
        maintainers = []
        for person in tree.findall('person'):
            if person.get('role') == "maintainer":
                maintainers.append(person.get('userid'))
        return maintainers

    def isMaintainer(self, project, user):
        """
        isMaintainer(project, user) -> Bool

        returns True if the user is a maintainer in the project False otherwise
        """
        maintainers = self.getProjectMaintainers(project)
        if user in maintainers:
            return True
        return False

    def getPackageChecksum(self, project, package, rev=None):
        """
        getPackageChecksum(self, project, package, rev=None) -> string

        returns source md5 of a package
        """
        query = { 'expand' : 1 }
        if rev:
            query['rev'] = rev
        else:
            query['rev'] = 'latest'
    
        u = core.makeurl(self.apiurl, ['source', project, package], query=query)
        f = core.http_GET(u)
        root = ElementTree.parse(f).getroot()
        return root.get("srcmd5")

    def hasChanges(self, oprj, opkg, orev, tprj, tpkg):
        """
        hasChanges(self, oprj, opkg, orev, tprj, tpkg) -> Bool

        Compares the source md5sum of the whole source and target packages
        If target package does not exist, change is assumed.
        Returns False if there is no change, otherwise returns True
        """
        try:
            tsrcmd5 = self.getPackageChecksum(tprj, tpkg)
        except urllib2.HTTPError, e:
            if e.code == 404:
                return True
            else:
                raise
        osrcmd5 = self.getPackageChecksum(oprj, opkg, rev=orev)
        if osrcmd5 == tsrcmd5:
            return False
        return True

    def getProjectRepositories(self, project):
        """
        getProjectRepositories(project) -> list

        Get a list of repositories in a project
        """
        repos = []
        tree = ElementTree.fromstring(''.join(core.show_project_meta(self.apiurl, project)))
        for repo in tree.findall('repository'):
            repos.append(repo.get("name"))
        return repos

    def getRepositoryTargets(self, project, repository):
        """
        getRepositoryTargets(project, repository) -> list

        Get a list of targets for a repository in a project
        """
        targets = []
        tree = ElementTree.fromstring(''.join(core.show_project_meta(self.apiurl, project)))
        for repo in tree.findall('repository'):
            if repo.get("name") == repository:
                for path in repo.findall("path"):
                    targets.append("%s/%s" % (path.get("project"), path.get("repository")))
        return targets

    def getRepositoryArchs(self, project, repository):
        """
        getRepositoryArchs(project, repository) -> list

        Get a list of architectures for a repository in a project
        """
        archs = []
        tree = ElementTree.fromstring(''.join(core.show_project_meta(self.apiurl, project)))
        for repo in tree.findall('repository'):
            if repo.get("name") == repository:
                for arch in repo.findall("arch"):
                    archs.append("%s" % (arch.text))
        return archs

    def isPackageSucceeded(self, project, repository, pkg, arch):
        results = core.get_package_results(self.apiurl, project, pkg, 
                                           repository = [repository],
                                           arch=[arch])
        for result in results:
            if result['code'] != "succeeded":
                return False
            return True

    def getPackageDepends(self, project, repository, pkg, arch, query):
        p = []
        xml = core.get_dependson(self.apiurl, project, repository, arch, 
                                 packages=[pkg], reverse=True)
        tree =  ElementTree.fromstring(''.join(xml))
        for package in tree.findall('package'):
            for dep in package.findall(query):
                p.append(dep.text)
        return p

    def getPackageSubpkgs(self, project, repository, pkg, arch):
        return self.getPackageDepends(self, project, repository, pkg, arch,
                "subpkg")

    def getPackageReverseDepends(self, project, repository, pkg, arch):
        return self.getPackageDepends(self, project, repository, pkg, arch,
                "pkgdep")

    def getPackageRev(self, project, pkg):
        xml = core.show_files_meta(self.apiurl, project, pkg, expand=True)
        tree =  ElementTree.fromstring(''.join(xml))
        return tree.get("rev")

    def getPackageFileList(self, project, pkg, revision=None):
        if not revision:
            revision = self.getPackageRev(project, pkg)

        return core.meta_get_filelist(self.apiurl, project, pkg,
                                          expand=True, revision=revision)

    def getFile(self, project, pkg, filename, revision=None):
        data = ""
        if not revision:
            revision = self.getPackageRev(project, pkg)

        u = core.makeurl(self.apiurl, ['source', project, pkg, quote(filename)],
                             query={"rev":revision, "expand":1})
        for chunks in core.streamfile(u):
            data += chunks
        return data

    def isType(self, name, is_type):
        try:
            u = core.makeurl(self.apiurl, [is_type, name])
            f = core.http_GET(u)
            return True
        except HTTPError as err:
            if err.code == 404:
                return False
            raise

    def getType(self, name):
        if self.isType(name, "group"):
            objtype = "group"
        elif self.isType(name, "person"):
            objtype = "user"
        elif name in self.getProjectList():
            objtype = "project"
        else:
            objtype = "unknown"
        return objtype

    def addReview(self, rid, msg, reviewer):
        reviewer_type = self.getType(reviewer)
        if reviewer_type == "unknown":
            raise RuntimeError("Reviewer %s is not a person,"\
                               " group or project" % reviewer)

        by_type = "by_%s" % reviewer_type
        query = {'cmd': 'addreview', by_type : reviewer }
        u = core.makeurl(self.apiurl, ['request', rid], query=query)
        f = core.http_POST(u, data=msg)
        root = ElementTree.parse(f).getroot()
        ret = root.get('code')
        if ret == "ok":
            return True
        else:
            return False

    def setReviewState(self, rid, new_state, msg, user):
        ret = core.change_review_state(self.apiurl, rid, new_state,
                                        message=msg, by_user=user)
        if ret == "ok":
            return True
        else:
            return False

    def setRequestState(self, rid, new_state, msg):
         ret = core.change_request_state(self.apiurl, rid, new_state, message=msg)
         if ret == "ok":
             return True
         else:
             return False

    def wipeBinaries(self, project):
        core.wipebinaries(self.apiurl, project)

    def getPackageResults(self, project, repository, pkg, arch):
        return core.get_package_results(self.apiurl, project, pkg,
                                        repository=[repository],
                                        arch=[arch])[0]

    def getTargetRepo(self, prj, target_project, target_repository,
                      target_archs):
        """ Find a repo that builds only against one target for certain
            archs """

        target = "%s/%s" % (target_project, target_repository)
        prj_repos = self.getProjectRepositories(prj)
        if prj_repos:
            for repo in prj_repos:
                repo_targets = self.getRepositoryTargets(prj, repo)
                if len(repo_targets) == 1:
                    if target in repo_targets:
                        repo_archs = self.getRepositoryArchs(prj, repo)
                        if set(target_archs).issubset(repo_archs):
                            return repo
        return False

    def getProjectResults(self, project):
        results = core.show_prj_results_meta(self.apiurl, project)
        if not results:
            return {}
        tree = ElementTree.fromstring(''.join(results))
        results = {}
        for result in tree.findall('result'):
            target = '/'.join((result.get('repository'), result.get('arch')))
            results[target] = {}
            for status in result:
                pkg = status.get("package")
                code = status.get("code")
                results[target][pkg] = code

        return results

    def getRepoResults(self, project, repository):
        repo_results = {}
        prj_results = self.getProjectResults(project)
        for repo_arch , result in prj_results.items():
            repo , arch = repo_arch.split("/")
            if repo == repository:
                repo_results[arch] = result

        return repo_results

    def createProjectLink(self, link_source, repolinks, link_target):
        repositories = ""
        for repo, archs in repolinks.iteritems():
            arch_string = ""
            for arch in archs:
                arch_string += "<arch>%s</arch>" % arch
            repositories += repo_link_template % dict(
                repository=repo,
                build_mech="localdep",
                link_source=link_source,
                archs=arch_string
                )
        meta = prj_link_template % dict(
            link_source=link_source,
            name=link_target,
            user=self.getUserName(),
            title="Project link to %s" % link_source,
            description="",
            repositories=repositories,
            )
        u = core.makeurl(self.apiurl, ['source', link_target, '_meta'])
        f = core.http_PUT(u, data=meta)
        root = ElementTree.parse(f).getroot()
        ret = root.get('code')
        if ret == "ok":
            return True
        else:
            return False

    def projectAttributeExists(self, project, attribute):
        u = core.makeurl(self.apiurl, ['source',
                                       project,
                                       '_attribute'])
        f = core.http_GET(u)
        xml = ElementTree.parse(f).getroot()
        return attribute in [child.get('name') for child in xml.getchildren()]

    def createProjectAttribute(self, project, attribute):
        u = core.makeurl(self.apiurl, ['source',
                                       project,
                                       '_attribute'])
        xml = """
        <attributes>
        <attribute namespace='OBS' name='%s'>
        </attribute>
        </attributes>
        """%attribute
        f = core.http_POST(u, data=xml)
        root = ElementTree.parse(f).getroot()
        ret = root.get('code')
        if ret == "ok":
            return True
        else:
            return False

    def deleteProjectAttribute(self, project, attribute):
        u = core.makeurl(self.apiurl, ['source',
                                           project,
                                           '_attribute',
                                           'OBS:%s'%attribute])
        try:
            f = core.http_DELETE(u)
        except HTTPError:
            return False
        root = ElementTree.parse(f).getroot()
        ret = root.get('code')
        if ret == "ok":
            return True
        else:
            return False
    # Series of methods to convert some objects to dicts
    # in order to emit as json.
    # FIXME: should migrate to core
    def req_to_dict(self, req, action_diff=False):
        """serialize Request object to a dict
        Includes Action diffs if action_diff is True
        """
        root = {}
        if not req.reqid is None:
            root['id'] = req.reqid
        for action in req.actions:
            if 'actions' not in root:
                root['actions'] = []
            root['actions'].append(self.action_to_dict(action, diff=action_diff))
        if not req.state is None:
            root['state'] = self.state_to_dict(req.state)
        for review in req.reviews:
            if 'reviews' not in root:
                root['reviews'] = []
            root['reviews'].append(self.review_to_dict(review))
        for hist in req.statehistory:
            if 'statehistory' not in root:
                root['statehistory'] = []
            root['statehistory'].append(self.hist_to_dict(hist))
        if req.title:
            root['title'] = req.title
        if req.description:
            root['description'] = req.description
        return root

    def action_to_dict(self, action, diff=False):
        """serialize Action object to a dict"""
        root={}
        root['type'] = action.type

        for i in core.Action.type_args[action.type]:
            prefix, attr = i.split('_', 1)
            val = getattr(action, i)
            if val is None:
                continue
            elm = core.Action.prefix_to_elm.get(prefix, prefix)
            if elm not in root:
                root[elm]={}
            if prefix == 'opt':
                root['options'][attr] = val
            else:
                root[elm][attr] = val
        if diff and action.type == "submit":
            thediff = self.submit_action_diff(action)
            try:
                root['diff'] = thediff.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    root['diff'] = thediff.decode('iso-8859-1')
                except UnicodeDecodeError:
                    root['diff'] = "Diff could not be decoded"
        return root


    def submit_action_diff(self, action):
        """Replaces core.submit_action_diff() to work with new packages"""
        new_pkg = False
        try:
            # if target package does not exists this is new package
            core.meta_exists(apiurl=self.apiurl, metatype='pkg',
                    create_new=False, path_args=(
                        core.quote_plus(action.tgt_project),
                        core.quote_plus(action.tgt_package)
                    ))
        except urllib2.HTTPError, e:
            if e.code == 404:
                new_pkg = True
            else:
                raise
        if new_pkg:
            action.tgt_package = None

        try:
            return core.server_diff(self.apiurl, action.tgt_project,
                    action.tgt_package, None, action.src_project,
                    action.src_package, action.src_rev,
                    unified=False, missingok=True)
        except urllib2.HTTPError, e:
            try:
                reason = core.ET.fromstring(e.read()).find("summary").text
            except Exception:
                reason = "Unknown reason"
            return "Error getting diff %s/%s <-> %s/%s rev %s\n%s" % \
                    (action.tgt_project, action.tgt_package, action.src_project,
                            action.src_package, action.src_rev, reason)


    def state_to_dict(self, state):
        """serialize Abstractstate object to a dict"""
        root={}
        root['state'] = state.get_node_name()
        for attr in state.get_node_attrs():
            val = getattr(state, attr)
            if not val is None:
                root[attr] = val
        if state.get_comment():
            root['comment'] = state.get_comment()
        return root

    def review_to_dict(self, review):
        return(self.state_to_dict(review))

    def hist_to_dict(self, hist):
        return(self.state_to_dict(hist))

    def getProjectPatternsList(self, project):
        url = core.makeurl(self.apiurl,
                           ['source', project, '_pattern'])
        response = core.http_GET(url)
        root = ElementTree.parse(response).getroot()
        return [ node.get('name') for node in root.findall('entry') ]
        
    def setProjectPattern(self, project, pattern, name=None):
        with open(pattern) as body:
            if not name:
                name = os.path.basename(pattern)
            url = core.makeurl(self.apiurl,
                               ['source', project, '_pattern', name])
            response = core.http_PUT(url, data=body.read())
            ret = ElementTree.parse(response).getroot().get('code')
            return ret == "ok"

    def deleteProjectPattern(self, project, name):
        url = core.makeurl(self.apiurl,
                           ['source', project, '_pattern', name])
        core.http_DELETE(url)
        return True
        
    def getGroupUsers(self, group):
        u = core.makeurl(self.apiurl, ["group", group])
        try:
            f = core.http_GET(u)
            root = ElementTree.parse(f).getroot()
            users = []
            # weirdness in the OBS api person subelements are
            # wrapped in a person subelement
            for person in root.findall("person")[0].findall("person"):
                if person.get("userid"):
                    users.append(person.get("userid"))
            return users
        except urllib2.HTTPError as e:
            if e.code == 404:
                return []
            else:
                raise

    def putFile(self, project, pkg, filename, filepath):

        u = core.makeurl(self.apiurl, ['source', project, pkg, quote(filename)])
        core.http_PUT(u, file=filepath)

    def getCreatePackage(self, dst_project, dst_package):
        # Check whether the dst pac is a new one
        pkg = core.meta_exists(metatype = 'pkg',
                        path_args = (core.quote_plus(dst_project), core.quote_plus(dst_package)),
                        create_new = True,
                        template_args = { "name" : dst_package, "user" : self.getUserName() },
                        apiurl = self.apiurl)
        u = core.makeurl(self.apiurl, ['source', dst_project, dst_package, "_meta"])
        core.http_PUT(u, data="".join(pkg))

    def setupService(self, dst_project, dst_package, service):
        u = core.makeurl(self.apiurl, ['source', dst_project, dst_package, "_service"])
        core.http_PUT(u, data=service)


class ProjectFlags(object):
    """
    ProjectFlags(bs, project)

    Represents the flags in project through the BuildService object bs
    """
    def __init__(self, bs, project):
        self.bs = bs
        self.tree = ElementTree.fromstring(self.bs.getProjectMeta(project))

        # The "default" flags, when undefined
        self.defaultflags = {'build': True,
                             'publish': True,
                             'useforbuild': True,
                             'debuginfo': False}

        # Figure out what arches and repositories are defined
        self.arches = {}
        self.repositories = {}

        # Build individual repository list
        for repository in self.tree.findall('repository'):
            repodict = {'arches': {}}
            self.__init_flags_in_dict(repodict)
            for arch in repository.findall('arch'):
                repodict['arches'][arch.text] = {}
                self.__init_flags_in_dict(repodict['arches'][arch.text])
                # Add placeholder in global arches
                self.arches[arch.text] = {}
            self.repositories[repository.get('name')] = repodict

        # Initialise flags in global arches
        for archdict in self.arches.values():
            self.__init_flags_in_dict(archdict)

        # A special repository representing the global and global arch flags
        self.allrepositories = {'arches': self.arches}
        self.__init_flags_in_dict(self.allrepositories)

        # Now populate the structures from the xml data
        for flagtype in ('build', 'publish', 'useforbuild', 'debuginfo'):
            flagnode = self.tree.find(flagtype)
            if flagnode:
                for node in flagnode:
                    repository = node.get('repository')
                    arch = node.get('arch')

                    if repository and arch:
                        self.repositories[repository]['arches'][arch][flagtype] = flag2bool(node.tag)
                    elif repository:
                        self.repositories[repository][flagtype] = flag2bool(node.tag)
                    elif arch:
                        self.arches[flagtype] = flag2bool(node.tag)
                    else:
                        self.allrepositories[flagtype] = flag2bool(node.tag)

    def __init_flags_in_dict(self, d):
        """
        __init_flags_in_dict(d)

        Initialize all build flags to None in d
        """
        d.update({'build': None,
                  'publish': None,
                  'useforbuild': None,
                  'debuginfo': None})

    def save(self):
        """
        save()

        Save flags
        """

        for flagtype in ('build', 'publish', 'useforbuild', 'debuginfo'):
            # Clear if set
            flagnode = self.tree.find(flagtype)
            if flagnode:
                self.tree.remove(flagnode)

            # Generate rule nodes
            rulenodes = []

            # globals
            if self.allrepositories[flagtype] != None:
                rulenodes.append(ElementTree.Element(bool2flag(self.allrepositories[flagtype])))
            for arch in self.arches:
                if self.arches[arch][flagtype] != None:
                    rulenodes.append(ElementTree.Element(bool2flag(self.arches[arch][flagtype]), arch=arch))

            # repositories
            for repository in self.repositories:
                if self.repositories[repository][flagtype] != None:
                    rulenodes.append(ElementTree.Element(bool2flag(self.repositories[repository][flagtype]), repository=repository))
                for arch in self.repositories[repository]['arches']:
                    if self.repositories[repository]['arches'][arch][flagtype] != None:
                        rulenodes.append(ElementTree.Element(bool2flag(self.repositories[repository]['arches'][arch][flagtype]), arch=arch, repository=repository))

            # Add nodes to tree
            if rulenodes:
                from pprint import pprint
                pprint(rulenodes)
                flagnode = ElementTree.Element(flagtype)
                self.tree.insert(3, flagnode)
                for rulenode in rulenodes:
                    flagnode.append(rulenode)

        print ElementTree.tostring(self.tree)

