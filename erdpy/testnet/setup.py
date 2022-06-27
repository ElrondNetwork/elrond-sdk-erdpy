import logging
from pathlib import Path
import shutil
from os import path
from typing import Any

import erdpy.utils as utils
from erdpy import dependencies, myprocess, workstation
from erdpy.dependencies.install import install_module
from erdpy.testnet import (genesis_json, genesis_smart_contracts_json,
                           node_config_toml, nodes_setup_json, p2p_toml,
                           wallets)
from erdpy.testnet.config import TestnetConfiguration

logger = logging.getLogger("testnet")

DEPENDENCY_KEYS = ["elrond_go", "elrond_proxy_go", "testwallets"]


def install_dependencies():
    dependencies.install_module("golang")

    for key in DEPENDENCY_KEYS:
        install_module(key, tag="", overwrite=True)


def configure(args: Any):
    testnet_config = TestnetConfiguration.from_file(args.configfile)
    logger.info('testnet folder is %s', testnet_config.root())

    create_folders(testnet_config)

    # Validators and Observers
    copy_config_to_nodes(testnet_config)
    copy_validator_keys(testnet_config)
    patch_node_config(testnet_config)

    patch_nodes_p2p_config(
        testnet_config,
        testnet_config.validator_config_folders(),
        testnet_config.networking['port_first_validator'],
    )
    patch_nodes_p2p_config(
        testnet_config,
        testnet_config.observer_config_folders(),
        testnet_config.networking['port_first_observer'],
    )
    overwrite_nodes_setup(
        testnet_config,
        testnet_config.validator_config_folders(),
    )
    overwrite_nodes_setup(
        testnet_config,
        testnet_config.observer_config_folders(),
    )
    overwrite_genesis_file(
        testnet_config,
        testnet_config.validator_config_folders()
    )
    overwrite_genesis_file(
        testnet_config,
        testnet_config.observer_config_folders()
    )

    # Seed node
    copy_config_to_seednode(testnet_config)
    patch_seednode_p2p_config(testnet_config)

    # Proxy
    copy_config_to_proxy(testnet_config)
    patch_proxy_config(testnet_config)

    patch_source_code(testnet_config)
    build_binaries(testnet_config)


def clean(args):
    testnet_config = TestnetConfiguration.from_file(args.configfile)
    logger.info('testnet folder is %s', testnet_config.root())
    utils.remove_folder(testnet_config.root())


def create_folders(testnet_config: TestnetConfiguration):
    makefolder(testnet_config.seednode_folder())

    if testnet_config.features['proxy'] is True:
        folder = testnet_config.proxy_folder()
        makefolder(folder)
        makefolder(folder / 'config')

    for folder in testnet_config.all_nodes_folders():
        makefolder(folder)


def copy_config_to_nodes(testnet_config: TestnetConfiguration):
    config_source = testnet_config.node_config_source()
    for node_config in testnet_config.all_nodes_config_folders():
        shutil.copytree(config_source, node_config)

        # Overwrite files when applicable
        overwrites_folder_name = "localnet-node-config"
        sdk_overwrites = workstation.get_tools_folder() / overwrites_folder_name
        cwd_overwrites = Path() / overwrites_folder_name
        if sdk_overwrites.exists():
            logger.info(f"Overwrite configuration with {sdk_overwrites.absolute()}")
            shutil.copytree(sdk_overwrites, node_config, dirs_exist_ok=True)
        if cwd_overwrites.exists():
            logger.info(f"Overwrite configuration with {cwd_overwrites.absolute()}")
            shutil.copytree(cwd_overwrites, node_config, dirs_exist_ok=True)


def copy_validator_keys(testnet_config: TestnetConfiguration):
    for index, validator in enumerate(testnet_config.validators()):
        shutil.copy(wallets.get_validator_key_file(index), validator.key_file_path())

    # Currently, observers require validator PEM files as well
    for index, observer in enumerate(testnet_config.observers()):
        shutil.copy(wallets.get_observer_key_file(index), observer.key_file_path())


def patch_node_config(testnet_config: TestnetConfiguration):
    for node_config in testnet_config.all_nodes_config_folders():
        node_config_file = node_config / 'config.toml'
        data = utils.read_toml_file(node_config_file)
        node_config_toml.patch_config(data, testnet_config)
        utils.write_toml_file(node_config_file, data)

        api_config_file = node_config / 'api.toml'
        data = utils.read_toml_file(api_config_file)
        node_config_toml.patch_api(data, testnet_config)
        utils.write_toml_file(api_config_file, data)


        genesis_smart_contracts_file = node_config / 'genesisSmartContracts.json'
        data = utils.read_json_file(genesis_smart_contracts_file)
        genesis_smart_contracts_json.patch(data, testnet_config)
        utils.write_json_file(genesis_smart_contracts_file, data)


def copy_config_to_seednode(testnet_config: TestnetConfiguration):
    config_source = testnet_config.node_source() / 'cmd' / 'seednode' / 'config'
    seednode_config = testnet_config.seednode_config_folder()
    makefolder(seednode_config)
    shutil.copy(config_source / 'p2p.toml', seednode_config / 'p2p.toml')
    shutil.copy(config_source / 'config.toml', seednode_config / 'config.toml')


