import asyncio
import time
from termcolor import cprint
from eth_abi import abi
from eth_account import Account
from eth_utils import to_int
from client import Client
from config import (
    SYNCSWAP_CONTRACTS, SYNCSWAP_POOL_FACTORY_ABI, TOKENS_PER_CHAIN, ZERO_ADDRESS,
    SYNCSWAP_ROUTER_ABI, SYNCSWAP_POOL_ABI
)
from functions import get_amount


class SyncSwap:
    def __init__(self, client: Client):
        self.client = client
        self.pool_factory_contract = self.client.get_contract(
            contract_address=SYNCSWAP_CONTRACTS[self.client.chain_name]['pool_factory'],
            abi=SYNCSWAP_POOL_FACTORY_ABI
        )
        self.router_contract = self.client.get_contract(
            contract_address=SYNCSWAP_CONTRACTS[self.client.chain_name]['router_v2'],
            abi=SYNCSWAP_ROUTER_ABI
        )


    async def add_liquidity(self, token_name_a: str, token_name_b: str, amount: float):
        tokens_config = TOKENS_PER_CHAIN[self.client.chain_name]

        token_address_a = tokens_config[token_name_a]
        token_address_b = tokens_config[token_name_b]

        amount_in_wei = amount

        pool_address = await self.pool_factory_contract.functions.getPool(
            token_address_a,
            token_address_b
        ).call()
        inputs = [
            [ZERO_ADDRESS, amount_in_wei, True]
        ]
        encode_address = abi.encode(['address'], [self.client.address])

        pool_contract = self.client.get_contract(contract_address=pool_address, abi=SYNCSWAP_POOL_ABI)
        total_supply = await pool_contract.functions.totalSupply().call()
        _, reserve_eth = await pool_contract.functions.getReserves().call()

        min_lp_amount_out = int(amount_in_wei * total_supply / reserve_eth / 2 * 0.98)

        transaction = await self.router_contract.functions.addLiquidity2(
            pool_address,
            inputs,
            encode_address,
            min_lp_amount_out,
            ZERO_ADDRESS,
            '0x',
            ZERO_ADDRESS
        ).build_transaction(await self.client.prepare_tx(value=amount_in_wei))

        return await self.client.send_transaction(transaction)

    async def burn_liquidity(self, token_name_a: str, token_name_b: str):
        tokens_config = TOKENS_PER_CHAIN[self.client.chain_name]

        token_address_a = tokens_config[token_name_a]
        token_address_b = tokens_config[token_name_b]

        pool_address = await self.pool_factory_contract.functions.getPool(
            token_address_a,
            token_address_b
        ).call()

        pool_contract = self.client.get_contract(contract_address=pool_address, abi=SYNCSWAP_POOL_ABI)
        withdraw_mode = 1
        lp_balance_in_wei = await pool_contract.functions.balanceOf(self.client.address).call()

        burn_data = abi.encode(
            ["address", "address", "uint8"],
            [token_address_a, self.client.address, withdraw_mode]
        )

        total_supply = await pool_contract.functions.totalSupply().call()
        _, reserve_eth = await pool_contract.functions.getReserves().call()

        min_eth_amount_out = int(lp_balance_in_wei * reserve_eth * 2 / total_supply * 0.98)

        await self.client.make_approve(
            pool_address, spender_address=self.router_contract.address, amount_in_wei=lp_balance_in_wei
        )

        transaction = await self.router_contract.functions.burnLiquiditySingle(
            pool_address,
            lp_balance_in_wei,
            burn_data,
            min_eth_amount_out,
            ZERO_ADDRESS,
            '0x',
        ).build_transaction(await self.client.prepare_tx())

        return await self.client.send_transaction(transaction)


async def main():
    proxy = ''
    while True:
        try:
            private_key = input("Введите private key: ")
            w3_client = Client(private_key=private_key, proxy=proxy)
            break
        except Exception as er:
            print(f"Некорректный private key! {er}")


    swap_client = SyncSwap(client=w3_client)
    balance = await swap_client.client.get_balance(TOKENS_PER_CHAIN['zkSync']['ETH'])
    amount_in_wei = get_amount(balance)
    cprint("Добавляем в пул ETH", 'light_green')
    await swap_client.add_liquidity('ETH', 'USDT', amount_in_wei)

    response = input("Вывести из пула?")
    if response in "YyДд":
        cprint("Выводим из пула ETH", 'light_green')
        await swap_client.burn_liquidity('ETH', 'USDT')
    else:
        cprint("Программа заgitвершилась")

asyncio.run(main())

