"""Protocol Buffers compilation script for warden-shared."""
import re
import sys
from pathlib import Path
from grpc_tools import protoc

ROOT_DIR = Path(__file__).resolve().parent.parent
PROTO_DIR = ROOT_DIR / "proto"
OUT_DIR = ROOT_DIR / "src" / "warden_shared" / "proto" / "v1"

def compile_all() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR.parent / "__init__.py").touch(exist_ok=True)
    (OUT_DIR / "__init__.py").touch(exist_ok=True)

    proto_files = list(PROTO_DIR.glob("**/*.proto"))
    if not proto_files:
        print("No .proto files found in", PROTO_DIR)
        sys.exit(1)

    print(f"Compiling {len(proto_files)} proto files from {PROTO_DIR} to {OUT_DIR}...")

    cmd = [
        "protoc",
        f"-I{PROTO_DIR}",
        f"--python_out={OUT_DIR}",
        f"--grpc_python_out={OUT_DIR}",
    ] + [str(p) for p in proto_files]

    res = protoc.main(cmd)
    if res != 0:
        print(f"protoc failed with exit code {res}", file=sys.stderr)
        sys.exit(res)

    # Fix relative imports in generated _pb2_grpc.py files
    for grpc_file in OUT_DIR.glob("*_pb2_grpc.py"):
        content = grpc_file.read_text(encoding="utf-8")
        fixed = re.sub(r"^(?:from [\w.]+ )?import (.*_pb2) as (.*)$", r"from . import \1 as \2", content, flags=re.MULTILINE)
        grpc_file.write_text(fixed, encoding="utf-8")

    # If protoc created nested directories (e.g. OUT_DIR/warden/v1), flatten or export them
    nested_dir = OUT_DIR / "warden" / "v1"
    if nested_dir.exists():
        for generated_file in nested_dir.glob("*.py"):
            dest_file = OUT_DIR / generated_file.name
            c = generated_file.read_text(encoding="utf-8")
            fixed = re.sub(r"^(?:from [\w.]+ )?import (.*_pb2) as (.*)$", r"from . import \1 as \2", c, flags=re.MULTILINE)
            dest_file.write_text(fixed, encoding="utf-8")

    # Generate __init__.py exports in OUT_DIR
    init_content = [
        '"""Generated Protocol Buffer stubs for warden.v1."""',
        "try:",
        "    from . import retrieval_pb2, retrieval_pb2_grpc",
        "    from . import laya_pb2, laya_pb2_grpc",
        "    __all__ = [",
        '        "retrieval_pb2",',
        '        "retrieval_pb2_grpc",',
        '        "laya_pb2",',
        '        "laya_pb2_grpc",',
        "    ]",
        "except ImportError:",
        "    pass",
        "",
    ]
    (OUT_DIR / "__init__.py").write_text("\n".join(init_content), encoding="utf-8")
    print("Compilation completed successfully.")

if __name__ == "__main__":
    compile_all()
