# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/096_Docusaurus_Helper.ipynb.

# %% auto 0
__all__ = ['fix_invalid_syntax_in_markdown', 'generate_markdown_docs', 'generate_sidebar']

# %% ../nbs/096_Docusaurus_Helper.ipynb 2
import itertools
import re
import types
from inspect import Signature, getmembers, isclass, isfunction, signature
from pathlib import Path
from typing import *
from urllib.parse import urljoin

from docstring_parser import parse
from docstring_parser.common import DocstringParam, DocstringRaises, DocstringReturns
from nbdev.config import get_config
from nbdev_mkdocs.mkdocs import (
    _add_all_submodules,
    _import_all_members,
    _import_functions_and_classes,
    _import_submodules,
)

# %% ../nbs/096_Docusaurus_Helper.ipynb 4
def _format_docstring_sections(
    items: Union[List[DocstringParam], List[DocstringReturns], List[DocstringRaises]],
    keyword: str,
) -> str:
    """Format a list of docstring sections

    Args:
        items: A list of DocstringParam objects
        keyword: The type of section to format (e.g. 'Parameters', 'Returns', 'Exceptions')

    Returns:
        The formatted docstring.
    """
    formatted_docstring = ""
    if len(items) > 0:
        formatted_docstring += f"**{keyword}**:\n"
        for item in items:
            if keyword == "Parameters":
                formatted_docstring += f"- `{item.arg_name}`: {item.description}\n"  # type: ignore
            elif keyword == "Exceptions":
                formatted_docstring += f"- `{item.type_name}`: {item.description}\n"
            else:
                formatted_docstring += f"- {item.description}\n"
        formatted_docstring = f"{formatted_docstring}\n"
    return formatted_docstring

# %% ../nbs/096_Docusaurus_Helper.ipynb 8
def _docstring_to_markdown(docstring: str) -> str:
    """Converts a docstring to a markdown-formatted string.

    Args:
        docstring: The docstring to convert.

    Returns:
        The markdown-formatted docstring.
    """
    parsed_docstring = parse(docstring)
    formatted_docstring = f"{parsed_docstring.short_description}\n\n"
    formatted_docstring += (
        f"{parsed_docstring.long_description}\n\n"
        if parsed_docstring.long_description
        else ""
    )
    formatted_docstring += _format_docstring_sections(
        parsed_docstring.params, "Parameters"
    )
    formatted_docstring += _format_docstring_sections(
        parsed_docstring.many_returns, "Returns"
    )
    formatted_docstring += _format_docstring_sections(
        parsed_docstring.raises, "Exceptions"
    )

    return formatted_docstring

# %% ../nbs/096_Docusaurus_Helper.ipynb 12
def _get_submodules(module_name: str) -> List[str]:
    """Get a list of all submodules contained within the module.

    Args:
        module_name: The name of the module to retrieve submodules from

    Returns:
        A list of submodule names within the module
    """
    members = _import_all_members(module_name)
    members_with_submodules = _add_all_submodules(members)
    members_with_submodules_str: List[str] = [
        x[:-1] if x.endswith(".") else x for x in members_with_submodules
    ]
    return members_with_submodules_str

# %% ../nbs/096_Docusaurus_Helper.ipynb 14
def _load_submodules(
    module_name: str, members_with_submodules: List[str]
) -> List[Union[types.FunctionType, Type[Any]]]:
    """Load the given submodules from the module.

    Args:
        module_name: The name of the module whose submodules to load
        members_with_submodules: A list of submodule names to load

    Returns:
        A list of imported submodule objects.
    """
    submodules = _import_submodules(module_name)
    members: List[Tuple[str, Union[types.FunctionType, Type[Any]]]] = list(
        itertools.chain(*[_import_functions_and_classes(m) for m in submodules])
    )
    names = [
        y
        for x, y in members
        if f"{y.__module__}.{y.__name__}" in members_with_submodules
    ]
    return names

