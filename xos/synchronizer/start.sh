#if [[ ! -e ./veg-observer.py ]]; then
#    ln -s ../../xos-observer.py veg-observer.py
#fi

export XOS_DIR=/opt/xos
nohup python veg-synchronizer.py  -C $XOS_DIR/synchronizers/veg/veg_synchronizer_config > /dev/null 2>&1 &
