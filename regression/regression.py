#!/usr/bin/env python
# ./regression.py --dryrun --spec ::~py36,~pt0.4.1 main/
# ./regression.py --dryrun --spec ::py27           main/
# ./regression.py --dryrun --spec ::py27,~pt0.3.1  main/
# ./regression.py --dryrun --spec ::pythons=py27   main/
# ./regression.py --cli_branch feature/data-frame-media --spec ::~broken .
from __future__ import print_function

# TODO(jhr): deal with matplotlib config .config/matplotlib
# by allowing a directory to be specified for config
# XDG_CONFIG_HOME=$PWD/xtra/ wandb magic conv_lstm.py

import os
import yaml
import datetime
import random
import string
import subprocess
import argparse
import sys
import re
import six
import itertools
import shutil
import codecs
import glob
import time

import wandb

def gettimestr():
    now = datetime.datetime.now()
    return now.strftime("%Y%m%d_%H%M%S")

BASE="~/work/regression"
CONF="regression-config.yaml"
REG="regression.yaml"
WHEN=gettimestr()
RUNFILE=os.path.join(os.path.abspath("."), "results", WHEN, "runs.txt")

#p = subprocess.Popen(sys.argv, stdin=0, stdout=1, stderr=2)
#ret = p.wait()

import shortuuid

def generate_id():
    # ~3t run ids (36**8)
    run_gen = shortuuid.ShortUUID(alphabet=list("0123456789abcdefghijklmnopqrstuvwxyz"))
    return run_gen.random(8)

def getdatestr():
    now = datetime.datetime.now()
    return now.strftime("%Y%m%d")

def reg_subprocess_retry(cmdlist):
    exception = None
    for x in range(10):
        try:
            o = subprocess.check_output(cmdlist)
            return o
        except subprocess.CalledProcessError as e:
            exception = e
        time.sleep(10 + x * 30)
    if exception:
        raise exception
        

def getid():
    num = 6
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(num))

def gettestid(branch, cliver, clihash):
    # workaround for #1682
    branch = branch.replace("/", "_")
    return '%s-%s-%s-%s-%s' % (getdatestr(), cliver, branch, clihash[:7], getid())


def macro_replace(s):
    start = s.find("${")
    if start < 0:
        return s
    end = s.find("}", start)
    if end < 0:
        return s
    macro = s[start+2:end]
    val = os.environ[macro]
    s = s[:start] + val + s[end+1:]
    # recursively replace macros
    s = macro_replace(s)
    return s


def checkout_git_one(gitfirst):

    giturl = gitfirst.get("url")
    base = gitfirst.get("base")
    githash = gitfirst.get("hash")
    branch = gitfirst.get("branch") or "master"
    # print('got', giturl, base)
    if not os.path.isdir(base):
        tmpdir = "tempgit.%s" % getid()
        if os.path.isdir(tmpdir):
            os.remove(tmpdir)
        subprocess.check_output(["git", "clone", "-b", branch, giturl, tmpdir])
        if githash:
            os.chdir(tmpdir)
            subprocess.check_output(["git", "checkout", githash])
            os.chdir("..")
        os.rename(tmpdir, base)


def checkout_git(gitlist):
    for git_item in gitlist:
        git_one = list(git_item.values()).pop()
        print("Git checkout:", git_one)
        checkout_git_one(git_one)


