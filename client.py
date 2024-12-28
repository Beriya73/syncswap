import asyncio

from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.contract import AsyncContract
from web3.exceptions import TransactionNotFound
from termcolor import cprint
from config import ERC20_ABI, TOKENS_PER_CHAIN


class Client:
    def __init__(self, private_key, proxy):
        self.private_key = private_key

        request_kwargs = {'proxy': f'http://{proxy}'}
        rpc_url = 'https://mainnet.era.zksync.io'

        self.chain_name = 'zkSync'
        self.chain_token = 'ETH'
        self.chain_id = 324
        self.proxy = proxy
        self.eip_1559 = True
        self.explorer_url = 'https://era.zksync.network/'
        self.w3 = AsyncWeb3(AsyncHTTPProvider(rpc_url, request_kwargs=request_kwargs))
        self.address = self.w3.to_checksum_address(self.w3.eth.account.from_key(self.private_key).address)

    def to_wei_custom(self, number: int | float, decimals: int = 18):

        unit_name = {
            6: 'mwei',
            9: 'gwei',
            18: 'ether',
        }.get(decimals)

        if not unit_name:
            raise RuntimeError(f'Can not find unit name with decimals: {decimals}')

        return self.w3.to_wei(number, unit_name)

    def from_wei_custom(self, number: int | float, decimals: int):

        unit_name = {
            6: 'mwei',
            9: 'gwei',
            18: 'ether',
        }.get(decimals)

        if not unit_name:
            raise RuntimeError(f'Can not find unit name with decimals: {decimals}')

        return self.w3.from_wei(number, unit_name)

    def get_contract(self, contract_address: str, abi: dict = ERC20_ABI) -> AsyncContract:
        return self.w3.eth.contract(
            address=AsyncWeb3.to_checksum_address(contract_address),
            abi=abi
        )

    async def get_decimals(self, token_name: str):
        if token_name != self.chain_token:
            token_contract = self.get_contract(contract_address=TOKENS_PER_CHAIN[self.chain_name][token_name])
            return await token_contract.functions.decimals().call()
        return 18

    async def make_approve(self, token_address: str, spender_address: str, amount_in_wei: int):
        approve_transaction = await (self.get_contract(contract_address=token_address).functions.approve(
            spender_address,
            amount_in_wei
        ).build_transaction(await self.prepare_tx()))

        cprint(f'Make approve for {spender_address} in {token_address}')

        return await self.send_transaction(approve_transaction)

    async def get_priotiry_fee(self) -> int:
        fee_history = await self.w3.eth.fee_history(5, 'latest', [80.0])
        non_empty_block_priority_fees = [fee[0] for fee in fee_history["reward"] if fee[0] != 0]

        divisor_priority = max(len(non_empty_block_priority_fees), 1)
        priority_fee = int(round(sum(non_empty_block_priority_fees) / divisor_priority))

        return priority_fee

    async def prepare_tx(self, value: int | float = 0):
        transaction = {
            'chainId': await self.w3.eth.chain_id,
            'nonce': await self.w3.eth.get_transaction_count(self.address),
            'from': self.address,
            'value': value,
            'gasPrice': int((await self.w3.eth.gas_price) * 1.25)
        }

        if self.eip_1559:
            del transaction['gasPrice']

            base_fee = await self.w3.eth.gas_price
            max_priority_fee_per_gas = await self.get_priotiry_fee()

            if max_priority_fee_per_gas == 0:
                max_priority_fee_per_gas = base_fee

            max_fee_per_gas = int(base_fee * 1.25 + max_priority_fee_per_gas)

            transaction['maxPriorityFeePerGas'] = max_priority_fee_per_gas
            transaction['maxFeePerGas'] = max_fee_per_gas
            transaction['type'] = '0x2'

        return transaction

    async def send_transaction(
            self, transaction=None, without_gas: bool = False, need_hash: bool = False, ready_tx: bytes = None
    ):
        if ready_tx:
            tx_hash_bytes = await self.w3.eth.send_raw_transaction(ready_tx)

            cprint('Successfully sent transaction!', 'light_green')

            tx_hash_hex = self.w3.to_hex(tx_hash_bytes)
        else:

            if not without_gas:
                transaction['gas'] = int((await self.w3.eth.estimate_gas(transaction)) * 1.5)

            signed_raw_tx = self.w3.eth.account.sign_transaction(transaction, self.private_key).raw_transaction

            cprint('Successfully signed transaction!', 'light_green')

            tx_hash_bytes = await self.w3.eth.send_raw_transaction(signed_raw_tx)

            cprint('Successfully sent transaction!', 'light_green')

            tx_hash_hex = self.w3.to_hex(tx_hash_bytes)

        if need_hash:
            await self.wait_tx(tx_hash_hex)
            return tx_hash_hex

        return await self.wait_tx(tx_hash_hex)

    async def wait_tx(self, tx_hash):
        total_time = 0
        timeout = 120
        poll_latency = 10
        while True:
            try:
                receipts = await self.w3.eth.get_transaction_receipt(tx_hash)
                status = receipts.get("status")
                if status == 1:
                    cprint(f'Transaction was successful: {self.explorer_url}tx/{tx_hash}', 'light_green')
                    return True
                elif status is None:
                    await asyncio.sleep(poll_latency)
                else:
                    cprint(f'Transaction failed: {self.explorer_url}tx/{tx_hash}', 'light_red')
                    return False
            except TransactionNotFound:
                if total_time > timeout:
                    cprint(f"Transaction is not in the chain after {timeout} seconds", 'light_yellow')
                    return False
                total_time += poll_latency
                await asyncio.sleep(poll_latency)

    async def get_balance(self, token_address: str) -> dict:
        """
        Получает баланс кошелька.

        Возвращает:
            int: Баланс кошелька в wei.
        """

        if token_address in TOKENS_PER_CHAIN[self.chain_name]['ETH']:
            amount_in_wei = await self.w3.eth.get_balance(self.address)
            decimals = 18
            self.chain_token = "ETH"
            return {'amount_in_wei': amount_in_wei, "decimals": decimals, 'name': self.chain_token}
        else:
            self.token_contract = self.get_contract(
                contract_address=token_address,
                abi=ERC20_ABI)
            amount_in_wei = await self.token_contract.functions.balanceOf(self.address).call()
            decimals = await self.token_contract.functions.decimals().call()
            name = await self.token_contract.functions.name().call()
            return {'amount_in_wei': amount_in_wei, "decimals": decimals, 'name': name}