# %% ../nbs/096_Docusaurus_Helper.ipynb 16
def _convert_union_to_optional(annotation_str: str) -> str:
    """Convert the 'Union[Type1, Type2, ..., NoneType]' to 'Optional[Type1, Type2, ...]' in the given annotation string

    Args:
        annotation_str: The type annotation string to convert.

    Returns:
        The converted type annotation string.
    """
    pattern = r"Union\[(.*)?,\s*NoneType\s*\]"
    match = re.search(pattern, annotation_str)
    if match:
        union_type = match.group(1)
        optional_type = f"Optional[{union_type}]"
        return re.sub(pattern, optional_type, annotation_str)
    else:
        return annotation_str

# %% ../nbs/096_Docusaurus_Helper.ipynb 18
def _get_arg_list_with_signature(_signature: Signature) -> str:
    """Converts a function's signature into a string representation of its argument list.

    Args:
        _signature (signature): The signature object for the function to convert.

    Returns:
        str: A string representation of the function's argument list.
    """
    arg_list = []
    for param in _signature.parameters.values():
        arg_list.append(_convert_union_to_optional(str(param)))

    return ", ".join(arg_list)

# %% ../nbs/096_Docusaurus_Helper.ipynb 21
def _get_symbol_definition(symbol: Union[types.FunctionType, Type[Any]]) -> str:
    """Return the definition of a given symbol.

    Args:
        symbol: A function or method object to get the definition for.

    Returns:
        A string representing the function definition
    """
    _signature = signature(symbol)
    arg_list = _get_arg_list_with_signature(_signature)
    ret_val = ""

    if isfunction(symbol):
        ret_val = f"### `{symbol.__name__}`" + f" {{#{symbol.__name__.strip('_')}}}\n\n"
        ret_val = ret_val + f"`def {symbol.__name__}({arg_list})"
        if _signature.return_annotation and "inspect._empty" not in str(
            _signature.return_annotation
        ):
            if isinstance(_signature.return_annotation, type):
                ret_val = ret_val + f" -> {_signature.return_annotation.__name__}`\n"
            else:
                ret_val = ret_val + f" -> {_signature.return_annotation}`\n"

        else:
            ret_val = ret_val + " -> None`\n"

    return ret_val

# %% ../nbs/096_Docusaurus_Helper.ipynb 28
def _get_formatted_docstring_for_symbol(
    symbol: Union[types.FunctionType, Type[Any]]
) -> str:
    """Recursively parses and get formatted docstring of a symbol.

    Args:
        symbol: A Python class or function object to parse the docstring for.

    Returns:
        A formatted docstring of the symbol and its members.

    """

    def traverse(symbol: Union[types.FunctionType, Type[Any]], contents: str) -> str:
        """Recursively traverse the members of a symbol and append their docstrings to the provided contents string.

        Args:
            symbol: A Python class or function object to parse the docstring for.
            contents: The current formatted docstrings.

        Returns:
            The updated formatted docstrings.

        """
        for x, y in getmembers(symbol):
            if not x.startswith("_") or x.endswith("__"):
                if isfunction(y) and y.__doc__ is not None:
                    contents += f"{_get_symbol_definition(y)}\n{_docstring_to_markdown(y.__doc__)}"
                elif isclass(y) and not x.startswith("__") and y.__doc__ is not None:
                    contents += f"{_get_symbol_definition(y)}\n{_docstring_to_markdown(y.__doc__)}"
                    contents = traverse(y, contents)
        return contents

    contents = (
        f"{_get_symbol_definition(symbol)}\n{_docstring_to_markdown(symbol.__doc__)}"
        if symbol.__doc__ is not None
        else ""
    )
    if isclass(symbol):
        contents = traverse(symbol, contents)
    return contents

# %% ../nbs/096_Docusaurus_Helper.ipynb 32
def _convert_html_style_attribute_to_jsx(contents: str) -> str:
    """Converts the inline style attributes in an HTML string to JSX compatible format.

    Args:
        contents: A string containing an HTML document or fragment.

    Returns:
        A string with inline style attributes converted to JSX compatible format.
    """
    style_regex = re.compile(r'style="(.+?)"')
    style_matches = style_regex.findall(contents)

    for style_match in style_matches:
        style_dict = {}
        styles = style_match.split(";")
        for style in styles:
            key_value = style.split(":")
            if len(key_value) == 2:
                key = re.sub(
                    r"-(.)", lambda m: m.group(1).upper(), key_value[0].strip()
                )
                value = key_value[1].strip().replace("'", '"')
                style_dict[key] = value
        replacement = "style={{"
        for key, value in style_dict.items():
            replacement += f"{key}: '{value}', "
        replacement = replacement[:-2] + "}}"
        contents = contents.replace(f'style="{style_match}"', replacement)

    return contents

