import logging
import time
from typing import Any, List, Tuple, Union, cast

from erdpy.accounts import Address
from erdpy.interfaces import IAddress, IElrondProxy, ISimulateCostResponse, ISimulateResponse, ITransactionOnNetwork
from erdpy.proxy.http_facade import do_get, do_post
from erdpy.proxy.messages import NetworkConfig, SimulateCostResponse, SimulateResponse, TransactionOnNetwork

METACHAIN_ID = 4294967295
ANY_SHARD_ID = 0
AWAIT_TRANSACTION_PERIOD = 5

logger = logging.getLogger("proxy")


class ElrondProxy(IElrondProxy):
    def __init__(self, url: str):
        self.url = url

    def get_account_nonce(self, address: IAddress) -> int:
        url = f"{self.url}/address/{address.bech32()}"
        response = do_get(url)
        nonce = response.get("account").get("nonce", 0)
        return int(nonce)

    def get_account_balance(self, address: IAddress):
        url = f"{self.url}/address/{address.bech32()}/balance"
        response = do_get(url)
        balance = response.get("balance", 0)
        return int(balance)

    def get_account(self, address: IAddress):
        url = f"{self.url}/address/{address.bech32()}"
        response = do_get(url)
        account = response.get("account", dict())
        return account

    def get_account_transactions(self, address: Address):
        TRUNCATE_DATA_THRESHOLD = 75

        url = f"{self.url}/address/{address.bech32()}/transactions"
        response = do_get(url)
        transactions = response.get("transactions", [])
        for transaction in transactions:
            data = transaction.get("data") or ""
            data = (data[:TRUNCATE_DATA_THRESHOLD] + ' ... truncated ...') if len(data) > TRUNCATE_DATA_THRESHOLD else data
            transaction["data"] = data
        return transactions

    def get_esdt_tokens(self, address: str) -> List[Any]:
        response = do_get(f"{self.url}/address/{address}/esdt")
        esdts = response.get("esdts")
        return cast(List[Any], esdts)

    def get_esdt_balance(self, address: str, ticker: str) -> dict:
        response = do_get(f"{self.url}/address/{address}/esdt/{ticker}")
        token_data = response.get("tokenData")
        return cast(dict, token_data)

    def get_all_tokens(self) -> List[str]:
        response = do_get(f"{self.url}/network/esdts")
        tokens = response.get("tokens", [])
        return cast(List[str], tokens)

    def get_num_shards(self):
        network_config = self.get_network_config()
        return network_config.num_shards

    def get_epoch(self):
        status = self._get_network_status(METACHAIN_ID)
        nonce = status.get("erd_epoch_number", 0)
        return nonce

    def get_last_block_nonce(self, shard_id: Union[str, int]):
        if shard_id == "metachain":
            metrics = self._get_network_status(METACHAIN_ID)
        else:
            metrics = self._get_network_status(shard_id)

        nonce = metrics.get("erd_highest_final_nonce", 0)
        return nonce

    def get_gas_price(self):
        network_config = self.get_network_config()
        return network_config.min_gas_price

    def get_chain_id(self):
        network_config = self.get_network_config()
        return network_config.chain_id

    def _get_network_status(self, shard_id: Union[str, int]):
        url = f"{self.url}/network/status/{shard_id}"
        response = do_get(url)
        payload = response.get("status")
        return payload

    def get_network_config(self) -> NetworkConfig:
        url = f"{self.url}/network/config"
        response = do_get(url)
        payload = response.get("config")
        result = NetworkConfig(payload)
        return result

    def send_transaction(self, payload: Any) -> str:
        url = f"{self.url}/transaction/send"
        response = do_post(url, payload)
        tx_hash = str(response.get("txHash"))
        return tx_hash

    def simulate_transaction(self, payload: Any) -> ISimulateResponse:
        url = f"{self.url}/transaction/simulate"
        response = do_post(url, payload)
        return SimulateResponse(response)

    def simulate_transaction_cost(self, payload: Any) -> ISimulateCostResponse:
        url = f"{self.url}/transaction/cost"
        response = do_post(url, payload)
        return SimulateCostResponse(response)

    def send_transactions(self, payload: List[Any]) -> Tuple[int, List[str]]:
        url = f"{self.url}/transaction/send-multiple"
        response = do_post(url, payload)
        # Proxy and Observers have different response format:
        num_sent = response.get("numOfSentTxs", 0) or response.get("txsSent", 0)
        hashes = response.get("txsHashes")
        return num_sent, hashes

    def query_contract(self, payload: Any) -> Any:
        url = f"{self.url}/vm-values/query"
        response = do_post(url, payload)
        return response

    def get_transaction(self, tx_hash: str, sender_address: str = "", with_results: bool = False) -> ITransactionOnNetwork:
        url = f"{self.url}/transaction/{tx_hash}"
        url += f"?sender={sender_address or ''}"
        url += f"&withResults={with_results}"

        response = do_get(url)
        return TransactionOnNetwork(tx_hash, response)

    def get_hyperblock(self, key: Union[str, int]) -> Any:
        url = f"{self.url}/hyperblock/by-hash/{key}"
        if str(key).isnumeric():
            url = f"{self.url}/hyperblock/by-nonce/{key}"

        response = do_get(url)
        response = response.get("hyperblock", {})
        return response

    def send_transaction_and_wait_for_result(self, payload: Any, num_seconds_timeout: int = 100) -> ITransactionOnNetwork:
        url = f"{self.url}/transaction/send"
        response = do_post(url, payload)
        tx_hash = response.get("txHash")
        num_periods_to_wait = int(num_seconds_timeout / AWAIT_TRANSACTION_PERIOD)

        for _ in range(0, num_periods_to_wait):
            time.sleep(AWAIT_TRANSACTION_PERIOD)

            tx = self.get_transaction(tx_hash=tx_hash, with_results=True)
            if tx.is_done():
                return tx
            else:
                logger.info("Transaction not yet done.")

        return ITransactionOnNetwork()
 