class Test(object):
    def __init__(self):
        self.options = []
        self.run_group = None
        self.job_type = None
        self.tags = []

    def setglob(self, testid, dirname, args, branch, cliver, clihash):
        self.testid = testid
        self.dirname = dirname
        self.args = args
        self.branch = branch
        self.cliver = cliver
        self.clihash = clihash

    def setup(self, conf, v, params, vals):
        self.conf = conf
        self.variant = v
        self.params = params
        self.vals = vals

    def env(self):
        base = os.path.expanduser(BASE)
        instance = self.conf.get("name", "unknown")
        vname = list(self.variant.keys()).pop()
        gname = '-'.join(self.vals)
        reg_gname = ','.join(self.vals)
        fullname = '%s_%s_%s_%s' % (self.testid, instance, vname, gname)
        self.run_group = self.testid
        self.job_type = instance
        self.reg_name = vname
        self.name = vname
        if gname:
            self.name += "_" + gname
            self.reg_name += ":" + reg_gname
        pathname = "%s/%s" % (base, fullname)
        self.pathname = pathname
        if not os.path.isdir(pathname):
            os.makedirs(pathname)

    def parse(self):
        self.components = []
        pdict = dict(zip(self.params, self.vals))
        cdict = self.conf.get("components", {})
        l = list(self.variant.values()).pop()
        for c in l:
            # look for component in conf (TODO(jhr): later in base conf - recursively)
            if c in pdict:
                c = pdict[c]
            f = cdict.get(c)
            if not f:
                print("ERROR: can not find: %s" % c)
                sys.exit(1)
            self.components.append((c, f))

    def prepare0(self):
        #print("pdict", pdict)
        #groups = self.conf.get("groups", {})
        for c, f in self.components:
            # need to walk
            patches = f.get("patches", {})
            pip = f.get("pip", [])
            tags = f.get("tags", [])
            self.tags += tags
            options = f.get("options", [])
            #print("PPP", patches, pip)
            for p in pip:
                if self.args.nogpu:
                    # strip off -gpu\b or _gpu\b
                    mgpu1 = re.compile(r'(.*)-gpu\b(.*)')
                    mgpu2 = re.compile(r'(.*)_gpu\b(.*)')
                    m = mgpu1.match(p)
                    if not m:
                        m = mgpu2.match(p)
                    if m:
                        p = ''.join(m.groups())
                action = 'installing'
                # TODO only check first element
                if '==' in p:
                    action = 'upgrading'
                print("INFO: %s pip %s" % (action, p))
                p = p.split(' ')
                if action == 'upgrading':
                    print("DEBUG:", ['pyenv', 'exec', 'pip', 'install', '--upgrade'] + p)
                    reg_subprocess_retry(['pyenv', 'exec', 'pip', 'install', '--upgrade'] + p)
                else:
                    #print("DEBUG2:", ['pyenv', 'exec', 'pip', 'install'] + p)
                    reg_subprocess_retry(['pyenv', 'exec', 'pip', 'install'] + p)
            for k, v in patches.items():
                for p in v:
                    print("INFO: applying patch %s" % p)
                    #subprocess.check_output(['patch', '-p1', p])
                    fs = self.sources.get(k)
                    basename = fs.get("base")
                    pathname = os.path.join(self.pathname, basename)
                    print("INFO: dir: %s" % pathname)
                    os.chdir(pathname)
                    fp = os.path.join(self.dirname, p)
                    print("INFO: reading from: %s" % fp)
                    FIN = open(fp, 'r')
                    p = subprocess.Popen(['patch', '-p1'], stdin=FIN, stdout=1, stderr=2)
                    ret = p.wait()
                    if ret != 0:
                        sys.exit(1)
                    #print("INFO: patch:", ret)
            for p in options:
                self.options.append(p)
            
    def prepare(self):
        #print("Chdir", self.pathname)
        os.chdir(self.pathname)
        gitlist = self.conf.get("sources", [])
        sources = {}
        for g in gitlist:
            sources.update(g)
        self.sources = sources

        # if not gitlist, run locally
        if gitlist:
            checkout_git(gitlist)

    def cleanup(self):
        #vs = ["PYENV_VERSION", "PYENV_VIRTUALENV_INIT", "PYENV_VIRTUAL_ENV", "PYENV_SHELL", "VIRTUAL_ENV", "PYENV_ROOT", "PYENV_HOOK_PATH"]
        vs = []
        #vs = os.environ.keys()
        for v in vs:
            os.environ.pop(v, None)
            if v in os.environ:
                del os.environ[v]
        #o = subprocess.check_output(["env"])
        #print("ENV:", o)
        pyver = None
        for c, f in self.components:
            v = f.get("python")
            if v:
                if pyver:
                    print("ERROR: python already set")
                    sys.exit(1)
                pyver = v
        if not pyver:
            pyver = "3.6.8"
        pyenv = "v" + pyver.replace('.', '')
        subprocess.check_output(["pyenv", "install", "-s", pyver])
        subprocess.check_output(["pyenv", "uninstall", "-f", pyver + "/envs/" + pyenv])
        subprocess.check_output(["pyenv", "virtualenv", pyver, pyenv])
        # PYENV_VERSION=v36 pyenv exec pip list
        env = self.conf.get("environment", {})
        pl = env.get("pip")
        pl = pl if pl else []
        os.environ["PYENV_VERSION"] = pyenv
        for p in pl:
            action = 'installing'
            if '==' in p:
                action = 'upgrading'
            print("%s: %s" % (action.capitalize(), p))
            if action == 'upgrading':
                reg_subprocess_retry(['pyenv', 'exec', 'pip', 'install', '--upgrade', p])
            else:
                reg_subprocess_retry(['pyenv', 'exec', 'pip', 'install', p])
        #o = subprocess.check_output(["pyenv", "exec", "pip", "list", "--format=columns"])
        #print("LIST:", o)
        #old = ['tf-nightly-2.0-preview', 'tf-nightly-gpu-2.0-preview', 'tf-nightly', 'tf-nightly-gpu', 'tensorflow', 'tensorflow_gpu']
        #for p in old:
        #    cmd = ['pip', 'uninstall', '-y', p]
        #    subprocess.check_output(cmd)
        vs = env.get("variables")
        vs = vs if vs else {}
        for k, v in six.iteritems(vs):
            os.environ[k] = str(v)

    def prepare2(self):
        pl = self.conf.get("prepare", [])
        for pi in pl:
            l = list(pi.values()).pop()
            #print("GOT", l)
            os.chdir(self.pathname)
            p = l.get("path")
            #print("Chdir", p)
            os.chdir(p)
            cmd = l.get("command")
            cmd = ["pyenv", "exec"] + cmd
            print("DIR:", p)
            print("INFO: Running", ' '.join(cmd))
            subprocess.check_output(cmd)


    def env_save(self):
        self._env_capture = dict(os.environ.copy())

    def env_restore(self):
        # undo environment
        for evk, evv in six.iteritems(self._env_capture):
            os.environ[evk] = evv
        for evk in list(os.environ.keys()):
            if evk not in self._env_capture:
                del os.environ[evk]

    def check(self):
        c = self.conf.get("check")
        if not c:
            return
        if os.environ.get("WANDB_MODE") == "disabled":
            return
        cwd = os.getcwd()
        os.chdir(self.dirname)
        l = c.get("command")
        p = subprocess.Popen(l, stdin=0, stdout=1, stderr=2)
        ret = p.wait()
        if ret != 0:
            print("INFO: exit code: %d" % ret)
            record_failed('%s:%s' % (self.job_type, self.reg_name))
            self.failed = True
        os.chdir(cwd)

    def launch(self):
        run_id = "norunid"
        l = self.conf.get("launch").get("command")
        # if naked run
        description = "%s\nRelease = %s\nBranch = %s\nHash = %s\n\nBatch = %s\nTest = %s\n" % (self.name, self.cliver, self.branch, self.clihash, self.run_group, self.job_type)
        name = self.name
        notes = "Release = %s\nBranch = %s\nHash = %s\n\nBatch = %s\nTest = %s\n" % (self.cliver, self.branch, self.clihash, self.run_group, self.job_type)
        tags = ",".join(self.tags)
        if 'wandb-run' in self.options:
            r = ['wandb', 'run']
            r += ['--message', description]
            if self.run_group:
                r += ['--run_group', self.run_group]
            if self.job_type:
                r += ['--job_type', self.job_type]
            if self.tags:
                r += ['--tags', tags]
            r = r  + l
            l = r
        elif 'wandb-magic' in self.options:
            if self.run_group:
                os.environ["WANDB_RUN_GROUP"] = self.run_group
            if self.job_type:
                os.environ["WANDB_JOB_TYPE"] = self.job_type
            os.environ["WANDB_TAGS"] = tags
            r = ['wandb', 'magic']
            r = r  + l
            l = r
        else:
            if self.run_group:
                os.environ["WANDB_RUN_GROUP"] = self.run_group
            if self.job_type:
                os.environ["WANDB_JOB_TYPE"] = self.job_type
            os.environ["WANDB_TAGS"] = tags
        if 'python-path' in self.options:
            os.environ["PYTHONPATH"] = "."

        os.chdir(self.pathname)

        pth = self.conf.get("launch").get("path")
        timeout = self.conf.get("launch", {}).get("timeout")
        killtime = self.conf.get("launch", {}).get("killtime")
        norunid = self.conf.get("launch", {}).get("norunid")
        os.chdir(pth or self.dirname)

        preps = self.conf.get("launch").get("prep", [])
        for prep in preps:
            print("Running:", prep)
            p = subprocess.Popen(prep, stdin=0, stdout=1, stderr=2)
            ret = p.wait()
            self.failed = False
            if ret != 0:
                print("INFO: exit code: %d" % ret)
                record_alltests('%s:%s' % (self.job_type, self.reg_name), args=self.args)
                record_failed('%s:%s' % (self.job_type, self.reg_name))
                self.failed = True
                return

        patches = self.conf.get("launch").get("patches", [])
        for patch in patches:
            print("Patching:", patch)
            # go to right dir
            p = patch
            if True:
                    # FIXME: copied from elsewhere
                    print("INFO: applying patch %s" % p)
                    #subprocess.check_output(['patch', '-p1', p])
                    #basename = fs.get("base")
                    #pathname = os.path.join(self.pathname, basename)
                    #print("INFO: dir: %s" % pathname)
                    #os.chdir(pathname)
                    fp = os.path.join(self.dirname, p)
                    print("INFO: reading from: %s" % fp)
                    FIN = open(fp, 'r')
                    # FIXME:HACK to do -p2, sould use sources, probably should specify sources
                    p = subprocess.Popen(['patch', '-p2'], stdin=FIN, stdout=1, stderr=2)
                    ret = p.wait()
                    if ret != 0:
                        sys.exit(1)
                    #print("INFO: patch:", ret)
        #sys.exit(1)
        # go back to where we want to be
        #os.chdir(self.pathname)
        #os.chdir(pth)

        l_list = []
        if l and isinstance(l[0], dict):
            for num, command_dict in enumerate(l):
                lsetting = {}
                # HACK: ignore return code if we are a list and not last
                if num != len(l) - 1:
                    lsetting["ignore"] = True
                for _, v in command_dict.items():
                    l_list.append((lsetting, v))
        else:
            lsetting = {}
            l_list.append((lsetting, l))

        generated_id = generate_id()
        for l_settings, l in l_list:
            r = [os.path.expanduser(str(i)) for i in l]
            print("INFO: Cool Running", ' '.join(r))
            project = "regression"
            if self.args.project:
                project = self.args.project
            # timeout -k 90s -s TERM 5s sleep 20
            #print("RUN:", r)
            #sys.exit(1)
            os.environ["WANDB_PROJECT"] = project
            # os.environ["WANDB_DESCRIPTION"] = description
            os.environ["WANDB_NAME"] = name
            os.environ["WANDB_NOTES"] = notes
            if not norunid:
                run_id = "r-" + generated_id
                os.environ["WANDB_RUN_ID"] = run_id
            #subprocess.check_output(r)

            # expand macros if needed
            r = [macro_replace(ri) for ri in r]

            # wrap run with pyenv and timeout if needed
            r = ["pyenv", "exec"] + r
            if timeout and killtime:
                r = ["timeout", "-k", killtime, "-s", "TERM", timeout] + r

            p = subprocess.Popen(r, stdin=0, stdout=1, stderr=2)
            ret = p.wait()
            self.failed = False
            if l_settings.get("ignore"):
                continue
            run_path = "%s/%s" % (project, run_id)
            record_alltests('%s:%s' % (self.job_type, self.reg_name), run=run_path, args=self.args)
            if ret != 0:
                print("INFO: exit code: %d" % ret)
                record_failed('%s:%s' % (self.job_type, self.reg_name))
                self.failed = True


