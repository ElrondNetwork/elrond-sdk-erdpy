from typing import Any

from erdpy.testnet.config import TestnetConfiguration


def patch(data: Any, testnet_config: TestnetConfiguration) -> Any:
    data['GeneralSettings']['SCDeployEnableEpoch'] = 0
    data['GeneralSettings']['BuiltInFunctionsEnableEpoch'] = 0
    data['GeneralSettings']['RelayedTransactionsEnableEpoch'] = 0
    data['GeneralSettings']['PenalizedTooMuchGasEnableEpoch'] = 0