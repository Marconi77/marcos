import numpy as np
import random
from settings import settings

class HistoryList:
    def __init__(self, values=None, histories=None, history_values=None):
        self.values = values if values is not None else []
        self.histories = histories if histories is not None else {
            'mbk': [], 'cb': [], 'deposit': [], 'credit': []}
        self.history_values = history_values if history_values is not None else {
            'mbk': [], 'cb': [], 'deposit': [], 'credit': []}

    def append(self, item: object) -> object:
        self.values.append(item)
        self.history_values[item.flow_type].append(item.amount)

    def extend(self, other):
        for item in other:
            self.values.append(item)
            self.history_values[item.flow_type].append(item.amount)

    def update_history_removed(self, item):
        self.history_values[item.flow_type].append(-item.amount)

    def update_history(self):
        for key in self.history_values.keys():
            if self.histories[key]:
                self.histories[key].append(
                    self.histories[key][-1] + sum(self.history_values[key]))
            else:
                self.histories[key].append(sum(self.history_values[key]))

            self.history_values[key] = []

    def __len__(self):
        return len(self.values)

    def __iter__(self):
        for item in self.values:
            yield item

    def _string_representation(self):
        return f'{self.values}'

    def __repr__(self):
        return self._string_representation()

    def __str__(self):
        return self._string_representation()


class Flow:
    def __init__(self, flow_type, amount=None):
        self.flow_type = flow_type
        self.amount = amount

        # Депозит или Кредит
        if (flow_type == 'deposit' or 'credit') and amount is None:
            self.rate = settings['cb_rate']
            self.volume = round(np.random.uniform(settings[f'{flow_type}_volume_bound'][0],
                                                settings[f'{flow_type}_volume_bound'][1]))
            self.maturity = random.choice(
                settings[f'{flow_type}_maturity'])
            self.days_to_pay = settings['payment_period']

        else:
            raise ValueError(f'Unimplemented type of {flow_type} was given')

    def update_rate(self, delta):
        """
        Функция, которая назначает ставку потоку в зависимости от того,
        в какой банк попал данный поток
        """
        if self.flow_type == 'deposit':
            self.rate = settings['cb_rate'] - delta
        else:
            self.rate = settings['cb_rate'] + delta

    def _string_representation(self):
        return f'{self.flow_type.title()} (тип: {self.flow_type}) сроком погашения {self.maturity} дней, размером {self.volume} рублей, по ставке {self.rate * 100}%, с периодом выплат {self.days_to_pay} дней'

    def __repr__(self):
        return self._string_representation()

    def __str__(self):
        return self._string_representation()


class Bank:
    def __init__(self, name):
        self.name = name
        self.assets = 0

        self.deposits = HistoryList()
        self.credits = HistoryList()

        self.deposit_apps = []
        self.credit_apps = []

        self.cash_history = []


    def set_assets(self, amount):
        self.assets = amount

    def validate(self):
        # Посчитать текущие обязательства по депозитам
        #self.deposits_to_return = sum(deposit.amount for deposit in self.deposit_apps)

        # Понять, сколько сегодня нужно выплатить процентов по депозитам в Market - просуммировать и записать
        deposits_coupon_to_return = sum(deposit.rate * deposit.amount for deposit in self.deposit_apps if not deposit.days_to_pay)

        # Разделить депозиты на те, что возвращаем сегодня и на те, что пока что остаются
        self.deposits_to_return = []
        deposits_to_stay = []

        for deposit in self.deposits:
            # Если депозит истекает сегодня
            if not deposit.maturity:
                self.deposits_to_return.append(deposit)
                self.deposits.update_history_removed(deposit)
            # Если депозит не истекает сегодня
            else:
                # Уменьшаем срок до истечения на 1.
                deposit.maturity -= 1
                # Уменьшаем количество дней до следующегей выплаты, а если сейчас ноль, то ставим новый период
                deposit.days_to_pay = self.settings['payment_period'] if not deposit.days_to_pay else deposit.days_to_pay - 1
                deposits_to_stay.append(deposit)

            self.deposits = HistoryList(
                values=deposits_to_stay, histories=self.deposits.histories, history_values=self.deposits.history_values)

            # Сумма депозитов, которые банк должен выплатить сегодня
            deposits_amount_to_return = sum(deposit.amount +
                                            (deposit.amount * deposit.rate * (
                                                    (self.settings['payment_period'] - deposit.days_to_pay) /
                                                    self.settings['payment_period']))
                                            for deposit in self.deposits_to_return)

            # Сумма всех обязательств банка на сегодня
            self.current_obligations = deposits_coupon_to_return + deposits_amount_to_return

        # Понять, сколько еще предстоит выплатить (обновить список обязательств)
        # Посчитать текушие активы по кредитам
        self.credits_to_receive = sum(credit.amount for credit in self.credit_list)

        # Понять, сколько процентов по кредитам должны вернуть сегодня - просуммировать и записать
        # Понять, сколько еще предстоит получить (обновить список обязательств)


    def solve(self):
        # Вычесть из активов выплаты по депозитам
        # Прибавить поступления из кредитов
        pass

    def get_assets(self):
        print(f"Net Assets of bank '{self.name}' = {self.assets}")

    def take_deposit(self, deposit):
        self.assets += deposit


    def _string_representation(self):
        return self.name

    def __repr__(self):
        return self._string_representation()

    def __str__(self):
        return self._string_representation()


