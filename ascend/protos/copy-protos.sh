#!/bin/bash

set -e
set -x
ROOT=$(dirname "$0")/../..

copy_file() {
  local path=$1
  cp "$SOURCE/$path" "$ROOT/$path"
}

copy_file "ascend/protos/ascend/ascend.proto"
copy_file "ascend/protos/content_encoding/content_encoding.proto"
copy_file "ascend/protos/format/format.proto"
copy_file "ascend/protos/function/function.proto"
copy_file "ascend/protos/io/io.proto"
copy_file "ascend/protos/operator/operator.proto"
copy_file "ascend/protos/pattern/pattern.proto"
copy_file "ascend/protos/schema/schema.proto"
copy_file "ascend/protos/text/text.proto"

cd "$ROOT/ascend/protos"
# remove java options
sed -i '/java_/d' */*.proto
# remove java classtags
sed -i '/\.class_tag/d' */*.proto
echo "Done (copy-protos.sh)!"