# parse and find groups in variants
def gengroups(conf, vname, gspec):
    groups = conf.get("groups", {})
    #print("gs", groups)

    variants = conf.get("variants", [])
    vdict = {}
    for variant in variants:
        vdict.update(variant)

    clist = vdict[vname]

    # gspec: str=val,str=val
    gsfilter = []
    gspecdict = {}
    if gspec:
        gspeclist = gspec.split(",")
        for gsval in gspeclist:
            if '=' in gsval:
                k,v = gsval.split("=")
                gspecdict[k] = v
            else:
                gsfilter.append(gsval)
    params = []
    vals = []
    for c in clist:
        gs = groups.get(c)
        if gs:
            s = gspecdict.get(c)
            if s:
                if s in gs:
                    gs = [s]
                else:
                    continue
            params.append(c)
            vals.append(gs)
    s = list(itertools.product(*vals))
    # check filters
    return params, s, gsfilter
            
        

def hack_get_glob(conf, commandglob):
    start_path = os.path.abspath(os.getcwd())
    #print("HACK", conf, commandglob, start_path)
    # FIXME: this is taken from def prepare()
    tmpname = ".tmp.repo"
    if not os.path.isdir(tmpname):
        os.makedirs(tmpname)
    if True:
        os.chdir(tmpname)
        gitlist = conf.get("sources", [])
        sources = {}
        for g in gitlist:
            sources.update(g)
        # FIXME, process list not just first
        gitfirst = list(gitlist[0].values()).pop()
        giturl = gitfirst.get("url")
        base = gitfirst.get("base")
        #print('got', giturl, base)
        if not os.path.isdir(base):
            tmpdir = "tempgit.%s" % getid()
            if os.path.isdir(tmpdir):
                os.remove(tmpdir)
            subprocess.check_output(["git", "clone", giturl, tmpdir])
            os.rename(tmpdir, base)
    os.chdir(start_path)
    os.chdir(tmpname)
    os.chdir(conf.get("launch").get("path"))
    gg = commandglob.get("glob")
    excl = commandglob.get("exclude", [])
    gfiles = glob.glob(gg)
    #print("gfiles", gfiles)
    commands = []
    gfiles.sort()
    for c in gfiles:
        if c in excl:
            continue
        cname = c.rstrip(".py")
        commands.append({cname: {'command': [c]}})
    os.chdir(start_path)
    return commands


