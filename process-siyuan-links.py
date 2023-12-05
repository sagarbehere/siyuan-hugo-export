import regex as re
import pathlib
import logging
import argparse
import requests

# Replace 'YOUR_API_ENDPOINT' with the actual Siyuan API endpoint
SIYUAN_API_ENDPOINT = "http://localhost:6806"
URL_PREFIX = "/notes"
HPATH_PREFIX_TO_REMOVE="/Publish"

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

def process_siyuan_links(file):
    if not file.exists():
        logging.error("ERROR: The file %s does not exist. Exiting", file)
        return
    with open (file, "r", encoding="utf-8") as f:
        logging.info(f"Processing {file}")
        content = f.read()
        matches = re.findall(r"\[.*?\]\(siyuan://blocks/(.*?)\)", content)
        for block_id in matches:
            result = query_block_details(block_id)
            if not result:
                logging.error("ERROR: No result for block_id {block_id}")
            #assumes ref is of a doc, not a block inside a doc
            if result:
                hpath_value = result["data"][0].get("hpath").removeprefix(HPATH_PREFIX_TO_REMOVE) # For my notes, hpath_value will be of the type /Publish/path/to/note. Need to remove the /Publish prefix.
                #new_link = f"({URL_PREFIX}{hpath_value}.md)" # Uncomment this (and comment the next line) to enable regular markdown style links
                new_link = f'({{{{< ref "{URL_PREFIX}{hpath_value}" >}}}})' # This is Hugo style ref links (https://gohugo.io/content-management/cross-references/). Note that due to Python f string formatting, double curlies {{ in the output need to be expressed as four curlies
                logging.info(f"Replacing (siyuan://blocks/{block_id}) with {new_link}")
                content = content.replace(f"(siyuan://blocks/{block_id})", new_link)
        f.close()
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
        process_siyuan_links(file)

if __name__ == "__main__":
    main()
