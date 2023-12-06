import os
import pathlib
import logging
import argparse
import shutil
import frontmatter

def parseargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('notes_dir', help="The full pathname to the folder containing markdown notes exported from SiYuan")
    args = parser.parse_args()
    return (args.notes_dir,)

def create_index_files(notes_dir): # Move e.g. foo/bar/baz.md to foo/bar/baz/_index.md if foo/bar/baz exists
    logging.info("Creating index files")
    for root, dirs, files in os.walk(notes_dir):
        #for name in files:
            #print(os.path.join(root, name))
        #for name in dirs:
            #print(os.path.join(root, name))
        for file in files:
            if file[:-3] in dirs:
                indx = dirs.index(file[:-3])
                logging.info("Moving %s to %s", pathlib.Path(root, file), pathlib.Path(root, dirs[indx], '_index.md'))
                shutil.move(pathlib.Path(root,file), pathlib.Path(root, dirs[indx], '_index.md'))

    #Sanity check: At this point, all folders in notes_dir should have an _index.md file.
    for root, dirs, files in os.walk(notes_dir):
        for dir in dirs:
            indx_file = pathlib.Path(root, dir, '_index.md')
            if not indx_file.exists():
                logging.error("ERROR: Directory %s does not have an _index.md file.", pathlib.Path(root, dir))

    # Fix frontmatter of _index.md in root folder
    indx_file = pathlib.Path(notes_dir, 'Publish', '_index.md')
    post = frontmatter.load(indx_file)
    post['title'] = 'Notes'
    post['cascade'] = {'type': 'docs'}
    post['menu'] = {'main': {'title': 'Notes', 'weight': '45'}}
    post['publish'] = True
    f = open(indx_file, 'wb') # Note the 'wb'. Need to open file for binary writing, else frontmatter.dump() will not work
    frontmatter.dump(post, f)
    f.close()

def main():
    pathlib.Path('logs').mkdir(parents=True, exist_ok=True) # Create logs/ dir if it does not exist
    logging.basicConfig(filename='logs/create-index-files.log', filemode='w', encoding='utf-8', level=logging.DEBUG)

    (notes_dir_string,) = parseargs()
    notes_dir = pathlib.Path(notes_dir_string)
    if not notes_dir.exists():
        logging.error("ERROR: The notes dir %s does not exist. Exiting", notes_dir)
        raise SystemExit(f"ERROR: The notes dir {notes_dir} does not exist. Exiting.")
    logging.info(f"The notes dir is {notes_dir}")

    create_index_files(notes_dir)

if __name__ == "__main__":
    main()
