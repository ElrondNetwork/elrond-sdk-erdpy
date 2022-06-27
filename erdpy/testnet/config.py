import itertools
import logging
import time
from pathlib import Path
from typing import Any, Dict, Iterator

import erdpy.config
import erdpy.utils as utils
from erdpy import workstation

logger = logging.getLogger("testnet")

ConfigurationDict = Dict[str, Dict[str, Any]]


class Node:
    def __init__(self, index: int, folder: Path, shard: str, api_port: int) -> None:
        self.index = index
        self.folder = folder
        self.shard = shard
        self.api_port = api_port

    def config_folder(self):
        return self.folder / 'config'

    def key_file_path(self):
        return self.config_folder() / 'validatorKey.pem'

    def api_address(self):
        return f"http://localhost:{self.api_port}"

    def __repr__(self) -> str:
        return f"Node {self.index}, shard={self.shard}, port={self.api_port}, folder={self.folder}"


class TestnetConfiguration:
    config: ConfigurationDict
    folders: Dict[str, Path]
    networking: Dict[str, Any]
    metashard: Dict[str, Any]
    shards: Dict[str, Any]
    features: Dict[str, Any]
    timing: Dict[str, Any]
    systemSmartContracts: Dict[str, Any]

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.folders = dict()
        self.networking = dict()
        self.metashard = dict()
        self.shards = dict()
        self.features = dict()
        self.timing = dict()
        self.systemSmartContracts = dict()

        sdk_folder = workstation.get_tools_folder()

        for folder_key, folder_path in self.config['folders'].items():
            if folder_key == 'testnet':
                continue

            folder_path = folder_path.replace('{ELRONDSDK}', str(sdk_folder))

            default_tag = erdpy.config.get_dependency_tag(folder_key)
            if default_tag == 'latest':
                parent_folder = erdpy.config.get_dependency_parent_directory(folder_key)
                default_tag = erdpy.config.get_latest_semver_from_directory(parent_folder)

            folder_path = folder_path.replace('{TAG}', default_tag)

            # If the user has not specified a custom source repository, the
            # ones provided by the SDK will be used, which are downloaded as
            # tar.gz files from GitHub. Due to how the name of the archive is
            # built by GitHub, the path will contain the tag in two variants:
            # with the 'v' prefix (e.g. "v1.1.0"), but also without (e.g.
            # "1.1.0"), hence the need for {NOvTAG}.
            if default_tag.startswith('v'):
                default_tag = default_tag[1:]
            folder_path = folder_path.replace('{NOvTAG}', default_tag)

            self.folders[folder_key] = Path(folder_path).expanduser()

        try:
            self.folders['testnet'] = Path(self.config['folders']['testnet']).expanduser()
        except KeyError:
            self.folders['testnet'] = Path().absolute() / 'testnet'

        self.networking.update(self.config.get('networking', dict()))
        self.metashard.update(self.config.get('metashard', dict()))
        self.shards.update(self.config.get('shards', dict()))
        self.features.update(self.config.get('features', dict()))
        self.timing.update(self.config.get('timing', dict()))
        self.systemSmartContracts.update(self.config.get('systemSmartContracts', dict()))

    @classmethod
    def from_file(cls, filename: str):
        """
        If no filename is specified, try to load testnet.toml from the current
        directory, if there is any, and merge it with the SDK-level testnet
        config. Otherwise, load the SDK-level testnet config. If that one is
        missing as well, generate it from hard-coded defaults.
        """

        local_config = cls.get_local_config(filename)
        sdk_testnet_config = cls.get_sdk_testnet_config()
        final_config = merge_configs(sdk_testnet_config, local_config)
        return cls(final_config)

    @classmethod
    def from_sdk_testnet_config(cls):
        config = cls.get_sdk_testnet_config()
        return cls(config)

    @classmethod
    def from_default_config(cls):
        return cls(cls.default())

    @classmethod
    def get_local_config(cls, filename):
        if filename is None or filename == '':
            filename = Path() / "testnet.toml"
            if not filename.exists():
                return dict()

        return utils.read_toml_file(filename)

    @classmethod
    def get_sdk_testnet_config(cls):
        default = cls.default()
        filename = workstation.get_tools_folder() / "testnet.toml"

        if not filename.exists():
            logger.info('writing sdk_testnet_config from defaults')
            utils.write_toml_file(str(filename), default)
            return default
        sdk_testnet_config = utils.read_toml_file(filename)
        return merge_configs(default, sdk_testnet_config)

    def node_config_source(self) -> Path:
        return self.node_source() / 'cmd' / 'node' / 'config'

    def node_source(self) -> Path:
        path = self.folders['elrond_go']
        assert isinstance(path, Path)
        return path

    def proxy_source(self) -> Path:
        return self.folders['elrond_proxy_go']

    def proxy_config_source(self):
        return self.folders['elrond_proxy_go'] / 'cmd' / 'proxy' / 'config'

    def validator_key_files(self):
        for config_folder in self.validator_config_folders():
            yield config_folder / 'validatorKey.pem'

    def root(self):
        return self.folders['testnet']

    def genesis_time(self):
        return int(time.time()) + int(self.timing['genesis_delay'])

    def rounds_per_epoch(self):
        return self.timing['rounds_per_epoch']

    def seednode_folder(self):
        testnet = self.root()
        return testnet / 'seednode'

    def seednode_config_folder(self):
        return self.seednode_folder() / 'config'

    def seednode_address(self):
        host = self.networking['host']
        port = self.networking['port_seednode']
        identifier = self.networking['p2p_id_seednode']
        return f"/ip4/{host}/tcp/{port}/p2p/{identifier}"

    def proxy_folder(self):
        testnet = self.root()
        return testnet / 'proxy'

    def proxy_config_folder(self):
        return self.proxy_folder() / 'config'

    def num_all_nodes(self):
        return self.num_all_validators() + self.num_all_observers()

    def num_all_validators(self):
        count = (
            self.shards['count'] * self.shards['validators_per_shard'] + self.metashard['validators']
        )
        return count

    def num_all_observers(self):
        count = (
            self.shards['count'] * self.shards['observers_per_shard'] + self.metashard['observers']
        )
        return count

    def num_shards(self):
        return self.shards['count']

    def num_observers_per_shard(self):
        return self.shards['observers_per_shard']

    def num_validators_per_shard(self):
        return self.shards['validators_per_shard']

    def num_validators_in_metashard(self):
        return self.metashard['validators']

    def all_nodes_folders(self):
        return itertools.chain(
            self.validator_folders(),
            self.observer_folders(),
        )

    def all_nodes_config_folders(self):
        return itertools.chain(
            self.validator_config_folders(),
            self.observer_config_folders(),
        )

    def validators(self) -> Iterator[Node]:
        first_port = self.networking['port_first_validator_rest_api']

        for i, folder in enumerate(self.validator_folders()):
            shard = self._get_shard_of_validator(i)
            port = first_port + i
            yield Node(index=i, folder=folder, shard=shard, api_port=port)

    def _get_shard_of_validator(self, observer_index: int):
        shard = int(observer_index // self.num_validators_per_shard())
        return shard if shard < self.num_shards() else self.metashard['metashardID']

    def validator_folders(self):
        testnet = self.root()
        for i in range(self.num_all_validators()):
            yield testnet / 'validator{:02}'.format(i)

    def validator_config_folders(self):
        for folder in self.validator_folders():
            yield folder / 'config'

    def observers(self) -> Iterator[Node]:
        first_port = self.networking['port_first_observer_rest_api']

        for i, folder in enumerate(self.observer_folders()):
            shard = self._get_shard_of_observer(i)
            api_port = first_port + i
            yield Node(index=i, folder=folder, shard=shard, api_port=api_port)

    def _get_shard_of_observer(self, observer_index: int):
        shard = int(observer_index // self.num_observers_per_shard())
        return shard if shard < self.num_shards() else self.metashard['metashardID']

    def observer_config_folders(self):
        for folder in self.observer_folders():
            yield folder / 'config'

    def observer_folders(self):
        testnet = self.root()
        for i in range(self.num_all_observers()):
            yield testnet / 'observer{:02}'.format(i)

    def observer_addresses(self):
        host = self.networking['host']
        first_port = self.networking['port_first_observer_rest_api']
        for port in range(self.num_all_observers()):
            port = first_port + port
            yield f"http://{host}:{port}"

    def validator_addresses(self):
        host = self.networking['host']
        first_port = self.networking['port_first_observer_rest_api']
        for port in range(self.num_all_observers()):
            port = first_port + port
            yield f"http://{host}:{port}"

    def api_addresses_sharded_for_proxy_config(self):
        nodes = list()
        for node in list(self.observers()):
            nodes.append({
                'ShardId': node.shard,
                'Address': node.api_address(),
                'Type': 'Observer'
            })

        for node in list(self.validators()):
            nodes.append({
                'ShardId': node.shard,
                'Address': node.api_address(),
                'Type': 'Validator'
            })

        return nodes

    def proxy_port(self):
        return self.networking["port_proxy"]

    def loglevel(self) -> str:
        return self.features.get("loglevel", "")

    def wasm_vm_binary(self) -> bool:
        return self.features.get("wasm_vm_binary", False)

    @classmethod
    def default(cls):
        config: Dict[str, Any] = dict()
        config['features'] = {
            'loglevel': '*:DEBUG',
            'proxy': True,
            'wasm_vm_binary': False
        }
        config['folders'] = {
            'elrond_go':
                '{ELRONDSDK}/elrond_go/{TAG}/elrond-go-{NOvTAG}',
            'elrond_proxy_go':
                '{ELRONDSDK}/elrond_proxy_go/{TAG}/elrond-proxy-go-{NOvTAG}',
        }
        config['metashard'] = {
            'consensus_size': 1,
            'metashardID': 4294967295,
            'observers': 0,
            'validators': 1,
        }
        config['networking'] = {
            'host': '127.0.0.1',
            'port_seednode': 9999,
            'p2p_id_seednode': '16Uiu2HAkw5SNNtSvH1zJiQ6Gc3WoGNSxiyNueRKe6fuAuh57G3Bk',
            'port_proxy': 7950,
            'port_first_observer': 21100,
            'port_first_observer_rest_api': 10000,
            'port_first_validator': 21500,
            'port_first_validator_rest_api': 10100,
        }
        config['shards'] = {
            'consensus_size': 1,
            'count': 1,
            'observers_per_shard': 0,
            'validators_per_shard': 1,
        }
        config['timing'] = {
            'rounds_per_epoch': 50,
            'genesis_delay': 10
        }

        return config


def merge_configs(leftcfg: ConfigurationDict, rightcfg: ConfigurationDict) -> ConfigurationDict:
    result = dict()
    result.update(leftcfg)

    for key, subcfg in result.items():
        try:
            subcfg.update(rightcfg[key])
        except KeyError:
            pass

    for key in rightcfg:
        if key not in result:
            result[key] = rightcfg[key]

    return result