# %% ../nbs/096_Docusaurus_Helper.ipynb 34
def _get_all_markdown_files_path(docs_path: Path) -> List[Path]:
    """Get all Markdown files in a directory and its subdirectories.

    Args:
        directory: The path to the directory to search in.

    Returns:
        A list of paths to all Markdown files found in the directory and its subdirectories.
    """
    markdown_files = [file_path for file_path in docs_path.glob("**/*.md")]
    return markdown_files

# %% ../nbs/096_Docusaurus_Helper.ipynb 36
def _fix_special_symbols_in_html(contents: str) -> str:
    contents = contents.replace("”", '"')
    return contents

# %% ../nbs/096_Docusaurus_Helper.ipynb 38
def _add_file_extension_to_link(url: str) -> str:
    """Add file extension to the last segment of a URL

    Args:
        url: A URL string.

    Returns:
        A string of the updated URL with a file extension added to the last segment of the URL.
    """
    segments = url.split("/#")[0].split("/")[-2:]
    return url.replace(f"/{segments[1]}", f"/{segments[1]}.md")

# %% ../nbs/096_Docusaurus_Helper.ipynb 42
def _fix_symbol_links(
    contents: str, dir_prefix: str, doc_host: str, doc_baseurl: str
) -> str:
    """Fix symbol links in Markdown content.

    Args:
        contents: The Markdown content to search for symbol links.
        dir_prefix: Directory prefix to append in the relative URL.
        doc_host: The host URL for the documentation site.
        doc_baseurl: The base URL for the documentation site.

    Returns:
        str: The Markdown content with updated symbol links.
    """
    prefix = re.escape(urljoin(doc_host + "/", doc_baseurl))
    pattern = re.compile(rf"\[(.*?)\]\(({prefix}[^)]+)\)")
    matches = pattern.findall(contents)
    for match in matches:
        old_url = match[1]
        new_url = _add_file_extension_to_link(old_url).replace("/api/", "/docs/api/")
        dir_prefix = "./" if dir_prefix == "" else dir_prefix
        relative_url = dir_prefix + new_url.split("/docs/")[1]
        contents = contents.replace(old_url, relative_url)
    return contents

# %% ../nbs/096_Docusaurus_Helper.ipynb 49
def _get_relative_url_prefix(docs_path: Path, sub_path: Path) -> str:
    """Returns a relative url prefix from a sub path to a docs path.

    Args:
        docs_path (Path): The docs directory path.
        sub_path (Path): The sub directory path.

    Returns:
        str: A string representing the relative path from the sub path to the docs path.

    Raises:
        ValueError: If the sub path is not a descendant of the docs path.
    """
    try:
        relative_path = sub_path.relative_to(docs_path)
    except ValueError:
        raise ValueError(f"{sub_path} is not a descendant of {docs_path}")

    return (
        "../" * (len(relative_path.parts) - 1) if len(relative_path.parts) > 1 else ""
    )

# %% ../nbs/096_Docusaurus_Helper.ipynb 51
def fix_invalid_syntax_in_markdown(docs_path: str) -> None:
    """Fix invalid HTML syntax in markdown files and converts inline style attributes to JSX-compatible format.

    Args:
        docs_path: The path to the root directory to search for markdown files.
    """
    cfg = get_config()
    doc_host = cfg["doc_host"]
    doc_baseurl = cfg["doc_baseurl"]

    markdown_files = _get_all_markdown_files_path(Path(docs_path))
    for file in markdown_files:
        relative_url_prefix = _get_relative_url_prefix(Path(docs_path), file)
        contents = Path(file).read_text()

        contents = _convert_html_style_attribute_to_jsx(contents)
        contents = _fix_special_symbols_in_html(contents)
        contents = _fix_symbol_links(
            contents, relative_url_prefix, doc_host, doc_baseurl
        )

        file.write_text(contents)

