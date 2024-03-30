from settings import settings
import numpy as np
from agents import HistoryList, Flow


liquid_distr = [0.45, 0.14, 0.08, 0.06, 0.05, 0.03, 0.02, 0.02, 0.02, 0.02, 0.02, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01]
banks = {}

for i in range(len(settings['liquid_distribution'])):
    banks[i] = 10e6 * settings['liquid_distribution'][i]
print(f'Bank Sector: {banks}')

system_liquid = sum(banks.values())

print(f'System Liquidity = {sum(banks.values())}')

deposit_1 = np.random.randint(settings['deposit_volume_bound'][0], settings['deposit_volume_bound'][1])
#print(f' DEPOSIT = {deposit_1}')

i = 0
deposits = []
credits = []
while i < settings['num_steps']:  # количество шагов модели
    i += 1
    deposit_supply = []
    credit_supply = []
    for _ in range(np.random.randint(settings["deposit_amount_bound"][0], settings["deposit_amount_bound"][1])):  #генерируем депозиты
        deposit = np.random.randint(settings['deposit_volume_bound'][0], settings['deposit_volume_bound'][1])
        deposit_supply.append(deposit)  # создаем массив из сгенерированных депозитов

    deposits.append(deposit_supply)  # сохраняем пришедшие депозиты в массив

    for _ in range(np.random.randint(settings["credit_amount_bound"][0], settings["credit_amount_bound"][1])):
        credit = np.random.randint(settings['credit_volume_bound'][0], settings['credit_volume_bound'][1])
        credit_supply.append(credit)
    credits.append(credit_supply)

    for _ in range(len(deposit_supply)):
        banks[np.random.randint(0, 20)] += deposit_supply.pop()

    for _ in range(len(credit_supply)):
        banks[np.random.randint(0, 20)] -= credit_supply.pop()

print(deposits[7])
print(credits[7])

print(sorted(banks.values()))
print('---------------------------------------------------------------------------------')

deposit_list = HistoryList()
[deposit_list.append(Flow('deposit')) for _ in range(7)]

test_flow1 = Flow('deposit')
print(test_flow1.__dict__) # -> {'flow_type': 'deposit', 'amount': None, 'volume': 285040, 'maturity': 183, 'days_to_pay': 30}
test_flow2 = Flow('credit')
print(test_flow2.__dict__)

deposit_list.append(test_flow1)
print(deposit_list.history_values)