#!/usr/bin/env python

import os
import sys
import argparse

import wandb

from functools import reduce

from wandb.proto import wandb_telemetry_pb2 as telemetry

from typing import NewType, Optional, Dict, Any, Tuple, Generator


# dont strip internal
wandb.apis.public.WANDB_INTERNAL_KEYS = {}


def space(pb):
    for d in pb.DESCRIPTOR.fields:
        if d.type == d.TYPE_STRING:
            setattr(pb, d.name, "")
        elif d.type == d.TYPE_BOOL:
            setattr(pb, d.name, True)
        elif d.type == d.TYPE_MESSAGE:
            msg = getattr(pb, d.name)
            space(msg)


def parse(pb, obj):
    if not obj:
        return
    for d in pb.DESCRIPTOR.fields:
        val = obj.get(str(d.number))
        if d.type == d.TYPE_STRING:
            if not val or type(val) is not str:
                continue
            setattr(pb, d.name, val)
        elif d.type == d.TYPE_BOOL:
            if not val or type(val) is not bool:
                continue
            setattr(pb, d.name, val)
        elif d.type == d.TYPE_MESSAGE:
            if not val or type(val) is not list:
                continue
            msg = getattr(pb, d.name)
            data = dict()
            for k in val:
                data[str(k)] = True
            parse(msg, data)


def expand(pb):
    data = dict()
    for d, val in pb.ListFields():
        if d.name.startswith("imports"):
            continue
        if d.type == d.TYPE_MESSAGE:
            for d2, v2 in val.ListFields():
                data[".".join((d.name, d2.name))] = v2
    return data


# taken from wandb
def _framework_priority(imp) -> Generator[Tuple[bool, str], None, None]:
    yield imp.lightgbm, "lightgbm"
    yield imp.catboost, "catboost"
    yield imp.xgboost, "xgboost"
    yield imp.transformers, "huggingface"
    yield imp.pytorch_ignite, "ignite"
    yield imp.pytorch_lightning, "lightning"
    yield imp.fastai, "fastai"
    yield imp.torch, "torch"
    yield imp.keras, "keras"
    yield imp.tensorflow, "tensorflow"
    yield imp.sklearn, "sklearn"


# taken from wandb
def _telemetry_get_framework(pb) -> str:
    """Get telemetry data for internal config structure."""
    # detect framework by checking what is loaded
    if pb.HasField("imports_finish"):
        imp = pb.imports_finish
    elif pb.HasField("imports_init"):
        imp = pb.imports_init
    else:
        return ""
    priority = _framework_priority(imp)
    framework = next((f for b, f in priority if b), "")
    return framework
        
    
def scan(x, r, fname):
    run_ids = open(fname).readlines()
    run_ids = [f.strip().split() for f in run_ids]
    api = wandb.Api()
    for spec, run_id in run_ids:
        x["num"] += 1
        try:
            run = api.run(run_id)
        except wandb.errors.error.CommError:
            run = None
        if not run:
            print("# %d: run" % x["num"], spec, run_id)
            continue
        # print("run", spec, run_id)
        w = run.config.get("_wandb")
        t = w.get("t") if w else None
        pb = telemetry.TelemetryRecord()
        parse(pb, t)
        data = expand(pb)
        fw = _telemetry_get_framework(pb)
        if fw:
            data["framework.%s" % fw] = True
        used = list(data)
        print("%d: run" % x["num"], spec, run_id, run.state, fw)
        for i in used:
            r.setdefault(i, []).append(run_id)


def get_all():
    f = telemetry.TelemetryRecord()
    space(f)
    a = expand(f)
    for _, fw in _framework_priority(f.imports_init):
        a["framework.%s" % fw] = True
    a = list(a)
    return a


def summarize(extra):
    t = dict(num=0)
    r = dict()

    a = get_all()
    ln = reduce(max, map(len, a))

    fnames = extra
    for fname in fnames:
        scan(t, r, fname)

    for i in a:
        print("%*s: %d" % (ln, i, len(r.get(i, []))))


def grabone(fname, spec, run_id):
    api = wandb.Api()
    try:
        run = api.run(run_id)
    except wandb.errors.error.CommError:
        run = None
    if not run:
        return

    dirname = os.path.dirname(fname)
    base = os.path.join(dirname, "data")
    filesdir = os.path.join(base, spec, "files")
    try:
        os.makedirs(filesdir)
    except FileExistsError:
        pass
    files = run.files()
    for f in files:
        f.download(root=filesdir)


def grabstuff(fname):
    run_ids = open(fname).readlines()
    run_ids = [f.strip().split() for f in run_ids]
    for spec, run in run_ids:
        print("->", spec, run)
        grabone(fname, spec, run)


def grab(extra):
    fnames = extra
    for fname in fnames:
        grabstuff(fname)

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--project", type=str, default=None, help="project")
    parser.add_argument("--summarize", default=False, dest="summarize", help="scan stuff", action="store_true")
    parser.add_argument("--grab", default=False, dest="grab", help="grab stuff", action="store_true")
    args, extra = parser.parse_known_args()
    if args.summarize:
        summarize(extra)
    if args.grab:
        grab(extra)



if __name__ == "__main__":
    main()
