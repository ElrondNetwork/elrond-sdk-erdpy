#!/usr/bin/python3
import subprocess
from erdpy.wallet.bech32 import bech32_decode


CHAIN: str = "D"
PROXY: str = "https://devnet-gateway.elrond.com"
CONTRACT_ADDRESS: str = "dev_elrond_address"
OWNER_ADDRESS: str = "dev_elrond_address"
PEM: str = "walletKey.pem"
NAME: str = "My_Token"  # Length between 3 and 20 characters, alphanumeric characters only
TICKER: str = "MYT"  # Length between 3 and 10 character, alphanumeric UPPERCASE only


# Contract Functions
# --value 50000000000000000 equates to 0.05 EGLD
# need to add 0x to the ticket and collection names
def issuance_of_non_fungible_tokens():
    """This function will create your Token. Where you can then associate NFT collections with that token,
    you can have x number of NFTs associated with one token.
    """
    subprocess.run(
        f"""erdpy contract call {CONTRACT_ADDRESS} \
          --pem         {PEM} \
          --chain       {CHAIN} \
          --proxy       {PROXY} \
          --function    issueNonFungible \
          --arguments   {"0x" + NAME.encode('utf-8').hex()} {"0x" + TICKER.encode('utf-8').hex()} \
          --value       50000000000000000 \
          --gas-limit   60000000 \
          --recall-nonce \
          --send""",
        shell=True,
    )


def get_token_identifier():
    """ Previously sent transaction fetched token.
    """
    return "xyz"


def set_special_role_esdt_role_nft_create(token_identifier):
    # Arguments:
    # $1  : Token Identifier
    # $2  : Owner address
    # $3  : ESDTRoleNFTCreate
    subprocess.run(
        f"""erdpy contract call {CONTRACT_ADDRESS} \
          --pem         {PEM} \
          --chain       {CHAIN} \
          --proxy       {PROXY} \
          --function    setSpecialRole \
          --arguments   {token_identifier.encode('utf-8').hex()} {bech32_decode(OWNER_ADDRESS)} {"ESDTRoleNFTCreate".encode('utf-8').hex()} \
          --gas-limit   60000000 \
          --recall-nonce \
          --send""",
        shell=True,
    )


def main():
    """Issue a new NFT token, then set a role for the owners address to allow them to create an NFT."""
    # Issue a new nft
    # https://docs.elrond.com/developers/nft-tokens/#issuance-of-non-fungible-tokens
    issuance_of_non_fungible_tokens()

    token_identifier = get_token_identifier()

    # Set special roles
    # https://docs.elrond.com/developers/nft-tokens/#assigning-roles
    set_special_role_esdt_role_nft_create(token_identifier)


if __name__ == "__main__":
    main()
