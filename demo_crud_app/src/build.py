import argparse
import base64
import mimetypes
import pathlib
from dataclasses import dataclass
from typing import Callable, Literal

import premailer
import requests
import yaml
from bs4 import BeautifulSoup
from jinja2.sandbox import SandboxedEnvironment

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


# based on https://gist.github.com/pansapiens/110431456e8a4ba4f2eb
def inline_images(html: str, working_directory: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for img in soup.find_all("img"):
        img_src = img.attrs["src"]
        mt = mimetypes.guess_type(img_src)[0]
        if not img_src.startswith(
            "http"
        ):  # if it's a relative path, assume it's relative to the working_directory
            if not pathlib.Path(img_src).exists():
                img_src = str(pathlib.Path(working_directory) / pathlib.Path(img_src))
            raw = b""
            with open(img_src, "rb") as f:
                raw = f.read()
            img_b64 = base64.b64encode(raw)
        else:
            img_b64 = base64.b64encode(requests.get(img_src).content)

        img.attrs["src"] = "data:%s;base64,%s" % (mt, img_b64.decode("utf-8"))

    return str(soup)


def _inline_asset(
    html: str, working_directory: str, asset_type: Literal["js", "css"]
) -> str:
    soup = BeautifulSoup(html, "html.parser")
    head = soup.find("head")
    if not head:
        raise ValueError("no <head> in document")

    match asset_type:
        case "js":
            tagname = "script"
            attname = "src"
        case "css":
            tagname = "style"
            attname = "href"
        case _:
            raise NotImplementedError()
    for tag in soup.find_all(tagname):
        src = tag.attrs.get(attname, None)
        if src and not src.startswith(
            "http"
        ):  # if it's a relative path, assume it's relative to the working_directory
            if not pathlib.Path(src).exists():
                src = str(pathlib.Path(working_directory) / pathlib.Path(src))
            with open(src, "r") as f:
                code = f.read()
        else:
            code = requests.get(src).text
        tag = soup.new_tag(tagname)
        tag.string = code
        head.append(tag)
    return str(soup)


def standalone_js(html, working_directory):
    return _inline_asset(html, working_directory, "js")


def standalone_css(html, working_directory):
    return _inline_asset(html, working_directory, "css")


def inline_styles(html, _):
    return premailer.transform(html)


def reformat(html, _):
    prettied = BeautifulSoup(html, "html.parser").prettify(formatter="html")
    return prettied


def transform(transformers: list[Callable[[str, str], str]], html, wd):
    for fn in transformers:
        html = fn(html, wd)
    return html


@dataclass
class Config:
    template: str
    data: dict
    title: str
    working_directory: str


def cli() -> Config:
    parser = argparse.ArgumentParser()
    parser.add_argument("template", help="Jinja2 Template")
    parser.add_argument("data", help="YAML data file")
    parser.add_argument("--title", default="TITLE")
    args = parser.parse_args()
    working_directory = pathlib.Path(args.template).parent.absolute()
    with open(args.template, "r") as tmpl:
        with open(args.data, "r") as data:
            env = SandboxedEnvironment()
            data_tmpl = env.from_string(data.read())
            data = data_tmpl.render({})
            config = Config(
                template=tmpl.read(),
                data=yaml.load(data, Loader=Loader),
                title=args.title,
                working_directory=str(working_directory),
            )
            return config


def render(config: Config) -> str:
    env = SandboxedEnvironment()
    tmpl = env.from_string(config.template)
    data = config.data
    data.update({"title": config.title, "markdown_content": ""})
    raw = tmpl.render(data)
    cooked = transform(
        [
            standalone_js,
            standalone_css,
            inline_images,
            inline_styles,
            reformat,
        ],
        raw,
        config.working_directory,
    )
    return cooked


if __name__ == "__main__":
    conf = cli()
    print(render(conf))
