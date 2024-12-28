# from config import NETWORKS, WETH_ADDRESS
from termcolor import cprint, colored
from web3 import Web3, HTTPProvider


#
# def get_network():
#     """
#     Выбирает сеть для выполнения свапа.
#
#     Возвращает:
#         tuple: Название выбранной сети и ее параметры из NETWORKS.
#     """
#     keys = list(NETWORKS.keys())
#     for key in enumerate(keys, 1):
#         cprint(f'{key[0]}: {key[1]}', 'light_green')
#     while True:
#         try:
#             choice = int(input(colored("Выберите сеть в которой будет сделан свап: ", 'light_green')))
#             if choice < 1 or choice > len(keys):
#                 cprint("Некорректное число, повторите ввод!", 'light_yellow')
#             else:
#                 selected_network = keys[choice - 1]
#                 cprint(f"Вы выбрали сеть {selected_network}", 'light_green')
#                 return NETWORKS[selected_network]
#         except ValueError:
#             cprint("Некорректный символ, введите число!", 'light_yellow')

# def get_token_addr(rpc_url: str, message) -> str:
#     """
#     Получает адрес токена, на который/с которого будет выполнен перевод.
#
#     Параметры:
#         rpc_url (str): URL RPC для подключения к сети.
#
#     Возвращает:
#         str: Адрес токена.
#     """
#     cprint("0 - по умолчанию адрес ETH", 'light_yellow')
#     w3 = Web3(HTTPProvider(rpc_url))
#
#     while True:
#         # Проверка существования токена
#         try:
#             token_address = input(colored(message, 'light_green'))
#             if token_address == '0':
#                 return WETH_ADDRESS
#             # Получение ABI токена (если известен)
#             token_abi = w3.eth.get_code(token_address)
#             if token_abi:
#                 cprint(f"Токен с адресом {token_address} существует.", 'light_green')
#                 return token_address
#             else:
#                 cprint(f"Токен с адресом {token_address} не существует", 'light_yellow')
#                 continue
#         except:
#             cprint(f"Ошибка при проверке токена!", 'light_red')
#
#     async def get_balance(self, token_address:str) -> dict:
#         """
#         Получает баланс кошелька.
#
#         Возвращает:
#             int: Баланс кошелька в wei.
#         """
#
#
#         if token_address in NATIVE_TOKENS_PER_CHAIN:
#             amount_in_wei = await self.w3.eth.get_balance(self.address)
#             decimals = 18
#             self.chain_token = "ETH"
#             return {'amount_in_wei': amount_in_wei, "decimals": decimals, 'name': self.chain_token}
#         else:
#             self.token_contract = self.get_contract(
#                     contract_address=token_address,
#                     abi=GENERAL_ABI)
#             amount_in_wei = await self.token_contract.functions.balanceOf(self.address).call()
#             decimals = await self.token_contract.functions.decimals().call()
#             name = await self.token_contract.functions.name().call()
#             return {'amount_in_wei': amount_in_wei, "decimals": decimals, 'name': name}

def get_amount(balance_decimals_name: dict) -> int:
    """
    Получает количество токена для вывода в wei.

    Параметры:
        balance (int): Баланс в wei.

    Возвращает:
        float: Сумма перевода в нативном токене.
    """
    balance_human = balance_decimals_name['amount_in_wei'] / (10 ** balance_decimals_name['decimals'])
    cprint(f"На вашем счету: {balance_human:.6f} {balance_decimals_name['name']} токена", 'light_green')
    max_amount = balance_human * 0.98
    while True:
        try:
            amount = float(input(colored(f"Введите сумму перевода {balance_decimals_name['name']} токена: ", 'light_green')))
            if amount <= 0:
                cprint(f"Пожалуйста, введите корректное число.", 'light_red')
                continue
            elif balance_human == 0:
                cprint(f"На вашем счету нет токенов", 'light_red')
                exit(1)
            elif max_amount < amount:
                cprint(f"Введенная сумма превышает баланс с учетом коммисии 2%", 'light_red')
                cprint(f"Максимальная возможная сумма {max_amount}", 'light_red')
                continue
            return int(amount * (10**balance_decimals_name['decimals']))
        except ValueError:
            cprint("Пожалуйста, введите корректное число.", 'light_red')

def get_slippage() -> float:
    """
    Получает допустимый процент проскальзывания (Slippage).

    Возвращает:
        float: Процент проскальзывания.
    """
    while True:
        try:
            slippage = float(input(colored("Введите допустимый процент проскальзывания (Slippage) в %: ",
                                           'light_green')))
            if 0 < slippage < 100:
                return slippage
            else:
                cprint("Пожалуйста, введите корректное число.", 'light_yellow')
        except ValueError:
            cprint("Пожалуйста, введите корректное число.", 'light_red')

if __name__ == '__main__':
#     #print(get_network())
#     #get_token_addr('https://arbitrum.llamarpc.com',"Введите адрес токена с которого будем переводить:" )
      get_amount({'amount_in_wei': 10000000000000000, "decimals": 18, 'name': "ETH"})
#     #get_slippage()
#     #help(get_slippage)