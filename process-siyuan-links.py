import regex as re
import pathlib
import logging
import argparse
import requests

# Replace 'YOUR_API_ENDPOINT' with the actual Siyuan API endpoint
SIYUAN_API_ENDPOINT = "http://localhost:6806"
URL_PREFIX = "/notes/"
HPATH_PREFIX="/Publish/"

def parseargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('notes_dir', help="The full pathname to the folder containing markdown notes exported from SiYuan")
    args = parser.parse_args()
    return (args.notes_dir,)

# Function to make a SQL query to Siyuan API
def query_block_details(block_id):
    query = {"stmt": f"SELECT * FROM blocks WHERE id='{block_id}'"}
    response = requests.post(f"{SIYUAN_API_ENDPOINT}/api/query/sql", json=query)
    return response.json()

def get_new_link(result, notes_dir): #result is the result of the JSON query
    new_link = f'({{{{< ref "/404.html" >}}}})' #set the default link text to the 404 page
    ref_type = result["data"][0].get("type")
    if ref_type == "d": # Ref is of type document
        hpath_value = result["data"][0].get("hpath").removeprefix(HPATH_PREFIX)
        new_link = f'({{{{< ref "{URL_PREFIX}{hpath_value}" >}}}})' # This is Hugo style ref links (https://gohugo.io/content-management/cross-references/). Note that due to Python f string formatting, double curlies {{ in the output need to be expressed as four curlies
    else: #ref is to some block inside a document
        # get markdown, id, hpath, open the target doc, drop anchor, create newlink to hpath#anchor
        block_markdown = result["data"][0].get("markdown")
        block_id = result["data"][0].get("id")
        hpath_value = result["data"][0].get("hpath")
        #Open the target markdown file to place anchor text
        # The target markdown file is either hpath_value.md or hpath_value/_index.md
        if pathlib.Path(str(notes_dir)+hpath_value).is_dir():
            target_file = pathlib.Path(str(notes_dir)+hpath_value+"/_index.md")
        else:
            target_file = pathlib.Path(str(notes_dir)+hpath_value+".md")
        if not target_file.is_file():
            print(f"ERROR: Can't find target file {target_file}. Skipping.")
            logging.error(f"ERROR: Can't find target file {target_file}. Skipping.")
            return new_link
        with open(target_file, 'r') as f:
            content = f.read()
            f.close()
        if not block_markdown in content:
            print(f"ERROR: Can not find content {block_markdown} in {target_file}.This is odd. Shouldn't happen")
            logging.error(f"ERROR: Can not find content {block_markdown} in {target_file}.This is odd. Shouldn't happen")
            return new_link
        cursor_position = content.find(block_markdown)
        if not cursor_position:
            print(f"ERROR: Can not find cursor position for {block_markdown} in {target_file}.This is odd. Shouldn't happen")
            logging.error(f"ERROR: Can not find cursor position for {block_markdown} in {target_file}.This is odd. Shouldn't happen")
            return new_link
        anchor_text = f'{{{{< rawhtml >}}}} <a name="{block_id}"></a> {{{{< /rawhtml >}}}}'
        with open(target_file, 'w') as f:
            f.write(content[:cursor_position] + anchor_text + content[cursor_position:])
            f.close()
        hpath_value = result["data"][0].get("hpath").removeprefix(HPATH_PREFIX)
        new_link = f'({{{{< ref "{URL_PREFIX}{hpath_value}#{block_id}" >}}}})'
    return new_link

def process_siyuan_links(file, notes_dir):
    if not file.exists():
        print("ERROR: The file ", file, " does not exist. Skipping.")
        logging.error("ERROR: The file %s does not exist. Skipping.", file)
        return
    with open (file, "r", encoding="utf-8") as f:
        logging.info(f"Processing {file}")
        content = f.read()
        f.close()
        matches = re.findall(r"\[.*?\]\(siyuan://blocks/(.*?)\)", content)
        if not matches: #No links found
            logging.info(f"{file} has no SiYuan links.")
            return
        for block_id in matches:
            result = query_block_details(block_id)
            if not result["data"]:
                print(f"WARNING: In {file} : No result for block_id {block_id}")
                logging.warning(f"ERROR: In {file} : No result for block_id {block_id}")
            #assumes ref is of a doc, not a block inside a doc
            else:
                #hpath_value = result["data"][0].get("hpath").removeprefix(HPATH_PREFIX) # For my notes, hpath_value will be of the type /Publish/path/to/note. Need to remove the /Publish/ prefix.
                #new_link = f"({URL_PREFIX}{hpath_value}.md)" # Uncomment this (and comment the next line) to enable regular markdown style links
                #new_link = f'({{{{< ref "{URL_PREFIX}{hpath_value}" >}}}})' # This is Hugo style ref links (https://gohugo.io/content-management/cross-references/). Note that due to Python f string formatting, double curlies {{ in the output need to be expressed as four curlies
                new_link = get_new_link(result, notes_dir)
                logging.info(f"Replacing (siyuan://blocks/{block_id}) with {new_link}")
                content = content.replace(f"(siyuan://blocks/{block_id})", new_link)

    # Write the updated content back to the file
    with open(file, "w", encoding="utf-8") as f:
        f.write(content)

def main():
    pathlib.Path('logs').mkdir(parents=True, exist_ok=True) # Create logs/ dir if it does not exist
    logging.basicConfig(filename='logs/process-siyuan-links.log', filemode='w', encoding='utf-8', level=logging.DEBUG)

    (notes_dir_string,) = parseargs()
    notes_dir = pathlib.Path(notes_dir_string)
    if not notes_dir.exists():
        logging.error("ERROR: The notes dir %s does not exist. Exiting", notes_dir)
        raise SystemExit(f"ERROR: The notes dir {notes_dir} does not exist. Exiting.")
    logging.info(f"The notes dir is {notes_dir}")

    for file in notes_dir.rglob("*.md"):
        process_siyuan_links(file, notes_dir)

if __name__ == "__main__":
    main()