def process_external(ext_list, args, branch, cliver, clihash):
    # print("DEBUG", ext_list)
    base = os.path.expanduser(BASE)
    fullname = "external_" + gettimestr()
    pathname = "%s/%s" % (base, fullname)
    if not os.path.isdir(pathname):
        os.makedirs(pathname)

    start_path = os.path.abspath(os.getcwd())
    os.chdir(pathname)
    checkout_git(ext_list)
    scan_and_run(args, branch, cliver, clihash, tests=["."])

    os.chdir(start_path)


def process(fname, testid, args, branch, cliver, clihash, clibase, clirepo):
    # load base
    f = open(args.config).read()
    base = yaml.load(f, Loader=yaml.SafeLoader)
    
    f = open(fname).read()
    conf = yaml.load(f, Loader=yaml.SafeLoader)

    #print("BASE", base)
    #print("CONF", conf)
    #print("FINL", finl)
    for c in ("launch", "components", "groups"):
        for k, v in six.iteritems(base.get(c, {})):
            conf.setdefault(c, {}).setdefault(k, v)

    # if regression points to an external spec
    ext_list = conf.get("external", [])
    if ext_list:
        process_external(ext_list, args, branch, cliver, clihash)
        return

    # git+git://github.com/wandb/client.git@797db669bec29094fd2676ba8e35f7840bedf487#egg=wandb
    if args.cli_release:
        conf["components"]["wandb-cli"] = {"pip": ["%s==%s" % (clibase, cliver)]}
        conf["components"]["wandb-grpc"] = {"pip": ["%s[grpc]==%s" % (clibase, cliver)]}
    else:
        conf["components"]["wandb-cli"] = {"pip": ["git+git://github.com/%s@%s#egg=%s" % (clirepo, clihash, clibase)]}
        conf["components"]["wandb-grpc"] = {"pip": ["git+git://github.com/%s@%s#egg=%s[grpc]" % (clirepo, clihash, clibase)]}

    dirname = os.path.dirname(os.path.abspath(fname))
    #print("dirname", dirname)
    #print("running", conf)
    orig_name = conf.get("name")
    variants = conf.get("variants", [])
    speclen = 3
    spec = []
    if args.spec:
        spec = args.spec.split(':')
    spec.extend([None]*(speclen-len(spec)))
    tspec, vspec, gspec = spec

    # TODO(jhr): if launch has commands, iterate through each one here
    commands = conf.get("launch").get("commands", [])
    command = conf.get("launch").get("command")
    if command:
        commands.append({'': {'command': command}})
    commandglob = conf.get("launch").get("commandglob")
    if commandglob:
        #gg = commandglob.get("glob")
        #os.chdir(self.pathname)
        #p = self.conf.get("launch").get("path")
        # FIXME(jhr): this is a hack because we havent pulled the repo yet
        commands += hack_get_glob(conf, commandglob)
        #ggfiles = glob.glob(gg)
        #print("glob: ", commandglob, ggfiles, dirname)

    for command in commands:
        cname = None
        cdict = {}
        if command:
            # populate into regular conf
            #print("got command", command)
            cname, cdict = command.popitem()
            conf["launch"]["command"] = cdict["command"]
            if cname:
                conf["name"] = orig_name + "_" + cname
            else:
                conf["name"] = orig_name
        for variant in variants:
            vname = list(variant.keys()).pop()
            if vspec:
                if vspec.startswith("~"):
                    if vspec[1:] == vname:
                        continue
                elif vspec != vname:
                    continue
            params, vals, gsfilter = gengroups(conf, vname, gspec)
            for g in vals:
                skip_items = cdict.get("skip", [])
                if any(skip in g for skip in skip_items):
                    continue
                gname = '-'.join(g)
                #d = dict(zip(params, g))
                vname = list(variant.keys()).pop()
                name = conf.get("name")
                #if tspec and tspec != name:
                #    continue
                # allow partial match
                if tspec and not name.startswith(tspec):
                    continue
                #if args.dryrun:
                #    continue
                #continue
                t = Test()
                t.setglob(testid, dirname, args, branch, cliver, clihash)
                t.setup(conf, variant, params, g)
                t.env()
                t.parse()
                components = [k for k, v in t.components]
                gspos = [c for c in gsfilter if not c.startswith("~")]
                gsneg = [c[1:] for c in gsfilter if c.startswith("~")]
                found = True
                for c in gspos:
                    if c not in components:
                        found = False
                if not found:
                    continue
                found = False
                for c in gsneg:
                    if c in components:
                        found = True
                if found:
                    continue
                print("#" * 40)
                print("#", name, vname, gname)
                print("#" * 40)
                if args.dryrun:
                    continue

                t.env_save()
                t.cleanup()
                t.prepare()
                t.prepare0()
                t.prepare2()
                t.launch()
                t.failed = False
                if not t.failed:
                    t.check()
                t.env_restore()

                print("\n\n")


