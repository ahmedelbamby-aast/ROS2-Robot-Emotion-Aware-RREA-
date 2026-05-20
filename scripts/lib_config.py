#!/usr/bin/env python3
import json
import pathlib
import sys

try:
    import yaml
except Exception as exc:
    print(f"PyYAML is required: {exc}", file=sys.stderr)
    sys.exit(2)

ROOT = pathlib.Path(__file__).resolve().parents[1]
CFG = ROOT / "config" / "project.yaml"


def read_cfg():
    if not CFG.exists():
        raise FileNotFoundError(f"Config file not found: {CFG}")
    with open(CFG, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"Config root must be a mapping in {CFG}")
    return data


def write_cfg(cfg):
    with open(CFG, "w", encoding="utf-8") as f:
        try:
            yaml.safe_dump(cfg, f, sort_keys=False)
        except TypeError:
            yaml.safe_dump(cfg, f)


def parse_value(raw):
    lowered = raw.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "null":
        return None
    if raw.isdigit() or (raw.startswith("-") and raw[1:].isdigit()):
        return int(raw)
    return raw


def get_path(cfg, key):
    cur = cfg
    for part in key.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(key)
        cur = cur[part]
    return cur


def set_path(cfg, key, value):
    cur = cfg
    parts = key.split(".")
    for part in parts[:-1]:
        if not isinstance(cur, dict):
            raise KeyError(key)
        if part not in cur:
            cur[part] = {}
        if not isinstance(cur[part], dict):
            raise KeyError(key)
        cur = cur[part]
    if not isinstance(cur, dict):
        raise KeyError(key)
    cur[parts[-1]] = value


def main():
    if len(sys.argv) < 2:
        print("usage: lib_config.py get|set key [value]", file=sys.stderr)
        return 1
    action = sys.argv[1]
    try:
        cfg = read_cfg()
        if action == "get":
            if len(sys.argv) != 3:
                print("usage: lib_config.py get key", file=sys.stderr)
                return 1
            key = sys.argv[2]
            cur = get_path(cfg, key)
            if isinstance(cur, (dict, list)):
                print(json.dumps(cur))
            else:
                print(cur)
            return 0
        if action == "set":
            if len(sys.argv) != 4:
                print("usage: lib_config.py set key value", file=sys.stderr)
                return 1
            key, value = sys.argv[2], parse_value(sys.argv[3])
            set_path(cfg, key, value)
            write_cfg(cfg)
            return 0
        print("usage: lib_config.py get|set key [value]", file=sys.stderr)
        return 1
    except KeyError as exc:
        print(f"Config key not found: {exc.args[0]}", file=sys.stderr)
        return 1
    except (FileNotFoundError, ValueError, yaml.YAMLError) as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