class Market:

    def __init__(self, settings_instance):
        self.settings_instance = settings_instance
        self.settings = self.settings_instance.__dict__

        self.settings_instance.bank_params = list(zip(
            self.settings['simulation_starting_cash'],
            self.settings['simulation_starting_deposits'],
            self.settings['simulation_starting_credits'],

        ))
        # Инициализируем банки и цб
        self.banks = [Bank(i, settings_instance)
                      for i in range(self.settings['banks_number'])]

        all_cash = np.array([bank.cash for bank in self.banks])
        self.init_cash_proportions = all_cash / np.sum(all_cash)

        self.n_deposits = list(np.round(self.init_cash_proportions *
                                        self.settings['deposits_number']).astype(int))
        self.n_credits = list(np.round(self.init_cash_proportions *
                                       self.settings['credits_number']).astype(int))

        self.n_business_credits = list(np.round(self.init_cash_proportions *
                                                self.settings['business_credits_number']).astype(int))

        # Инициализируем стартовые МБК-кредиты/депозиты
        for _ in range(np.random.choice(range(*self.settings['flow_mbk_init_number_bounds']))):
            depositor, creditor = np.random.choice(
                self.banks, 2, replace=False)

            flow_amount = np.random.uniform(
                *self.settings['flow_mbk_init_amount_bounds'])
            flow = Flow('flow', 'mbk', self.settings, flow_amount)

            depositor.credits.append(flow)
            creditor.deposits.append(deepcopy(flow))

        self.cb = CentralBank(settings_instance)
        self.solved_banks = []
        self.unsolved_banks = []
        self.global_step = 0

    def __len__(self):
        return self.settings['banks_number']

    def day_route(self, step):

        if self.settings['applications_distribution'] == 'proportional':
            for bank in self.banks:
                for _ in range(self.n_deposits[bank.id]):
                    bank.potential_deposits.append(
                        Flow('deposit', self.settings))

                for _ in range(self.n_credits[bank.id]):
                    bank.potential_credits.append(
                        Flow('credit', 'standard', self.settings))

                for _ in range(self.n_business_credits[bank.id]):
                    bank.potential_credits.append(
                        Flow('credit', 'business', self.settings))
        elif self.settings['applications_distribution'] == 'uniform':
            # Генерируем потенциальные заявки на депозиты/кредиты и распределяем их по банкам
            for _ in range(self.settings['deposits_number']):
                selected_bank = np.random.choice(
                    range(self.settings['banks_number']))
                self.banks[selected_bank].potential_deposits.append(
                    Flow('deposit', 'standard', self.settings))

            for _ in range(self.settings['credits_number']):
                selected_bank = np.random.choice(
                    range(self.settings['banks_number']))
                self.banks[selected_bank].potential_credits.append(
                    Flow('credit', 'standard', self.settings))

            for _ in range(self.settings['business_credits_number']):
                selected_bank = np.random.choice(
                    range(self.settings['banks_number']))
                self.banks[selected_bank].potential_credits.append(
                    Flow('credit', 'business', self.settings))
        else:
            raise ValueError('Unsopported type of applications distribution')

        # Проверяем, может ли каждый банк расплатиться и записываем в соответствующие списки
        [bank.check_solvency() for bank in self.banks]
        self.cb.check_solvency()

        [self.solved_banks.append(bank) if bank.solved else self.unsolved_banks.append(
            bank) for bank in self.banks]

        # Незакрывшиеся банки отправляем на МБК
        indeces = list(range(len(self.solved_banks)))

        for bank in self.unsolved_banks:
            # Для каждого банка пытаемся найти кредитора среди всех остальных
            # Один кредитор может выдать больше одного кредита
            np.random.shuffle(indeces)
            result = False
            for idx in indeces:
                result = self.banks_commitment(bank, self.solved_banks[idx])
                if result:
                    break
            # Если не закредитовался на МБК, санация ЦБ
            if not result:
                self.central_bank_rescue(self.cb, bank)
                bank.solved = True

        # Производим расчёты
        [bank.solve() for bank in self.banks]

        # Обнуляем состояние банка
        [bank.clear() for bank in self.banks]

        # Обнуляем состояние цб
        self.cb.clear()

        # Обнуляем состояние рынка
        self.clear()

    def clear(self):
        self.unsolved_banks = []
        self.solved_banks = []

    # Функция запуска симуляции
    def run(self, model_number=0, disable=True, shocks={}):
        for step in tqdm(range(self.settings['num_steps']), leave=False, disable=disable,
                         desc=f'Model №{model_number}'):
            if step in shocks:
                self.settings_instance.impose_shocks(shocks[step])

            self.settings_instance.refresh_countable()
            self.settings = self.settings_instance.__dict__
            self.day_route(step)

    # Функция посторной инициализации
    def re_init(self):
        self.__init__()

    # Попытка соглашения о кредите между банками
    def banks_commitment(self, borrower, creditor):

        creditor_ability = (
                                   creditor.cash - creditor.current_obligations) * self.settings['loan_to_give_share']

        # Проверяем, может ли потенциальный кредитор выдать кредит на всю сумму текущего долга
        if creditor_ability >= borrower.loan_amount:
            loan_flow = Flow('flow', 'mbk', self.settings,
                             borrower.loan_amount)

            # В случае успеха добавляем поток как кредит одной стороне и как депозит другой
            borrower.deposits.append(loan_flow)
            creditor.credits.append(deepcopy(loan_flow))
            # self.mbk.append()

            borrower.cash += borrower.loan_amount
            creditor.cash -= borrower.loan_amount

            # Помечаем банк как разрешённый и возвращаем маркер успеха
            borrower.solved = True
            borrower.loan_amount = 0

            return True
        # Если у кредитора недостаточно денег, чтобы покрыть весь объём, то он отдаёт максимум, который может
        else:

            loan_flow = Flow('flow', 'mbk', self.settings, creditor_ability)

            borrower.deposits.append(loan_flow)
            creditor.credits.append(deepcopy(loan_flow))

            borrower.cash += creditor_ability
            creditor.cash -= creditor_ability

            # Уменьшаем текущий долг и возвращаем маркер незакрытого банка
            borrower.loan_amount -= creditor_ability
            return False

    # Санация центральным банком
    def central_bank_rescue(self, central_bank, bank):
        # Центральный банк возмещает под небольшой процент долг банка
        loan_amount = bank.loan_amount
        loan_flow = Flow('flow', 'cb', self.settings, loan_amount)
        central_bank.credits.append(loan_flow)
        bank.deposits.append(deepcopy(loan_flow))

        bank.cash += loan_amount
        bank.loan_amount = 0
        return True

    def refresh_settings_instance(self):
        self.settings = self.settings_instance.__dict__

    def _string_representation(self):
        return f'Instance of market. Can generate deposits and credits. Contains banks.'

    def __str__(self):
        return self._string_representation()

    def __repr__(self):
        return self._string_representation()