def get_branch_info(branch, repo):
    #subprocess.check_output(["git", "clone", "--single-branch", "--branch", branch, "-n", "git@github.com:wandb/client.git", "tmp-cli"])
    subprocess.check_output(["git", "clone", "--single-branch", "--branch", branch, "git@github.com:" + repo, "tmp-cli"])
    os.chdir("tmp-cli")
    o = subprocess.check_output(["git", "rev-parse", branch])
    o = o.strip()
    version_str = "current_version = "
    o2 = subprocess.check_output(["egrep", "^" + version_str, "setup.cfg"])
    o2 = o2[len(version_str):]
    o2 = o2.strip()
    os.chdir("..")
    shutil.rmtree("tmp-cli")
    o2 = codecs.decode(o2, encoding='utf-8', errors='strict')
    o = codecs.decode(o, encoding='utf-8', errors='strict')
    return o2, o
    
    
failed = []
alltests = []

def record_failed(s):
    global failed
    failed.append(s)

def record_alltests(s, run=None, args=None):
    global alltests
    alltests.append(s)
    if not run:
        return

    try:
        os.makedirs(os.path.dirname(RUNFILE))
    except OSError:
        pass

    with open(RUNFILE, "a") as f:
        print("%s %s" % (s, run), file=f)

def summary_print():
    print("\n------------------\n")
    f = []

    num = 0
    print("Good runs:")
    for r in alltests:
        if r in failed:
            if r not in f:
                f.append(r)
            continue
        print("  %3d: %s" % (num, r))
        num += 1

    print("Failed runs:")
    for num, r in enumerate(f):
        print("  %3d: %s" % (num, r))

    if f:
        sys.exit(1)


