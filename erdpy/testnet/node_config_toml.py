from typing import Dict, Any


from erdpy.testnet.config import TestnetConfiguration
from erdpy.testnet.nodes_setup_json import CHAIN_ID

ConfigDict = Dict[str, Any]


def patch_config(data: ConfigDict, testnet_config: TestnetConfiguration):
    data['DbLookupExtensions']['Enabled'] = True
    data['StoragePruning']['ValidatorCleanOldEpochsData'] = False
    data['StoragePruning']['ObserverCleanOldEpochsData'] = False

    general_settings: ConfigDict = dict()
    general_settings['ChainID'] = CHAIN_ID
    general_settings['MinTransactionVersion'] = 1
    general_settings['StartInEpochEnabled'] = True

    data['GeneralSettings'].update(general_settings)

    # Make epochs shorter
    epoch_start_config: ConfigDict = dict()
    epoch_start_config['RoundsPerEpoch'] = testnet_config.rounds_per_epoch()
    epoch_start_config['MinRoundsBetweenEpochs'] = 20
    epoch_start_config['MinShuffledOutRestartThreshold'] = 0.1
    epoch_start_config['MaxShuffledOutRestartThreshold'] = 0.5

    data['EpochStartConfig'].update(epoch_start_config)

    # Always use the latest VM
    virtual_machine: Dict[str, Any] = dict()
    virtual_machine['Execution'] = dict()
    virtual_machine['Execution']['ArwenVersions'] = [{'StartEpoch': 0, 'Version': '*'}]
    virtual_machine['Querying'] = dict()
    virtual_machine['Querying']['NumConcurrentVMs'] = 1
    virtual_machine['Querying']['ArwenVersions'] = [{'StartEpoch': 0, 'Version': '*'}]

    data['VirtualMachine'].update(virtual_machine)


def patch_api(data: ConfigDict, testnet_config: TestnetConfiguration):
    routes = data['APIPackages']['transaction']['Routes']
    for route in routes:
        route['Open'] = True


def validate_expected_keys(actual: ConfigDict, expected: ConfigDict):
    actual_keys = set(actual.keys())
    expected_keys = set(expected.keys())

    unrecognized_keys = actual_keys - expected_keys
    if len(unrecognized_keys) > 0:
        raise ValueError(f'unrecognized configuration keys {unrecognized_keys}')

    missing_keys = expected_keys - actual_keys
    if len(missing_keys) > 0:
        raise ValueError(f'missing configuration keys {missing_keys}')
