import os
import pathlib
from urllib.parse import urlparse, unquote

from south_africa.tools import utils
from south_africa.tools.http_client import HttpClient

DATA_FOLDER = pathlib.Path(__file__).parent.parent / "data"


async def download(url: str) -> None:
    async with HttpClient() as http_client:
        try:
            resp = await http_client.get(url=url)

            filename = None
            if hasattr(resp, "headers") and "Content-Disposition" in resp.headers:
                cd = resp.headers["Content-Disposition"]
                if "filename=" in cd:
                    filename = cd.split("filename=")[-1].strip('"\'')

            if not filename:
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path)
                filename = unquote(filename)

            if not filename:
                filename = "south-africa-gdp.xlsx"

            slug_name = utils.slugify(filename=filename)
            file_path = os.path.join(DATA_FOLDER, slug_name)

            with open(file_path, "wb") as f:
                f.write(resp.content)

        except Exception:
            raise
