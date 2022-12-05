import xml.etree.ElementTree as ET


class PaymentServer:

    def __init__(self, customers: list) -> None:
        self.customers = customers
        self.req = None
        self.transaction_dates = {cust['card_token']: [] for cust in customers}

    def parse_message(self, message: str) -> None:
        tree = ET.parse(message)
        root = tree.getroot()
        self.req = root.find('Transaction')

    def get_token(self) -> str | None:
        token = self.req.find('Token')
        if token is None:
            return None
        return token.text

    def get_amount(self) -> int | None:
        amount = self.req.find('Amount')
        if amount is None:
            return None
        return int(amount.text)

    def get_currency(self) -> str | None:
        currency = self.req.find('Currency')
        if currency is None:
            return None
        return currency.text

    def get_time(self) -> str | None:
        time = self.req.find('Transaction_Time')
        if time is None:
            return None
        return time.text

    def get_city(self) -> str | None:
        merchant = self.req.find('Merchant')
        if merchant is None:
            return None
        return merchant.find('Merchant_City').text

    def get_customer(self, token: str) -> dict | None:
        for customer in self.customers:
            if token == customer['card_token']:
                return customer
        return None

    def create_response(self, result: str, reason: str):
        body = ET.Element('Body')
        response = ET.SubElement(body, 'TransactionResponse')
        ET.SubElement(response, 'Result').text = result
        ET.SubElement(response, 'Reason').text = reason
        tree = ET.ElementTree(body)
        return tree

    def check_conditions(self, customer):
        if customer is None:
            return self.create_response('DECLINED', '')
        transaction_amount = self.get_amount()
        if customer['Limit'] > transaction_amount:
            if transaction_amount > 150:
                return self.create_response('DECLINED', 'TransactionAmountOverLimit')
            self.transaction_dates[customer['card_token']] = self.get_time()
            customer['Limit'] = customer['Limit'] - transaction_amount
            return self.create_response('ACCEPTED', 'None')
        else:
            return self.create_response('DECLINED', 'InsufficientFunds')

    def handle(self, payment_message_request_xml: str) -> str:
        self.parse_message(payment_message_request_xml)
        customer = self.get_customer(self.get_token())
        return self.check_conditions(customer)


def main() -> None:
    with open('resources/limits', 'r') as file:
        major = file.readline().split(',')
        major = [item.strip()[1:-1] for item in major]
        customers = []
        for line in file:
            line = line.split(',')
            line = [item.strip()[1:-1] for item in line]
            customers.append({major[0]: int(line[0]),
                              major[1]: line[1],
                              major[2]: line[2],
                              major[3]: line[3],
                              major[4].strip(): line[4]
                              }
                             )
    server = PaymentServer(customers)
    file_names = [f'resources/payments/payment_{i}.xml' for i in range(1, 21)]
    for file_name in file_names:
        with open(file_name, 'r') as file:
            response = server.handle(file)
        name = file_name.split('.')[0]
        response.write(f'{name}_response.xml')


if __name__ == '__main__':
    main()
