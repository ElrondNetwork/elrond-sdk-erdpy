from typing import Any, List, Optional
from erdpy.projects.report.data.common import first_non_none, merge_values_by_key
from erdpy.projects.report.data.option_results import OptionResults, merge_lists_of_option_results


class WasmReport:
    def __init__(self, wasm_name: str, option_results: List[OptionResults]) -> None:
        self.wasm_name = wasm_name
        self.option_results = option_results

    def to_json(self) -> Any:
        return {
            'wasm_name': self.wasm_name,
            'option_results': self.option_results
        }
    
    @staticmethod
    def from_json(json: Any) -> 'WasmReport':
        option_results = [OptionResults.from_json(option_result) for option_result in json['option_results']]
        return WasmReport(json['wasm_name'], option_results)

    def get_option_results(self) -> List[str]:
        return [option.results_to_markdown() for option in self.option_results]


def merge_list_of_wasms(first: List[WasmReport], second: List[WasmReport]) -> List[WasmReport]:
    return merge_values_by_key(first, second, get_wasm_key, merge_two_wasms)


def get_wasm_key(wasm: WasmReport) -> str:
    return wasm.wasm_name


def get_option_results_or_default(wasm: Optional[WasmReport]) -> List[OptionResults]:
    if wasm is None:
        return []
    return wasm.option_results


def merge_two_wasms(first: Optional[WasmReport], second: Optional[WasmReport]) -> WasmReport:
    any = first_non_none(first, second)
    first_option_results = get_option_results_or_default(first)
    second_option_results = get_option_results_or_default(second)
    merged_option_results = merge_lists_of_option_results(first_option_results, second_option_results)
    return WasmReport(any.wasm_name, merged_option_results)
