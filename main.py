import requests
import sys
import io
from bs4 import BeautifulSoup, element
import re
import os
import os.path


# The whole code is patched together in around 30 mins
# Don't judge it
# Saved my much time, manually opening 50+ tabs and pressing the download
# button twice, because if you see the source code of the website
# first time it is ad
def main() -> None:
    try:
        file: io.TextIOWrapper
        if len(sys.argv) > 1:
            file = open(sys.argv[1], "r")
        else:
            file = sys.stdin # Not good to actually use it, like from console, but you are reading the code, so don't do it

        url: str
        index: int = 0
        curr_path = os.getcwd()
        for url in file.readlines():
            if len(url.strip()) == 0:
                break
            url = url.strip()
            if (url[0] == '#'):
                continue
            if (url[0] == '!'):
                new_path = url[1:]
                if (not(os.path.exists(new_path))):
                    try:
                        os.makedirs(new_path)
                        curr_path = new_path
                    except OSError as e:
                        print("Directory " + new_path + " cannot be created, skipping setting current directory to that")
                        continue
                else:
                    curr_path = new_path
                continue
            
            http_index: int = url.find("http") # we are assuming only few characters can be before the actual url, like " - http://example.com"
            if http_index < 0:
                continue

            index += 1
            url = url[http_index : ]
            resp: requests.Response = requests.get(url)
            soup: BeautifulSoup = BeautifulSoup(resp.content, "html.parser")
            scripts: set = soup.find_all("script")
            
            tag: element.Tag
            for _, tag in enumerate(scripts):
                if "function download()" in tag.text: # Current hard-coding based upon inspection
                    match: re.Match = re.search(r"window.open\(\"([A-Za-z0-9\-\/\.\-\_\:]+)\"\)", tag.text) # Hard-coding based upon inspection
                    if match:
                        file_url: str = str(match.group(1))
                        with requests.get(file_url, stream=True) as download_resp:
                            download_resp.raise_for_status()

                            content_disposition: str = download_resp.headers["Content-Disposition"]
                            file_name_match: re.Match = re.search(r"filename\**=(UTF-8)*\'*\"*(.*)\'*\"*", content_disposition) # I know this regex is flawed, but we need to make do
                            file_name: str = None
                            if file_name_match:
                                file_name = str(file_name_match.group(2))

                            if not file_name:
                                print("Cannot find filename, resorting to index: {}".format(index))
                                file_name = str(index)

                            print("Downloading {} to {}".format(file_url, os.path.join(curr_path, file_name)))
                            with open(os.path.join(curr_path, file_name), "wb") as download_file:
                                big_chunk = None
                                for chunk in download_resp.iter_content(chunk_size=8*1024*1024):
                                    if big_chunk is None:
                                        big_chunk = chunk
                                    else:
                                        big_chunk += chunk
                                    
                                    if len(big_chunk) >= 64 * 1024 * 1024:
                                        download_file.write(big_chunk)
                                        big_chunk = None
                                        
                                if big_chunk is not None:
                                    download_file.write(big_chunk)
                                    big_chunk = None
    except Exception as e:
        print("Exception: " + e)
        sys.exit(1)


if __name__ == "__main__":
    main()
