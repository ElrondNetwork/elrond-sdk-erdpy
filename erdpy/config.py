import os.path
import semver
from typing import Any, Dict, List
from pathlib import Path

from erdpy import errors, utils, workstation

ROOT_FOLDER_NAME = "elrondsdk"
LOCAL_CONFIG_PATH = os.path.join(os.getcwd(), "erdpy.json")
GLOBAL_CONFIG_PATH = os.path.expanduser("~/elrondsdk/erdpy.json")

DEFAULT_GAS_PRICE = 1000000000
GAS_PER_DATA_BYTE = 1500
MIN_GAS_LIMIT = 50000
MAX_GAS_LIMIT = 600000000


class MetaChainSystemSCsCost:
    STAKE = 5000000
    UNSTAKE = 5000000
    UNBOND = 5000000
    CLAIM = 5000000
    GET = 5000000
    CHANGE_REWARD_ADDRESS = 5000000
    CHANGE_VALIDATOR_KEYS = 5000000
    UNJAIL = 5000000
    DELEGATION_MANAGER_OPS = 50000000
    DELEGATION_OPS = 1000000
    UNSTAKE_TOKENS = 5000000
    UNBOND_TOKENS = 5000000


def get_proxy() -> str:
    return get_value("proxy")


def get_chain_id() -> str:
    return get_value("chainID")


def get_tx_version() -> int:
    return int(get_value("txVersion"))


def get_dependency_tag(key: str) -> str:
    return get_value(f"dependencies.{key}.tag")


def set_dependency_tag(key: str, tag: str):
    set_value(f"dependencies.{key}.tag", tag)


def get_dependency_url(key: str, tag: str, platform: str) -> str:
    url_template = get_value(f"dependencies.{key}.urlTemplate.{platform}")
    return url_template.replace("{TAG}", tag)


def get_value(name: str) -> str:
    _guard_valid_name(name)
    data = get_active()
    default_value = get_defaults()[name]
    value = data.get(name, default_value)
    assert isinstance(value, str)
    return value


def set_value(name: str, value: Any):
    _guard_valid_name(name)
    data = read_file()
    active_config = data.get("active", "default")
    data.setdefault("configurations", {})
    data["configurations"].setdefault(active_config, {})
    data["configurations"][active_config][name] = value
    write_file(data)


def delete_value(name: str):
    _guard_valid_config_deletion(name)
    data = read_file()
    active_config = data.get("active", "default")
    data.setdefault("configurations", {})
    data["configurations"].setdefault(active_config, {})
    del data["configurations"][active_config][name]
    write_file(data)


def get_active() -> Dict[str, Any]:
    data = read_file()
    configs = data.get("configurations", {})
    active_config_name: str = data.get("active", "default")
    empty_config: Dict[str, Any] = dict()
    result: Dict[str, Any] = configs.get(active_config_name, empty_config)

    return result;


def set_active(name: str):
    data = read_file()
    _guard_valid_config_name(data, name)
    data["active"] = name
    write_file(data)


def create_new_config(name: str, template: str):
    data = read_file()
    _guard_config_unique(data, name)
    new_config = {}
    if template is not None and template != "":
        _guard_valid_config_name(data, template)
        new_config = data["configurations"][template]

    data["active"] = name
    data.setdefault('configurations', {})
    data["configurations"][name] = new_config
    write_file(data)


def delete_config(name: str):
    _guard_valid_config_deletion(name)
    data = read_file()
    data["configurations"].pop(name, None)
    if data["active"] == name:
        data["active"] = "default"
    write_file(data)


def _guard_valid_name(name: str):
    if name not in get_defaults().keys():
        raise errors.UnknownConfigurationError(name)


def _guard_valid_config_name(config: Any, name: str):
    configurations = config.get('configurations', {})
    if name not in configurations:
        raise errors.UnknownConfigurationError(name)


def _guard_config_unique(config: Any, name: str):
    configurations = config.get('configurations', {})
    if name in configurations:
        raise errors.ConfigurationShouldBeUniqueError(name)


def _guard_valid_config_deletion(name: str):
    if name == "default":
        raise errors.ConfigurationProtectedError(name)


