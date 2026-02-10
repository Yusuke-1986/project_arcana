# arcana.py　ver.0.3
# Arcana minimal runner
import argparse

from .lexer import *
from .ast import *
from .transpiler import *
# import sys

from datetime import datetime
from .pipeline import compile_source

VERSION = "0.3.5"

# --- tracing ---
TRACE = False

def tr(msg: str) -> None:
    if TRACE:
        print(f"[arcana: trace]> {msg}")

# ========================
# Runner
# ========================

def run_file(path: str, emit: bool=False, no_run: bool=False) -> None:
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()

    try:
        # src = strip_line_comments(src)
        art = compile_source(src)

        program = art.program
        tr(f"PARSE: {program}")
        warnings = art.warnings
        tr(f"SEMANTIC ANALYSIS COMPLETE: Warnings={ warnings }")
        # sys.exit()
        py = transpile(program)
        
        if emit:
            print("=== [arcana perscribere] transpiled python ===")
            print(py)
            print("=== [arcana perscribere] end ===")
        if no_run:
            return
        
        # Minimal execution environment
        print("=== [arcana: oraculum] ===")
        env = {"__name__": "__main__"}
        exec(compile(py, "<arcana>", "exec"), env, env)

    except Exception as e:
        if PYTRACE:
            import traceback
            print("[arcana] contraindication:", e)
            traceback.print_exc()
        else:
            print("[arcana] contraindication:", e)

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="arcana")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("exsecutio", help="run .arkhe source")
    p_run.add_argument("file", help="e.g. main.arkhe")
    p_run.add_argument("--perscribere", action="store_true", help="print transpiled python code")
    p_run.add_argument("--non-run", action="store_true", help="emit only, do not execute")
    p_run.add_argument("--vestigium", action="store_true", help="print parser/transpiler trace")
    p_run.add_argument("--pytrace", action="store_false", help="do not print python traceback")

    args = ap.parse_args()

    print(f"arcana: python transpiler ver v.{VERSION}")
    print("")
    
    if args.cmd == "exsecutio": # exsecutioあれば実行
        start = datetime.now()
        global TRACE
        TRACE = args.vestigium
        global PYTRACE
        PYTRACE = args.pytrace
        run_file(args.file, emit=args.perscribere, no_run=args.non_run)
        end = datetime.now()
        delta = end - start

        tr(f"[arcana] exsecutio completed in {delta.total_seconds()} seconds.")

        return 0
