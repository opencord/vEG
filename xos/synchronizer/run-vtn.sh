#if [[ ! -e ./veg-observer.py ]]; then
#    ln -s ../../xos-observer.py veg-observer.py
#fi

export XOS_DIR=/opt/xos
cp /root/setup/node_key $XOS_DIR/synchronizers/veg/node_key
chmod 0600 $XOS_DIR/synchronizers/veg/node_key
python veg-synchronizer.py  -C $XOS_DIR/synchronizers/veg/vtn_veg_synchronizer_config
