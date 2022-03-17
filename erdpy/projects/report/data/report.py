import functools
from io import StringIO
import json
from pathlib import Path
from typing import Any, List
from erdpy.projects.report.data.folder_report import FolderReport, merge_list_of_folder_reports

from erdpy.projects.report.data.common import flatten_list_of_rows, merge_values
from erdpy.projects.report.format.change_type import ChangeType
from erdpy.projects.report.format.format_options import FormatOptions


class Report:
    def __init__(self, feature_names: List[str], folders: List[FolderReport]) -> None:
        self.feature_names = feature_names
        self.folders = folders

    def to_json(self) -> Any:
        return {
            'features': self.feature_names,
            'folders': self.folders
        }

    @staticmethod
    def from_json(json: Any) -> 'Report':
        folders = [FolderReport.from_json(folder_report) for folder_report in json['folders']]
        return Report(json['features'], folders)

    @staticmethod
    def load_from_file(report_json_path: Path) -> 'Report':
        try:
            with open(report_json_path, 'r') as report_file:
                report_json = json.load(report_file)
                return Report.from_json(report_json)
        except FileNotFoundError:
            return Report([], [])

    def get_markdown_rows(self, format_options: FormatOptions) -> List[List[str]]:
        rows = [folder_report.get_markdown_rows(format_options) for folder_report in self.folders]
        return flatten_list_of_rows(rows)

    def to_markdown(self, format_options: FormatOptions) -> str:
        text = StringIO()

        table_headers = ["Path"] + self.feature_names
        _adjust_table_headers(table_headers, format_options)
        _write_markdown_row(text, table_headers, format_options)

        ALIGN_LEFT = ":--"
        ALIGN_RIGHT = "--:"
        row_alignments = [ALIGN_LEFT] + len(self.feature_names) * [ALIGN_RIGHT]
        _write_markdown_row(text, row_alignments, format_options)

        for row in self.get_markdown_rows(format_options):
            _write_markdown_row(text, row, format_options)

        return text.getvalue()

    def to_json_string(self) -> str:
        return json.dumps(self, indent=4, default=lambda obj: obj.to_json())


# Adjusts the column widths in github tables - see:
# https://github.com/markedjs/marked/issues/266#issuecomment-616347986
def _adjust_table_headers(table_headers: List[str], format_options: FormatOptions) -> None:
    if not format_options.github_flavor:
        return
    NBSP = '\u00A0'
    table_headers[0] = table_headers[0].ljust(60, NBSP)
    table_headers[1] = table_headers[1].rjust(40, NBSP)
    table_headers[2] = table_headers[2].rjust(30, NBSP)
    table_headers[3] = table_headers[3].rjust(30, NBSP)


def merge_list_of_reports(reports: List[Report]) -> Report:
    return functools.reduce(_merge_two_reports, reports)


def _merge_two_reports(first: Report, other: Report) -> Report:
    feature_names = merge_values(first.feature_names, other.feature_names)
    folders = merge_list_of_folder_reports(first.folders, other.folders)
    return Report(feature_names, folders)


# Hack in order to keep the column alignment in a terminal
# as unicode characters are sometimes wider or narrower
def _justify_text_string(string: str, width: int) -> str:
    if ChangeType.UNKNOWN._to_text_markdown() in string:
        width += 1
    if ChangeType.GOOD._to_text_markdown() in string:
        width -= 1
    if ChangeType.BAD._to_text_markdown() in string:
        width -= 1
    return string.rjust(width)


def _format_row_markdown(row: List[str], format_options: FormatOptions) -> str:
    row += [''] * (4 - len(row))
    if not format_options.github_flavor:
        row[0] = row[0].ljust(100)
        row[1] = _justify_text_string(row[1], 20)
        row[2] = _justify_text_string(row[2], 20)
        row[3] = _justify_text_string(row[3], 20)
    merged_cells = " | ".join(row)
    return f"| {merged_cells} |"


def _write_markdown_row(string: StringIO, row: List[str], format_options: FormatOptions):
    string.write(_format_row_markdown(row, format_options))
    string.write('\n')
