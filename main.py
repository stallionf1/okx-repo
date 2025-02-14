import time
import random
from web3 import Web3

# ====================================================
# НАЛАШТУВАННЯ
# ====================================================

RPC_URL = "https://ethereum-rpc.publicnode.com"

NUM_CYCLES = 5          # Скільки циклів виконувати
CYCLE_TIMEOUT = 60      # Таймаут між циклами, с
TRANSACTIONS_PER_WALLET = 1  # Кількість транзакцій на одну пару (гаманець → адреса)
TRANSACTION_TIMEOUT = 20      # Таймаут між транзакціями, с

GAS_PRICE_THRESHOLD_GWEI = 5  # Поріг ціни gas у Gwei

# Мінімальна і максимальна кількість ETH на одну транзакцію
MIN_SEND_ETH = 0.0001
MAX_SEND_ETH = 0.0005

GAS_LIMIT = 21000
CHAIN_ID = 1

# ====================================================
# Ініціалізація Web3
# ====================================================
w3 = Web3(Web3.HTTPProvider(RPC_URL))

if not w3.is_connected():
    raise ConnectionError("Неможливо підключитися до Ethereum RPC. Перевірте RPC_URL або інтернет-з'єднання.")

# ====================================================
# Функція для читання файлу і пропуску закоментованих рядків
# ====================================================
def read_noncommented_lines(filepath):
    """
    Зчитує файл построчно і повертає список,
    де пропущені порожні рядки та ті, що починаються з '#'.
    """
    lines = []
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                # Пропускаємо порожні та закоментовані рядки
                continue
            lines.append(line)
    return lines

# ====================================================
# Зчитування приватних ключів та адрес із файлів
# ====================================================
private_keys = read_noncommented_lines("private_keys.txt")
to_addresses = read_noncommented_lines("to_addresses.txt")

if not private_keys:
    raise ValueError("У файлі private_keys.txt немає жодного активного ключа (усі закоментовано або файл порожній).")
if not to_addresses:
    raise ValueError("У файлі to_addresses.txt немає жодної активної адреси (усі закоментовано або файл порожній).")

# ====================================================
# Функції
# ====================================================
def get_current_gas_price_gwei():
    """Повертає поточну ціну gas у Gwei (конвертація з Wei)."""
    gas_price_wei = w3.eth.gas_price
    gas_price_gwei = gas_price_wei / 10**9
    return gas_price_gwei

def send_eth(private_key, to_addr, amount_eth):
    """Відправляє 'amount_eth' ETH з гаманця (private_key) на 'to_addr'."""
    # Перевіряємо, що адреса валідна
    if not w3.is_address(to_addr):
        raise ValueError(f"Невірна адреса отримувача: {to_addr}")

    account = w3.eth.account.from_key(private_key)
    from_address = account.address

    # Отримати nonce (скільки транзакцій уже було з цього гаманця)
    nonce = w3.eth.get_transaction_count(from_address)
    gas_price_wei = w3.eth.gas_price

    tx = {
        'nonce': nonce,
        'to': to_addr,
        'value': w3.to_wei(amount_eth, 'ether'),  # конвертація в Wei
        'gas': GAS_LIMIT,
        'gasPrice': gas_price_wei,
        'chainId': CHAIN_ID
    }

    signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)  # web3.py 6.x
    return tx_hash.hex()

def main():
    for cycle_index in range(NUM_CYCLES):
        print(f"\n=== Цикл {cycle_index+1}/{NUM_CYCLES} ===")

        current_gas_price_gwei = get_current_gas_price_gwei()
        print(f"Поточна ціна gas: {current_gas_price_gwei:.2f} Gwei")

        if current_gas_price_gwei < GAS_PRICE_THRESHOLD_GWEI:
            print(f"Ціна газу нижча за {GAS_PRICE_THRESHOLD_GWEI} Gwei. Виконуємо транзакції...")

            # Згідно логіки: кожен i-й ключ відправляє ETH на i-ту адресу.
            for idx, (pk, to_addr) in enumerate(zip(private_keys, to_addresses), start=1):
                account_address = w3.eth.account.from_key(pk).address
                print(f"\n  {idx}. Гаманець {account_address} → {to_addr}")

                for tx_count in range(TRANSACTIONS_PER_WALLET):
                    amount_to_send = random.uniform(MIN_SEND_ETH, MAX_SEND_ETH)
                    print(f"    [{tx_count+1}/{TRANSACTIONS_PER_WALLET}] Відправляємо {amount_to_send:.6f} ETH ...")
                    try:
                        tx_hash = send_eth(pk, to_addr, amount_to_send)
                        print(f"    Транзакція відправлена! TX HASH: {tx_hash}")
                    except Exception as e:
                        print(f"    Помилка при відправленні: {str(e)}")

                    if tx_count < TRANSACTIONS_PER_WALLET - 1:
                        print(f"    Чекаємо {TRANSACTION_TIMEOUT} с...")
                        time.sleep(TRANSACTION_TIMEOUT)
        else:
            print(f"Ціна газу >= {GAS_PRICE_THRESHOLD_GWEI} Gwei. Пропускаємо транзакції.")

        # Таймаут між циклами (якщо не останній цикл)
        if cycle_index < NUM_CYCLES - 1:
            print(f"\nЗавершили цикл {cycle_index+1}. Чекаємо {CYCLE_TIMEOUT} с перед наступним циклом...")
            time.sleep(CYCLE_TIMEOUT)

    print("\nВсі цикли завершено!")

if __name__ == "__main__":
    main()