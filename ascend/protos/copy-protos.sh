#!/bin/bash

set -e
set -x

ROOT="$(dirname $0)/.."

cd "$ROOT"
ROOT=$(pwd)
cd ..
SRC="$(pwd)/source"
cd "$ROOT"

copy_file() {
  local path=$1
  cp "$SRC/$path" "$ROOT/$path"
}

copy_file "protos/ascend/ascend.proto"
copy_file "protos/content_encoding/content_encoding.proto"
copy_file "protos/format/format.proto"
copy_file "protos/function/function.proto"
copy_file "protos/io/io.proto"
copy_file "protos/operator/operator.proto"
copy_file "protos/pattern/pattern.proto"
copy_file "protos/schema/schema.proto"
copy_file "protos/text/text.proto"

cd "protos"
sed -i '/java_/d' */*.proto
sed -i '/\.class_tag/d' */*.proto
echo "Done (copy-protos.sh)!"