# %% ../nbs/096_Docusaurus_Helper.ipynb 53
def generate_markdown_docs(module_name: str, docs_path: str) -> None:
    """Generates Markdown documentation files for the symbols in the given module and save them to the given directory.

    Args:
        module_name: The name of the module to generate documentation for.
        docs_path: The path to the directory where the documentation files will be saved.
    """
    members_with_submodules = _get_submodules(module_name)
    symbols = _load_submodules(module_name, members_with_submodules)

    for symbol in symbols:
        content = f"## `{symbol.__module__}.{symbol.__name__}` {{#{symbol.__module__}.{symbol.__name__}}}\n\n"
        content += _get_formatted_docstring_for_symbol(symbol)
        target_file_path = (
            "/".join(f"{symbol.__module__}.{symbol.__name__}".split(".")) + ".md"
        )

        with open((Path(docs_path) / "api" / target_file_path), "w") as f:
            f.write(content)

# %% ../nbs/096_Docusaurus_Helper.ipynb 55
def _parse_lines(lines: List[str]) -> Tuple[List[str], int]:
    """Parse a list of lines and return a tuple containing a list of filenames and an index indicating how many lines to skip.

    Args:
        lines: A list of strings representing lines of input text.

    Returns:
        A tuple containing a list of strings representing the filenames extracted
        from links in the lines and an integer representing the number of lines to skip.
    """
    index = next(
        (i for i, line in enumerate(lines) if not line.strip().startswith("- [")),
        len(lines),
    )
    return [line.split("(")[1][:-4] for line in lines[:index]], index

# %% ../nbs/096_Docusaurus_Helper.ipynb 58
def _parse_section(text: str, ignore_first_line: bool = False) -> List[Any]:
    """Parse the given section contents and return a list of file names in the expected format.

    Args:
        text: A string representing the contents of a file.
        ignore_first_line: Flag indicating whether to ignore the first line extracting the section contents.

    Returns:
        A list of filenames in the expected format
    """
    pattern = r"\[.*?\]\((.*?)\)|\[(.*?)\]\[(.*?)\]"
    lines = text.split("\n")[1:] if ignore_first_line else text.split("\n")
    ret_val = []
    index = 0
    while index < len(lines):
        line = lines[index]
        match = re.search(pattern, line.strip())
        if match is not None:
            ret_val.append(match.group(1).split(".md")[0])
            index += 1
        elif line.strip() != "":
            value, skip_lines = _parse_lines(lines[index + 1 :])
            ret_val.append({line.replace("-", "").strip(): value})
            index += skip_lines + 1
        else:
            index += 1
    return ret_val

# %% ../nbs/096_Docusaurus_Helper.ipynb 61
def _get_section_from_markdown(
    markdown_text: str, section_header: str
) -> Optional[str]:
    """Get the contents of the section header from the given markdown text

    Args:
        markdown_text: A string containing the markdown text to extract the section from.
        section_header: A string representing the header of the section to extract.

    Returns:
        A string representing the contents of the section header if the section header
        is present in the markdown text, else None
    """
    pattern = re.compile(rf"^- {section_header}\n((?:\s+- .*\n)+)", re.M)
    match = pattern.search(markdown_text)
    return match.group(1) if match else None

# %% ../nbs/096_Docusaurus_Helper.ipynb 66
def generate_sidebar(
    summary_file: str = "./docusaurus/docs/SUMMARY.md",
    summary: str = "",
    target: str = "./docusaurus/sidebars.js",
) -> None:
    with open(summary_file, "r") as stream, open(target, "w") as target_stream:
        summary_contents = stream.read()

        guides_summary = _get_section_from_markdown(summary_contents, "Guides")
        parsed_guides = _parse_section(guides_summary)  # type: ignore

        api_summary = _get_section_from_markdown(summary_contents, "API")
        parsed_api = _parse_section(api_summary, True)  # type: ignore

        cli_summary = _get_section_from_markdown(summary_contents, "CLI")
        parsed_cli = _parse_section(cli_summary)  # type: ignore

        target_stream.write(
            """module.exports = {
tutorialSidebar: [
    'index', {'Guides': 
    """
            + str(parsed_guides)
            + "},"
            + "{'API': ["
            + str(parsed_api)[1:-1]
            + "]},"
            + "{'CLI': "
            + str(parsed_cli)
            + "},"
            + """
    "LICENSE",
    "CONTRIBUTING",
    "CHANGELOG",
],
};"""
        )
