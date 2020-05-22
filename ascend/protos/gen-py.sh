#!/bin/bash

set -e
set -x

# make sure we use the latest grpcio-tools
pip3 install  --upgrade grpcio-tools

ROOT="$(dirname $0)/../.."

cd "$ROOT"
cd "$(pwd -P)"

python_cmd="python3"

gen_python() {
  local path=$1
  local grpc_python_out=$2
  local args=(-m grpc_tools.protoc -I . --python_out=.)
  if [ ${grpc_python_out} ]; then
    args+=(--grpc_python_out=${grpc_python_out});
  fi
  ${python_cmd} "${args[@]}" ${path}
}

find ./ascend/protos/ -name '*.proto' | while read file; do
  gen_python "$file"
done

echo "Done (gen-py.sh)!"
