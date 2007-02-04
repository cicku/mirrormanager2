from mirrors.model import *
import socket
import re
import pickle
import bz2

redhat = None
core = None
fedora = None
rhel = None

Group(group_name='user', display_name='User')
Group(group_name='admin', display_name='Admin')
u = User(user_name='test', email_address='test@fedoraproject.org', display_name='Test', password='test')
u.addGroup(Group.by_group_name('user'))
a = User(user_name='admin', email_address='admin@fedoraproject.org', display_name='Admin', password='admin')
a.addGroup(Group.by_group_name('user'))
a.addGroup(Group.by_group_name('admin'))



def make_directories():
    testfiles = {'core':'../fedora-test-data/fedora-linux-core-dirsonly.txt', 'extras': '../fedora-test-data/fedora-linux-extras-dirsonly.txt'}
    for category, file in testfiles.iteritems():
        f = open(file, 'r')
        try:
            for line in f:
                line = line.strip()
                if re.compile('^\.$').match(line):
                    name = 'pub/fedora/linux/%s' % (category)
                    Directory(name=name)
                else:
                    name = 'pub/fedora/linux/%s/%s' % (category, line)
                    parent = None
                    index = name.rfind('/')
                    if index > 0:
                        parentname = name[:index]
                        parent = Directory.select(Directory.q.name==parentname)
                        if parent.count():
                            parent = parent[0]

                        child = Directory(name=name)
                    
        finally:
            f.close()

def trim_os_from_dirname(dirname):
    # trim the /os off the name
    index = dirname.rfind('/os')
    if index > 0:
        dirname = dirname[:index]
    return dirname

def rename_SRPMS_source(l):
    rc = []
    for i in l:
        if i == 'source':
            pass
        elif i == 'SRPMS':
            rc.append('source')
        else:
            rc.append(i)
    return rc

def guess_ver_arch_from_path(category, path):
    arch = None
    for a in Arch.select():
        if path.find(a.name) != -1:
            arch = a
    if path.find('SRPMS') != -1:
        arch = Arch.select(Arch.q.name=='source')

    ver = None
    for v in Version.select(Version.q.productID==category.product.id):
        s = '/%s' % (v.name)
        if path.find(s) != -1:
            ver = v

    return (ver, arch)

        


# lines look like
# -rw-r--r--         951 2007/01/10 14:17:39 updates/testing/6/SRPMS/repodata/repomd.xml
def make_repositories():
    testfiles = {'core':'../fedora-test-data/fedora-linux-core.txt', 'extras': '../fedora-test-data/fedora-linux-extras.txt'}
    for category, file in testfiles.iteritems():
        f = open(file, 'r')
        try:
            for line in f:
                line = line.strip()
                index = line.find('/repodata/repomd.xml')
                if index > 0:
                    path = line.split()[4]
                    index = path.find('/repodata/repomd.xml')
                    path = path[:index]
                    cat = Category.select(Category.q.name==category)[0]
                    (ver, arch) = guess_ver_arch_from_path(cat, path)
                    path = trim_os_from_dirname(path)
                    dirname = 'pub/fedora/linux/%s/%s'  % (category, path)
                    name=path.split('/')
                    name = rename_SRPMS_source(name)
                    name='-'.join(name)
                    name='%s-%s-%s' % (cat.product.name, category, name)
                    shortname = '%s-%s' % (category, ver)
                    dirs = Directory.select(Directory.q.name==dirname)
                    dir = None
                    if dirs.count() > 0:
                        dir = dirs[0]
                    Repository(name=name, category=cat, version=ver, arch=arch, directory=dir)

        finally:
            f.close()
    # assign shortnames to repositories like yum default mirrorlists expects
    
        


def make_sites():
    testfiles = {'core':'../fedora-test-data/mirror-hosts-core.txt', 'extras': '../fedora-test-data/mirror-hosts-extras.txt'}
    for category, file in testfiles.iteritems():
        # These are all fedora-core-6 mirrors, but they may not carry all arches or content.
        # That's ok, we'll figure out what they've got.
        # Turns out these all also carry fc5 too.
        f = open(file, 'r')
        try:
            for line in f:
                line = line.strip()
                s = line.split('/')
                index = line.find('://')
                protocol = line[:(index+3)]
                name = s[2]
                path = s[3:]
                    
                if Site.select(Site.q.name==name).count() == 0:
                    site = Site(name=name, password="password", private=False)
                else:
                    site = Site.select(Site.q.name==name)[0]

                if Host.select(Host.q.name==name).count() == 0:
                    host = Host(site=site, name=name)

        finally:
            f.close()



def make_versions():
    # create our default versions
    versions = []
    for ver in range(1,8):
        versions.append(str(ver))
    versions.append('development')
    for ver in versions:
        Version(name=ver, product=fedora)
    Version(name='6.90', product=fedora, isTest=True)

    for ver in ['4', '5']:
        Version(name=ver, product=rhel)

def make_embargoed_countries():
    for cc in ['cu', 'ir', 'kp', 'sd', 'sy' ]:
        EmbargoedCountry(country_code=cc)



#check if a configuration already exists. Create one if it doesn't
if not Arch.select().count():
    print "Creating Arches"
    Arch(name='source')
    Arch(name='i386')
    Arch(name='x86_64')
    Arch(name='ppc')
    Arch(name='sparc')
    Arch(name='ia64')


if not Site.select().count() and not Host.select().count():
    print "Creating Sites and Hosts"
    redhat = Site(name='Red Hat', password="password", orgUrl="http://www.redhat.com")
    Host(name='master', site=redhat)
    Host(name='download1.fedora.redhat.com', site=redhat)
    Host(name='download2.fedora.redhat.com', site=redhat)
    Host(name='download3.fedora.redhat.com', site=redhat)

    dell = Site(name='Dell', private=True, password="password", orgUrl="http://www.dell.com")
    Host(name='linuxlib.us.dell.com', site=dell)
    humbolt = Host(name='humbolt.us.dell.com', site=dell)
    f = open('../fedora-test-data/humbolt-pickle.bz2')
    pbz = f.read()
    f.close()
    humbolt.config = pickle.loads(bz2.decompress(pbz))
    
    



if not SiteAdmin.select().count():
    SiteAdmin(username='mdomsch', site=redhat)
    SiteAdmin(username='mdomsch', site=dell)

# create our default products
rhel = Product(name='rhel')
fedora = Product(name='fedora')


if not Version.select().count():
    make_versions()

if not Directory.select().count():
    make_directories()

if not EmbargoedCountry.select().count():
    make_embargoed_countries()

# create our default Repositories
core = Category(name='core',
                product = fedora,
                directory = Directory.select(Directory.q.name=='pub/fedora/linux/core')[0])

extras = Category(name='extras',
                  product = fedora,
                  directory = Directory.select(Directory.q.name=='pub/fedora/linux/extras')[0])


# release = Category(name='release',
#                    product = fedora,
#                    directory = Directory.select(Directory.q.name=='pub/fedora/linux/release')[0])

# epel = Category(name='epel',
#                 product = rhel,
#                 directory = Directory.select(Directory.q.name=='pub/epel/')[0])

                



if not Repository.select().count():
    make_repositories()

make_sites()
#make_mirrors()
