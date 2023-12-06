import regex as re
import pathlib
import logging
import argparse
import sqlite3
import frontmatter

def parseargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('notes_dir', help="The full pathname to the folder containing markdown notes exported from SiYuan")
    args = parser.parse_args()
    return (args.notes_dir,)

def get_post_title(file):
    post = frontmatter.load(file)
    title = post['title']
    if title:
        return title
    else:
        logging.error("ERROR: Unknown title of {file}")
        return 'Unknown title of'+str(file)

def find_hugo_links(notes_dir, dbconn): # Find all hugo references to other notes and add the details to the sqlite db
   dbcursor = dbconn.cursor()
   for file in notes_dir.rglob("*.md"):
    with open (file, "r", encoding="utf-8") as f:
            logging.info(f"Processing {file} to find Hugo links")
            content = f.read()
            matches = re.findall(r"\{\{< ref\s(.*?) >\}\}", content)

            for match in matches:
                from_file_str = "/notes"+str(file).removeprefix("notes/Publish") # file will be e.g. notes/Publish/snippets/Programmer entrepreneur journey.md. Need to remove the notes/Publish and replace with /notes/snippets/Programmer entrepreneur journey.md
                from_file_title = get_post_title(file)
                #to_file_str = match.strip('"')+".md" # match will be e.g. "/notes/snippets/Simple vs easy" and need to strip the " from beginning and end
                if pathlib.Path(str(notes_dir)+"/Publish/"+match.strip('"').removeprefix("/notes")).is_dir():
                    to_file_str = match.strip('"')+"/_index.md"
                elif pathlib.Path(str(notes_dir)+"/Publish/"+match.strip('"').removeprefix("/notes")+".md").is_file():
                    to_file_str = match.strip('"')+".md"
                else:
                    print(f"ERROR: {file} seems to have invalid link to {match}")
                    logging.error(f"ERROR: {file} seems to have invalid link to {match}")
                    continue

                dbcursor.execute('''INSERT INTO links ("from", "from_title", "to") VALUES (?, ?, ?)''', (from_file_str, from_file_title, to_file_str))
                dbconn.commit()

def add_backlinks(notes_dir, dbconn):
    dbcursor = dbconn.cursor()
    dbcursor.execute('''SELECT DISTINCT "to" FROM links''')
    file_list = dbcursor.fetchall()
    #print(file_list)
    for file in file_list: # file_list is e.g. [('/notes/snippets/Simple vs easy.md',), ('/notes/optional notes/App packaging.md',)]
        if file[0].endswith(".md"):
            logging.info("Processing file %s for adding backlinks", file[0])
            dbcursor.execute('''SELECT DISTINCT "from", "from_title" FROM links WHERE "to" = ?''', (file[0], ))
            backlinks_list = dbcursor.fetchall()
            #print(file[0], backlinks_list)
            filename = pathlib.Path(str(notes_dir)+"/Publish/"+file[0].removeprefix("/notes"))
            #print(filename, backlinks_list)
            newfiledata = ''
            with open(filename, 'r') as f:
                tuples = f.read().rpartition("## Backlinks") # [0] before delimiter [1]delimiter [2] after delimiter OR entire string if no delimiter
                if tuples[0]:
                    filedata = tuples[0].strip()
                else:
                    filedata = tuples[2].strip()
                filedata +=  "\n\n## Backlinks\n"
                for backlink in backlinks_list: # backlinks_list is like [('/notes/snippets/Simple vs easy.md', "Snippets"), ('/notes/optional notes/_index.md', "optional notes")]
                    if backlink[0].endswith("_index.md"):
                        backlink_url = "["+backlink[1]+"]({{< ref \""+backlink[0].rpartition("/")[0]+"\" >}})"
                    else:
                        backlink_url = "["+backlink[1]+"]({{< ref \""+backlink[0].rpartition(".md")[0]+"\" >}})"
                    filedata += "\n- "+backlink_url
                    logging.info("Adding backlink %s to %s", backlink_url, filename)
                newfiledata = filedata
            with open(filename, 'w') as f:
                f.write(newfiledata)
                f.close()

def main():
    pathlib.Path('logs').mkdir(parents=True, exist_ok=True) # Create logs/ dir if it does not exist
    logging.basicConfig(filename='logs/create-backlinks.log', filemode='w', encoding='utf-8', level=logging.DEBUG)

    (notes_dir_string,) = parseargs()
    notes_dir = pathlib.Path(notes_dir_string)
    if not notes_dir.exists():
        logging.error("ERROR: The notes dir %s does not exist. Exiting", notes_dir)
        raise SystemExit(f"ERROR: The notes dir {notes_dir} does not exist. Exiting.")
    logging.info(f"The notes dir is {notes_dir}")

    sqlitedbfilename = 'logs/relations.db'
    dbconn = sqlite3.connect(sqlitedbfilename)

    dbconn.execute('''CREATE TABLE IF NOT EXISTS links (id INTEGER UNIQUE NOT NULL PRIMARY KEY AUTOINCREMENT, "from" TEXT NOT NULL, from_title TEXT, "to" TEXT NOT NULL, to_title TEXT)''')
    dbconn.execute('''DELETE FROM links''')
    dbconn.execute('''DELETE FROM SQLITE_SEQUENCE WHERE name="links"''') # reset the autoincrement id
    dbconn.commit()

    find_hugo_links(notes_dir, dbconn)

    add_backlinks(notes_dir, dbconn)

if __name__ == "__main__":
    main()
