#!/bin/bash

set -e
set -x

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

gen_python "ascend/protos/ascend/ascend.proto"
gen_python "ascend/protos/content_encoding/content_encoding.proto"
gen_python "ascend/protos/format/format.proto"
gen_python "ascend/protos/function/function.proto"
gen_python "ascend/protos/io/io.proto"
gen_python "ascend/protos/operator/operator.proto"
gen_python "ascend/protos/pattern/pattern.proto"
gen_python "ascend/protos/resource/resource.proto"
gen_python "ascend/protos/schema/schema.proto"
gen_python "ascend/protos/text/text.proto"

echo "Done (gen-py.sh)!"
