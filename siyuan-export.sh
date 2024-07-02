#! /bin/sh

NOTES_DIR=notes/

rm -rf logs/
python3 create-index-files.py $NOTES_DIR
AUTHTOKEN=setmefillmechangeme python3 process-siyuan-links.py $NOTES_DIR
python3 add-backlinks.py $NOTES_DIR
python3 copy-images.py $NOTES_DIR $NOTES_DIR/assets
