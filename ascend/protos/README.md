# How to update protos for DRD
1. Make sure your proto updates are present in your `$SOURCE` directory (or switch to a branch that has them)
1. If you created a new proto file, add it to the list in `./ascend/protos/copy-protos.sh`
1. Run `./ascend/protos/copy-protos.sh` from the `sdk-python` directory
1. Run `./ascend/protos/gen-py.sh` from the `sdk-python` directory
1. Increment `API_VERSION` in `ascend/cli/global_values.py` to make sure that the new fields will not be lost
from saved copies downloaded with a newer version
