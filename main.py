import requests
import sys
import io
from bs4 import BeautifulSoup, element
import re


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
        for url in file.readlines():
            if len(url) == 0:
                break
            
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

                            print("Downloading {} to {}".format(file_url, file_name))
                            with open(file_name, "wb") as download_file:
                                for chunk in download_resp.iter_content(chunk_size=1024*1024):
                                    download_file.write(chunk)
    except Exception as e:
        print("Exception: " + e)
        sys.exit(1)


if __name__ == "__main__":
    main()
