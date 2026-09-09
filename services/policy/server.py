"""Transport/FFI only: authorization rules and cohort assignment live in C."""
import ctypes
import hmac
import os
import sys
from pathlib import Path
from concurrent import futures
import grpc
sys.path.insert(0, str(Path(__file__).parent))
import policy_pb2 as pb
import policy_pb2_grpc as rpc
from services.telemetry import configure
from opentelemetry.instrumentation.grpc import GrpcInstrumentorServer

ROOT = Path(__file__).resolve().parents[2]
class Request(ctypes.Structure):
    _fields_ = [(name, ctypes.c_int) for name in (
        "actor_role", "is_self", "target_role", "target_active", "active_admins", "action", "requested_role")]
class Decision(ctypes.Structure):
    _fields_ = [("allowed", ctypes.c_int), ("risk", ctypes.c_int), ("reason", ctypes.c_char * 160)]
lib = ctypes.CDLL(str(ROOT / "build/libatlas.so"))
lib.atlas_evaluate.argtypes = [ctypes.POINTER(Request), ctypes.POINTER(Decision)]
lib.atlas_evaluate.restype = ctypes.c_int
lib.atlas_flight.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
lib.atlas_flight.restype = ctypes.c_int

class Policy(rpc.PolicyServicer):
    def __init__(self, token): self.token = token
    def authenticate(self, context):
        supplied = dict(context.invocation_metadata()).get("x-policy-token", "")
        if not hmac.compare_digest(supplied, self.token):
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid service credential")
    def Evaluate(self, request, context):
        self.authenticate(context)
        value = Request(*(getattr(request, name) for name, _ in Request._fields_))
        result = Decision()
        if lib.atlas_evaluate(ctypes.byref(value), ctypes.byref(result)) != 0:
            context.abort(grpc.StatusCode.INTERNAL, "Policy evaluation failed")
        return pb.Decision(allowed=bool(result.allowed), risk=result.risk, reason=result.reason.decode())
    def Flight(self, request, context):
        self.authenticate(context)
        if len(request.subject) > 128 or len(request.flag) > 64 or '\0' in request.subject + request.flag:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Invalid cohort key")
        return pb.FlightDecision(enabled=bool(lib.atlas_flight(
            request.subject.encode(), request.flag.encode(), request.percent)))

def main():
    token = os.environ.get("POLICY_TOKEN", "")
    if len(token) < 32: raise SystemExit("POLICY_TOKEN must contain at least 32 characters")
    configure("atlas-policy")
    GrpcInstrumentorServer().instrument()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8), options=[
        ("grpc.max_receive_message_length", 16384)])
    rpc.add_PolicyServicer_to_server(Policy(token), server)
    address = os.getenv("POLICY_BIND", "127.0.0.1:50051")
    if server.add_insecure_port(address) == 0: raise SystemExit("Cannot bind policy service")
    server.start()
    print("Policy service listening", flush=True)
    try: server.wait_for_termination()
    except KeyboardInterrupt: server.stop(3)
if __name__ == "__main__": main()
