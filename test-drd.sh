#!/bin/bash
[ -z "$ASCEND_HOST" ] && echo "Need to set ASCEND_HOST" && exit 1;
TEST_TMP_DIR='tmp-drd-testing'
set -e
set -u
set -o pipefail

setup() {
  mkdir $TEST_TMP_DIR
}

apply_test() {
  ./bin/ascend apply drd_test_1 -i  tests/integration/drd_test_1_dir/
  ./bin/ascend apply drd_test_2 -i tests/integration/drd_test_2_file.yaml
  echo "uniquePiece: `date +%s`" > $TEST_TMP_DIR/config_file
  ./bin/ascend apply drd_test_1 --recursive -i tests/integration/drd_test_1_dir/ --config $TEST_TMP_DIR/config_file
  ./bin/ascend apply drd_test_2 --recursive -i tests/integration/drd_test_2_dir/
  ./bin/ascend apply drd_test_2 --recursive -i tests/integration/drd_test_2_file.yaml
}

list_test() {
  ./bin/ascend list drd_test_1 --recursive
  ./bin/ascend list drd_test_1.ksink_templated --recursive
  ./bin/ascend list drd_test_2 --recursive
}

get_test() {
  ./bin/ascend get drd_test_1 --recursive -d -o "$TEST_TMP_DIR/"
  ./bin/ascend get drd_test_1 --recursive  -o "$TEST_TMP_DIR/drd_test_1.yaml"
  ./bin/ascend get drd_test_2 --recursive -d -o "$TEST_TMP_DIR/"
  ./bin/ascend get drd_test_2 --recursive -o "$TEST_TMP_DIR/drd_test_2.yaml"
}

delete_test() {
  ./bin/ascend delete drd_test_2 --recursive
  ./bin/ascend delete drd_test_1.sub --recursive
  ./bin/ascend delete drd_test_1 --recursive
}

setup
echo 'test apply'
apply_test
echo 'test list'
list_test
echo 'test get'
get_test
echo 'test delete'
delete_test
echo 'cleanup'
rm -rf $TEST_TMP_DIR
echo 'DONE'
