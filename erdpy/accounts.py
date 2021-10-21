import logging
import os
from binascii import unhexlify
from os import path
from typing import Any, Optional

from erdpy import constants, errors, utils
from erdpy.errors import LedgerError
from erdpy.interfaces import IAccount, IAddress
from erdpy.wallet import bech32, generate_pair, pem
from erdpy.wallet.keyfile import get_password, load_from_key_file

logger = logging.getLogger("accounts")


class AccountsRepository:
    def __init__(self, folder):
        utils.ensure_folder(folder)
        self.folder = folder

    def get_account(self, name):
        pem_file = path.join(self.folder, f"{name}.pem")
        return Account(pem_file=pem_file)

    def generate_accounts(self, count):
        for i in range(count):
            self.generate_account(i)

    def generate_account(self, name):
        secret_key, pubkey = generate_pair()
        address = Address(pubkey).bech32()

        pem_file = f"{name}_{address}.pem"
        pem_file = path.join(self.folder, pem_file)
        pem.write(pem_file, secret_key, pubkey, name=f"{name}:{address}")

    def get_all(self):
        accounts = []
        for pem_file in os.listdir(self.folder):
            pem_file = path.join(self.folder, pem_file)
            account = Account(pem_file=pem_file)
            accounts.append(account)

        return accounts


class Account(IAccount):
    def __init__(self,
                 address: Any = None,
                 pem_file: Optional[str] = None,
                 pem_index: int = 0,
                 key_file: str = "",
                 pass_file: str = "",
                 ledger: bool = False):
        self.address = Address(address)
        self.pem_file = pem_file
        self.pem_index = int(pem_index)
        self.nonce: int = 0
        self.ledger = ledger

        if self.pem_file:
            secret_key, pubkey = pem.parse(self.pem_file, self.pem_index)
            self.secret_key = secret_key.hex()
            self.address = Address(pubkey)
        elif key_file and pass_file:
            password = get_password(pass_file)
            address_from_key_file, secret_key = load_from_key_file(key_file, password)
            self.secret_key = secret_key.hex()
            self.address = Address(address_from_key_file)

    def sync_nonce(self, proxy: Any):
        logger.info("Account.sync_nonce()")
        self.nonce = proxy.get_account_nonce(self.address)
        logger.info(f"Account.sync_nonce() done: {self.nonce}")

    def get_secret_key(self) -> bytes:
        if self.ledger:
            raise LedgerError("cannot get seed from a Ledger account")
        return unhexlify(self.secret_key)


class Address(IAddress):
    HRP = "erd"
    PUBKEY_LENGTH = 32
    PUBKEY_STRING_LENGTH = PUBKEY_LENGTH * 2    # hex-encoded
    BECH32_LENGTH = 62
    _value_hex: str

    def __init__(self, value):
        self._value_hex = ''

        if not value:
            return

        # Copy-constructor
        if isinstance(value, Address):
            value = value._value_hex

        # We keep a hex-encoded string as the "backing" value
        if len(value) == Address.PUBKEY_LENGTH:
            self._value_hex = value.hex()
        elif len(value) == Address.PUBKEY_STRING_LENGTH:
            self._value_hex = _as_string(value)
        elif len(value) == Address.BECH32_LENGTH:
            self._value_hex = _decode_bech32(value).hex()
        else:
            raise errors.BadAddressFormatError(value)

    def hex(self) -> str:
        self._assert_validity()
        return self._value_hex

    def bech32(self) -> str:
        self._assert_validity()
        pubkey = self.pubkey()
        b32 = bech32.bech32_encode(self.HRP, bech32.convertbits(pubkey, 8, 5))
        assert isinstance(b32, str)
        return b32

    def pubkey(self):
        self._assert_validity()
        pubkey = bytes.fromhex(self._value_hex)
        return pubkey

    def is_contract_address(self):
        return self.hex().startswith(constants.SC_HEX_PUBKEY_PREFIX)

    def _assert_validity(self):
        if self._value_hex == '':
            raise errors.EmptyAddressError()

    def __repr__(self):
        return self.bech32()

    @classmethod
    def zero(cls) -> 'Address':
        return Address("0" * 64)


def _as_string(value):
    if isinstance(value, str):
        return value
    return value.decode("utf-8")


def _decode_bech32(value):
    bech32_string = _as_string(value)
    hrp, value_bytes = bech32.bech32_decode(bech32_string)
    if hrp != Address.HRP:
        raise errors.BadAddressFormatError(value)
    decoded_bytes = bech32.convertbits(value_bytes, 5, 8, False)
    return bytearray(decoded_bytes)
