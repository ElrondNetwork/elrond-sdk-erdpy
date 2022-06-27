from typing import Any, Dict, List, Tuple
from erdpy.utils import ISerializable


class IAddress:
    def hex(self) -> str:
        return ""

    def bech32(self) -> str:
        return ""

    def pubkey(self) -> bytes:
        return bytes()


class ITransaction(ISerializable):
    def serialize(self) -> bytes:
        return bytes()

    def serialize_as_inner(self) -> str:
        return ''

    def to_dictionary(self) -> Dict[str, Any]:
        return {}

    def to_dictionary_as_inner(self) -> Dict[str, Any]:
        return {}

    def set_version(self, version: int):
        return

    def set_options(self, options: int):
        return

    def get_hash(self) -> str:
        return ""

    def get_data(self) -> str:
        return ""


class IAccount:
    def sign_transaction(self, transaction: ITransaction) -> str:
        return ""
    
    def get_secret_key(self) -> bytes:
        return bytes()


class ITransactionOnNetwork(ISerializable):
    def is_done(self) -> bool:
        return False

    def get_hash(self) -> str:
        return ""


class ISimulateResponse(ISerializable):
    pass


class ISimulateCostResponse(ISerializable):
    pass


class IElrondProxy:
    def get_account_nonce(self, address: IAddress) -> int:
        return 0

    def get_transaction(self, tx_hash: str, sender_address: str = "", with_results: bool = False) -> ITransactionOnNetwork:
        return ITransactionOnNetwork()

    def send_transaction(self, payload: Any) -> str:
        return ""

    def simulate_transaction(self, payload: Any) -> ISimulateResponse:
        return ISimulateResponse()

    def simulate_transaction_cost(self, payload: Any) -> ISimulateCostResponse:
        return ISimulateCostResponse()

    def send_transactions(self, payload: List[Any]) -> Tuple[int, List[str]]:
        return 0, []

    def send_transaction_and_wait_for_result(self, payload: Any, num_seconds_timeout: int) -> ITransactionOnNetwork:
        return ITransactionOnNetwork()

    def query_contract(self, payload: Any) -> Any:
        return dict()
