import random
import socket
import concurrent.futures
from datetime import datetime
import json
import time
import os
import subprocess
import platform
from typing import Tuple, Dict, List

def colored(text, color_code):
    return f"\033[{color_code}m{text}\033[0m"

def animated_banner():
    banner_lines = [
        "░██████╗░█████╗░░█████╗░███╗░░██╗███████╗██████╗░░██████╗░███████╗",
        "██╔════╝██╔══██╗██╔══██╗████╗░██║██╔════╝██╔══██╗██╔════╝░██╔════╝",
        "╚█████╗░██║░░╚═╝███████║██╔██╗██║█████╗░░██║░░██║██║░░██╗░█████╗░░",
        "░╚═══██╗██║░░██╗██╔══██║██║╚████║██╔══╝░░██║░░██║██║░░╚██╗██╔══╝░░",
        "██████╔╝╚█████╔╝██║░░██║██║░╚███║███████╗██████╔╝╚██████╔╝███████╗",
        "╚═════╝░░╚════╝░╚═╝░░╚═╝╚═╝░░╚══╝╚══════╝╚═════╝░░╚═════╝░╚══════╝",
        "",
        "█▄▄ █▄█   █▀▄ █▀▄ █▄░█ █▀▄ █▀█ █▀█",
        "█▄█ ░█░   █▄▀ █▄▀ █░▀█ █▄▀ █▄█ ▀▀█",
        ""
    ]
    for line in banner_lines:
        print(colored(line, "1;36"))
        time.sleep(0.08)

def is_private_ip(first: int, second: int) -> bool:
    if first == 10 or first == 127:
        return True
    if first == 169 and second == 254:
        return True
    if first == 172 and 16 <= second <= 31:
        return True
    if first == 192 and second == 168:
        return True
    if 224 <= first <= 255:
        return True
    return False

def generate_random_ip() -> str:
    while True:
        first = random.randint(1, 223)
        second = random.randint(0, 255)
        if not is_private_ip(first, second):
            break
    third = random.randint(0, 255)
    fourth = random.randint(1, 254)
    return f"{first}.{second}.{third}.{fourth}"

def scan_port(ip: str, port: int, timeout: float = 1.0) -> Tuple[str, int, bool]:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return ip, port, s.connect_ex((ip, port)) == 0
    except (socket.timeout, socket.error):
        return ip, port, False

def save_results_json(filename: str, working_ips: Dict[str, List[int]], ports: List[int], num_ips: int, timeout: float):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {
        "timestamp": timestamp,
        "num_ips_scanned": num_ips,
        "ports": ports,
        "timeout_sec": timeout,
        "working_ips": working_ips,
        "working_ips_count": len(working_ips),
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def open_file_crossplatform(path: str):
    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(path)
        elif system == "Darwin":
            subprocess.run(["open", path])
        elif system == "Linux":
            subprocess.run(["xdg-open", path])
        else:
            print("Неизвестная ОС: файл не может быть открыт автоматически.")
    except Exception as e:
        print(colored(f"Не удалось открыть файл: {e}", "1;31"))

def main():
    animated_banner()
    print(colored("Scan Edge — сканер публичных IP и портов (для обучения)\n", "1;36"))

    try:
        unlimited = False
        while True:
            raw_input = input("Сколько IP-адресов сгенерировать? (1-1000): ").strip()
            if raw_input.lower() == ".unl":
                unlimited = True
                print(colored("Код активирован — лимит снят!", "1;33"))
                time.sleep(1)
                break
            try:
                num_ips = int(raw_input)
                if 1 <= num_ips <= 1000:
                    break
                print("Введите число от 1 до 1000")
            except ValueError:
                print("Ошибка: введите целое число")

        if unlimited:
            while True:
                try:
                    num_ips = int(input("Сколько IP-адресов сгенерировать?: ").strip())
                    if num_ips >= 1:
                        break
                    print("Введите положительное число")
                except ValueError:
                    print("Ошибка: введите целое число")

        ports_input = input("Укажите порты (через запятую, например 80,443,22): ")
        ports = []
        for part in ports_input.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                port = int(part)
                if 1 <= port <= 65535:
                    ports.append(port)
                else:
                    print(f"Порт {port} вне диапазона (1-65535) и будет пропущен.")
            except ValueError:
                print(f"Неверный порт: {part}")

        ports = list(set(ports))  # удалить дубликаты

        if not ports:
            print("Не указано ни одного допустимого порта. Завершение.")
            return

        try:
            timeout = float(input("Таймаут подключения (сек, рекомендуемо 0.5–2): "))
        except ValueError:
            print("Некорректное значение, используется таймаут по умолчанию = 1.0")
            timeout = 1.0

        timeout = max(0.1, min(timeout, 5.0))

        print(f"\nГенерация {num_ips} IP и сканирование портов {ports}...\n")
        ips = [generate_random_ip() for _ in range(num_ips)]

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(scan_port, ip, port, timeout) for ip in ips for port in ports]

            for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
                ip, port, status = future.result()
                results.append((ip, port, status))
                if status:
                    print(colored(f"[ОТКРЫТ] {ip}:{port}", "1;32"))
                if i % 100 == 0 or i == len(futures):
                    print(f"Проверено {i}/{len(futures)} комбинаций...")

        working_ips: Dict[str, List[int]] = {}
        for ip, port, status in results:
            if status:
                working_ips.setdefault(ip, []).append(port)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"scan_results_{timestamp}.json"
        save_results_json(filename, working_ips, ports, num_ips, timeout)

        print("\nРезультаты:")
        print(f"Проверено: {num_ips} IP × {len(ports)} портов = {num_ips * len(ports):,} проверок")
        print(colored(f"Найдено рабочих IP: {len(working_ips)}", "1;32"))
        print(f"Файл с результатами: {filename}")

        print("\nОткрытие файла с результатами...")
        time.sleep(2)
        open_file_crossplatform(filename)

        print("\nПрограмма завершится через 5 секунд...")
        time.sleep(5)

    except KeyboardInterrupt:
        print("\nСканирование прервано пользователем.")
    except Exception as e:
        print(f"\nОшибка: {e}")

if __name__ == "__main__":
    main()