def get_defaults() -> Dict[str, Any]:
    return {
        "proxy": "https://testnet-gateway.elrond.com",
        "chainID": "T",
        "txVersion": "1",
        "dependencies.vmtools.tag": "latest",
        "dependencies.elrond_wasm_rs.tag": "latest",
        "dependencies.vmtools.urlTemplate.linux": "https://github.com/ElrondNetwork/wasm-vm/archive/{TAG}.tar.gz",
        "dependencies.vmtools.urlTemplate.osx": "https://github.com/ElrondNetwork/wasm-vm/archive/{TAG}.tar.gz",
        "dependencies.llvm.tag": "v9-19feb",
        "dependencies.llvm.urlTemplate.linux": "https://ide.elrond.com/vendor-llvm/{TAG}/linux-amd64.tar.gz?t=19feb",
        "dependencies.llvm.urlTemplate.osx": "https://ide.elrond.com/vendor-llvm/{TAG}/darwin-amd64.tar.gz?t=19feb",
        "dependencies.rust.tag": "nightly",
        "dependencies.nodejs.tag": "v12.18.3",
        "dependencies.nodejs.urlTemplate.linux": "https://nodejs.org/dist/{TAG}/node-{TAG}-linux-x64.tar.gz",
        "dependencies.nodejs.urlTemplate.osx": "https://nodejs.org/dist/{TAG}/node-{TAG}-darwin-x64.tar.gz",
        "dependencies.elrond_go.tag": "latest",
        "dependencies.elrond_go.urlTemplate.linux": "https://github.com/ElrondNetwork/elrond-go/archive/{TAG}.tar.gz",
        "dependencies.elrond_go.urlTemplate.osx": "https://github.com/ElrondNetwork/elrond-go/archive/{TAG}.tar.gz",
        "dependencies.elrond_go.url": "https://github.com/ElrondNetwork/elrond-go/archive/{TAG}.tar.gz",
        "dependencies.elrond_proxy_go.tag": "latest",
        "dependencies.elrond_proxy_go.urlTemplate.linux": "https://github.com/ElrondNetwork/elrond-proxy-go/archive/{TAG}.tar.gz",
        "dependencies.elrond_proxy_go.urlTemplate.osx": "https://github.com/ElrondNetwork/elrond-proxy-go/archive/{TAG}.tar.gz",
        "dependencies.golang.tag": "go1.17.6",
        "dependencies.golang.urlTemplate.linux": "https://golang.org/dl/{TAG}.linux-amd64.tar.gz",
        "dependencies.golang.urlTemplate.osx": "https://golang.org/dl/{TAG}.darwin-amd64.tar.gz",
        "dependencies.mcl_signer.tag": "latest",
        "dependencies.mcl_signer.urlTemplate.linux": "https://github.com/ElrondNetwork/elrond-sdk-go-tools/releases/download/{TAG}/mcl_signer_{TAG}_ubuntu-latest.tar.gz",
        "dependencies.mcl_signer.urlTemplate.osx": "https://github.com/ElrondNetwork/elrond-sdk-go-tools/releases/download/{TAG}/mcl_signer_{TAG}_macos-latest.tar.gz",
        "dependencies.wasm-opt.tag": "latest",
        "dependencies.twiggy.tag": "latest",
        "dependencies.wabt.tag": "1.0.27",
        "dependencies.wabt.urlTemplate.linux": "https://github.com/WebAssembly/wabt/releases/download/{TAG}/wabt-{TAG}-ubuntu.tar.gz",
        "dependencies.wabt.urlTemplate.osx": "https://github.com/WebAssembly/wabt/releases/download/{TAG}/wabt-{TAG}-macos.tar.gz",
        "dependencies.testwallets.tag": "latest",
        "dependencies.testwallets.urlTemplate.linux": "https://github.com/ElrondNetwork/elrond-sdk-testwallets/archive/{TAG}.tar.gz",
        "dependencies.testwallets.urlTemplate.osx": "https://github.com/ElrondNetwork/elrond-sdk-testwallets/archive/{TAG}.tar.gz",
        "testnet.validate_expected_keys": "false",
        "github_api_token": "",
    }


def resolve_config_path() -> str:
    if os.path.isfile(LOCAL_CONFIG_PATH):
        return LOCAL_CONFIG_PATH
    return GLOBAL_CONFIG_PATH


def read_file() -> Dict[str, Any]:
    config_path = resolve_config_path()
    if os.path.isfile(config_path):
        data: Dict[str, Any] = utils.read_json_file(config_path)
        return data
    return dict()


def write_file(data: Dict[str, Any]):
    config_path = resolve_config_path()
    utils.write_json_file(config_path, data)


def add_config_args(argv: List[str]) -> List[str]:
    try:
        command, subcommand, *_ = argv
    except ValueError:
        return argv

    config = read_file()

    try:
        config_args = config[command][subcommand]
    except KeyError:
        return argv

    final_args = determine_final_args(argv, config_args)
    print(f"Found extra arguments in erdpy.json. Final arguments: {final_args}")
    return final_args


def determine_final_args(argv: List[str], config_args: Dict[str, Any]) -> List[str]:
    extra_args = []
    for key, value in config_args.items():
        key_arg = f'--{key}'
        # arguments from the command line override the config
        if key_arg in argv:
            continue
        if any(arg.startswith(f"{key_arg}=") for arg in argv):
            continue
        extra_args.append(key_arg)
        if value is True:
            continue
        if isinstance(value, List):
            for item in value:
                extra_args.append(str(item))
        else:
            extra_args.append(str(value))

    # the verbose flag is an exception since it has to go before the command and subcommand
    # eg. erdpy --verbose contract deploy
    verbose_flag = '--verbose'
    pre_args = []
    if verbose_flag in extra_args:
        extra_args.remove(verbose_flag)
        pre_args = [verbose_flag]

    return pre_args + argv + extra_args


def get_dependency_directory(key: str, tag: str) -> Path:
    parent_directory = get_dependency_parent_directory(key)
    if tag == 'latest':
        tag = get_latest_semver_from_directory(parent_directory)

    return parent_directory / tag


def get_dependency_parent_directory(key: str) -> Path:
    tools_folder = Path(workstation.get_tools_folder())
    return tools_folder / key


def get_latest_semver_from_directory(directory: Path) -> str:
    subdirs = [subdir.name for subdir in directory.iterdir()]
    try:
        return get_latest_semver(subdirs)
    except IndexError:
        raise Exception(f'no versions found in {directory}')


def get_latest_semver(versions: List[str]) -> str:
    semantic_versions = parse_strings_to_semver(versions)
    latest_version = sorted(semantic_versions).pop()
    return 'v' + str(latest_version)


def parse_strings_to_semver(version_strings: List[str]) -> List[semver.VersionInfo]:
    versions = []
    for version_string in version_strings:
        try:
            # Omit the 'v' prefix of the version string
            version_string = version_string[1:]
            version = semver.VersionInfo.parse(version_string)
        except ValueError:
            continue

        versions.append(version)

    return versions
