from typing import Any

from erdpy.accounts import Account
from erdpy.testnet import wallets
from erdpy.testnet.config import TestnetConfiguration
from erdpy.testnet.genesis import get_delegation_address, is_foundational_node

CHAIN_ID = "localnet"


def build(testnet_config: TestnetConfiguration) -> Any:
    num_validators = testnet_config.num_all_validators()
    initial_nodes = []

    for nickname, [pubkey, account] in wallets.get_validators(num_validators).items():
        entry = _build_initial_nodes_entry(nickname, pubkey, account)
        initial_nodes.append(entry)

    # Then, patch the list of initial nodes, so that higher indexes will become metachain nodes.
    num_metachain_nodes = testnet_config.num_validators_in_metashard()
    num_nodes = len(initial_nodes)
    initial_nodes = initial_nodes[num_nodes - num_metachain_nodes:] + initial_nodes[:num_nodes - num_metachain_nodes]

    return {
        "startTime": testnet_config.genesis_time(),
        "roundDuration": 6000,
        "consensusGroupSize": testnet_config.shards["consensus_size"],
        "minNodesPerShard": testnet_config.shards["consensus_size"],
        "metaChainConsensusGroupSize": testnet_config.metashard["consensus_size"],
        "metaChainMinNodes": testnet_config.metashard["validators"],
        "hysteresis": 0,
        "adaptivity": False,
        "chainID": CHAIN_ID,
        "minTransactionVersion": 1,
        "initialNodes": initial_nodes
    }


def _build_initial_nodes_entry(nickname: str, pubkey: str, account: Account) -> Any:
    address = get_delegation_address().bech32() if is_foundational_node(nickname) else account.address.bech32()

    return {
        "nickname": nickname,
        "address": address,
        "pubkey": pubkey,
    }