def scan_and_run(args, branch, cliver, clihash, tests=None):
    if args.testid:
        testid = args.testid
    else:
        testid = gettestid(branch, cliver, clihash)

    #wandb.init()
    tests = tests or args.tests
    start_path = os.path.abspath(os.getcwd())
    for fname in tests:
        if os.path.isdir(fname):
            for root, dirs, files in os.walk(fname):
                reg_names = [args.name]
                if args.name == REG:
                    reg_names.append("." + REG)
                for reg_name in reg_names:
                    if reg_name not in files:
                        continue
                    # print("INFO: Run", root, reg_name)
                    process(os.path.join(root, reg_name), testid, args, branch, cliver, clihash, args.cli_base, args.cli_repo)
                    os.chdir(start_path)
        else:
            process(fname, testid, args, branch, cliver, clihash, args.cli_base, args.cli_repo)
        os.chdir(start_path)


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--project", type=str, default=None, help="project")
    parser.add_argument("--config", type=str, default=None, help="config file")
    parser.add_argument("--testid", type=str, default=None, help="test id")
    parser.add_argument("--spec", type=str, default=None, help="spec")
    parser.add_argument("--name", type=str, default=None, help="test name")
    parser.add_argument("--nogpu", default=False, dest="nogpu", help="disable gpu pip packages", action="store_true")
    parser.add_argument("--dryrun", default=False, dest="dryrun", help="dont run stuff", action="store_true")
    parser.add_argument("--cli_release", type=str, default=None, help="release name")
    parser.add_argument("--cli_branch", type=str, default=None, help="cli branch")
    parser.add_argument("--cli_hash", type=str, default=None, help="cli hash")
    parser.add_argument("--cli_base", type=str, default="wandb", help="cli base")
    parser.add_argument("--cli_repo", type=str, default="wandb/client.git", help="cli base")
    parser.add_argument('tests', metavar='TEST', type=str, nargs='+',
                    help='tests file or directory')
    args = parser.parse_args()

    # setup defaults
    if not args.config:
        dirname = os.path.abspath(os.path.dirname(sys.argv[0]))
        conf_pathname = os.path.join(dirname, CONF)
        args.config = conf_pathname
    if not args.name:
        args.name = REG

    cliver = "unknown"
    branch = "unknown"
    clihash = "unknown"

    if args.cli_branch:
        if args.cli_release or args.cli_hash:
            print("ERROR: can not specify branch with release or hash")
            sys.exit(1)
        branch = args.cli_branch
        cliver, clihash = get_branch_info(args.cli_branch, args.cli_repo)
    elif args.cli_release:
        if args.cli_hash:
            print("ERROR: can not specify release with hash")
            sys.exit(1)
        cliver = args.cli_release
        branch = "release"
        # branch and hash are unknown (these could be known)
    elif args.cli_hash:
        clihash = args.cli_hash
        # branch and release are unknown (these could be known)
    else:
        branch = "master"
        cliver, clihash = get_branch_info(branch, args.cli_repo)

    print("INFO: cli hash = ", clihash)

    scan_and_run(args, branch, cliver, clihash)

    summary_print()


if __name__ == "__main__":
    main()
