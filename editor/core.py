import functools, sys, os
import time
from multiprocessing.pool import ThreadPool

from flask import Blueprint, jsonify, request, current_app, render_template

from quantum import qasm as QASM

bp = Blueprint("core", __name__, url_prefix="/")

def jerror(err_code, message, code=400):
    return {
        "error":[err_code, message],
        "content": None
    }, code

def error(err_code, message, code=400):
    return jsonify(
        error=[err_code, message],
        content=None
    ), code

def jsuccess(body, code=200):
    return {
        "error": None,
        "content": body
    }, code

def success(body, message, code=400):
    return jsonify(
        error=None,
        content=body
    ), code

def final(data):
    return jsonify(data[0]), data[1]

@bp.route("/")
def index():
    return render_template("index.html")

@bp.route("/api/execute", methods=("POST",))
def execute():
    json = request.get_json()
    if json is None: return error("ERR_NO_BODY", "No json body present.")
    if not "instructions" in json: return error("ERR_NO_INSTRUCTIONS", "No instructions present")

    instructions = json["instructions"]
    shots = json["shots"] if "shots" in json else 1

    try:
        instructions = QASM.compile_qasm(instructions)
    except Exception as e:
        return error("ERR_CANNOT_COMPILE", str(e))

    def run():
        try:
            memory = None
            for i in range(shots):
                env = QASM.execute_qasm(instructions).toJSON()
                if memory is None: memory = env
                else: memory = [(memory[n] + env[n] if not memory[n] is None else None) for n in range(len(memory))]

            memory = [float(mem) / shots for mem in memory if not mem is None]
            return jsuccess(memory)
        except Exception as e:
            return jerror("ERR_CANNOT_EXECUTE", str(e))

    pool = ThreadPool(processes=1)
    thread = pool.apply_async(run)
    start = time.time()
    
    while len(pool._cache) != 0 and time.time() - start < 10: time.sleep(0.1)
    was_closed = len(pool._cache) != 0
    if was_closed: pool.close()

    return final(thread.get() if not was_closed else jerror("ERR_CANNOT_EXECUTE", "The process took more then 10 seconds to execute"))