def patch_seednode_p2p_config(testnet_config: TestnetConfiguration):
    seednode_config = testnet_config.seednode_config_folder()
    seednode_config_file = seednode_config / 'p2p.toml'

    data = utils.read_toml_file(seednode_config_file)
    p2p_toml.patch_for_seednode(data, testnet_config)
    utils.write_toml_file(seednode_config_file, data)


def patch_nodes_p2p_config(testnet_config: TestnetConfiguration, nodes_config_folders, port_first):
    for index, config_folder in enumerate(nodes_config_folders):
        config = config_folder / 'p2p.toml'
        data = utils.read_toml_file(config)
        p2p_toml.patch(data, testnet_config, index, port_first)
        utils.write_toml_file(config, data)


def overwrite_nodes_setup(testnet_config: TestnetConfiguration, nodes_config_folders):
    nodes_setup = nodes_setup_json.build(testnet_config)

    for index, config_folder in enumerate(nodes_config_folders):
        config = config_folder / 'nodesSetup.json'
        utils.write_json_file(str(config), nodes_setup)


def overwrite_genesis_file(testnet_config: TestnetConfiguration, nodes_config_folders):
    genesis = genesis_json.build(testnet_config)

    for index, config_folder in enumerate(nodes_config_folders):
        config = config_folder / 'genesis.json'
        utils.write_json_file(str(config), genesis)


def copy_config_to_proxy(testnet_config: TestnetConfiguration):
    proxy_config_source = testnet_config.proxy_config_source()
    proxy_config = testnet_config.proxy_config_folder()
    makefolder(proxy_config)

    shutil.copy(proxy_config_source / 'config.toml', proxy_config)
    shutil.copytree(proxy_config_source / 'apiConfig', proxy_config / 'apiConfig')
    shutil.copy(proxy_config_source / 'external.toml', proxy_config)


def patch_proxy_config(testnet_config: TestnetConfiguration):
    proxy_config_file = testnet_config.proxy_config_folder() / 'config.toml'
    nodes = testnet_config.api_addresses_sharded_for_proxy_config()
    data = utils.read_toml_file(proxy_config_file)
    data['Observers'] = nodes
    data['FullHistoryNodes'] = nodes
    data['GeneralSettings']['ServerPort'] = testnet_config.proxy_port()
    utils.write_toml_file(proxy_config_file, data)

    api_config_file = path.join(testnet_config.proxy_config_folder(), 'apiConfig', 'v1_0.toml')
    data = utils.read_toml_file(api_config_file)
    routes = data['APIPackages']['transaction']['Routes']
    for route in routes:
        route["Open"] = True
    utils.write_toml_file(api_config_file, data)


def makefolder(path_where_to_make_folder):
    path_where_to_make_folder.mkdir(parents=True, exist_ok=True)


def patch_source_code(testnet_config: TestnetConfiguration):
    logger.info("Patching the source code...")

    node_source = testnet_config.node_source()

    file = node_source / 'cmd' / 'node' / 'main.go'
    content = utils.read_text_file(file)
    content = content.replace("secondsToWaitForP2PBootstrap = 20", "secondsToWaitForP2PBootstrap = 1")
    utils.write_file(file, content)


def build_binaries(testnet_config: TestnetConfiguration):
    golang = dependencies.get_golang()
    golang_env = golang.get_env()
    myprocess.run_process(['go', 'env'], env=golang_env)

    logger.info("Building seednode...")
    seednode_folder = testnet_config.node_source() / "cmd" / "seednode"
    myprocess.run_process(['go', 'build'], cwd=seednode_folder, env=golang_env)

    logger.info("Building node...")
    node_folder = testnet_config.node_source() / "cmd" / "node"
    myprocess.run_process(['go', 'build'], cwd=node_folder, env=golang_env)

    wasm_vm_binary = testnet_config.wasm_vm_binary()
    if wasm_vm_binary:
        logger.warn("WASM VM does not require building anymore. Skipping...")

    logger.info("Building proxy...")
    proxy_folder = testnet_config.proxy_source() / "cmd" / "proxy"
    myprocess.run_process(['go', 'build'], cwd=proxy_folder, env=golang_env)

    # Now copy the binaries to the testnet folder
    wasm_vm_version = _get_wasm_vm_version(testnet_config)
    libwasmer_path = path.join(golang.get_gopath(), f"pkg/mod/github.com/!elrond!network/arwen-wasm-vm@{wasm_vm_version}/wasmer/libwasmer_darwin_amd64.dylib")

    shutil.copy(seednode_folder / "seednode", testnet_config.seednode_folder())
    if workstation.get_platform() == "osx":
        shutil.copy(libwasmer_path, testnet_config.seednode_folder())

    for destination in testnet_config.all_nodes_folders():
        shutil.copy(node_folder / "node", destination)

        if workstation.get_platform() == "osx":
            shutil.copy(libwasmer_path, destination)

    shutil.copy(proxy_folder / "proxy", testnet_config.proxy_folder())
    if workstation.get_platform() == "osx":
        shutil.copy(libwasmer_path, testnet_config.proxy_folder())


def _get_wasm_vm_version(testnet_config: TestnetConfiguration):
    go_mod = testnet_config.node_source() / "go.mod"
    lines = utils.read_lines(go_mod)
    line = next(line for line in lines if "github.com/ElrondNetwork/arwen-wasm-vm" in line)
    parts = line.split()
    return parts[1]
