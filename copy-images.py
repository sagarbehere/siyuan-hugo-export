import pathlib
import logging
import argparse
import regex as re
import shutil

# Below regex detects instances of ![Optional Alt text](path/to/image.ext "Optional title")
# Match group 0 is the whole matched text. Match group 1 is the file path. Match group 2 is the Optional title
images = re.compile(r'!\[[^\]]*\]\((?P<filename>.*?)(?=\"|\))(?P<optionalpart>\".*\")?\)')

URL_PREFIX = "/assets/images/"

def parseargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('notes_dir', help="The full pathname to the folder containing markdown notes exported from SiYuan")
    parser.add_argument('destination_dir', help="The folder into which the image files should be copied")
    args = parser.parse_args()
    return (args.notes_dir, args.destination_dir)


def recreate_target(destination):
    if destination.is_dir():
        shutil.rmtree(destination)
    else:
        logging.info("DESTINATION folder %s does not exist.", str(destination))
    destination.mkdir(parents=True, exist_ok=False)

# Find all image links. For each image link 
# 1) image file path will be like assets/filename.ext 2) Check if image file exists. If it does
# 3) Change file path string to /assets/images/filename.ext 4) Copy image file to $HUGO/static/assets/images/
def process_image_links(notes_dir, destination_dir):
    for file in notes_dir.rglob("*.md"):
        with open(file, 'r') as f:
            file_content = f.read()
            f.close()
            file_content_modified = False
            for image in images.finditer(file_content): # image.group(0) is the matched string, image.group(1) is the path/to/image.ext, image.group(2) is the title, if present
                imagefile = pathlib.Path(file.parent, image.group(1).strip("/").strip()) # Need to remove leading / else pathlib.Path will ignore origin. pathlib.Path() ignores all arguments preceding an argument which contains absolute paths. The extra strip() is needed to remove any whitespace that may exist at the end of the path/to/image.ext
                if not imagefile.exists():
                    print(f"WARNING: {imagefile} referenced in {file} does not exist. Skipping")
                    logging.warning(f"WARNING: {imagefile} referenced in {file} does not exist. Skipping")
                    continue
                else: # The referenced image file exists                   	
                    #print(str(file), " --> ", str(imagefile))
                    logging.info(f"Found reference to {imagefile} in {file}. Replacing with {URL_PREFIX+str(imagefile.name)}")
                    file_content = file_content.replace(image.group(1), URL_PREFIX+str(imagefile.name)+" ")#Need to add the space at the end of the filepath
                    file_content_modified = True
                    shutil.copy2(imagefile, destination_dir)
        # Write the updated content back to the file
        if file_content_modified:
            with open(file, "w", encoding="utf-8") as f:
                f.write(file_content)
                f.close()
        else:
            logging.info(f"No images found in {file}")


def main():
    pathlib.Path('logs').mkdir(parents=True, exist_ok=True) # Create logs/ dir if it does not exist
    logging.basicConfig(filename='logs/copy-images.log', filemode='w', encoding='utf-8', level=logging.DEBUG)

    (notes_dir_string, destination_dir_string) = parseargs()
    notes_dir = pathlib.Path(notes_dir_string)
    destination_dir = pathlib.Path(destination_dir_string)
    if not notes_dir.exists():
        logging.error("ERROR: The notes dir %s does not exist. Exiting", notes_dir)
        raise SystemExit(f"ERROR: The notes dir {notes_dir} does not exist. Exiting.")
    logging.info(f"The notes dir is {notes_dir}")
    logging.info("DELETING target folder {destination_dir}")
    recreate_target(destination_dir)
    process_image_links(notes_dir, destination_dir)

if __name__ == "__main__":
    main()
