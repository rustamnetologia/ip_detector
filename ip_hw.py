import requests
from pprint import pprint
import json
import ipinfo
import os
from dotenv import load_dotenv

load_dotenv()
yandex_token = os.getenv('YANDEX_DISK_TOKEN')
if not yandex_token:
    print("Токен не найден в .env !")
    
    
else:
    print(f"Токен загружен: {yandex_token[:10]}...")


class IPAdress:
    def __init__(self):
        self.ip = None
        self.info = None

    def get_ip(self):
        url = 'https://api.ipify.org'
        response = requests.get(url)
        if response.status_code == 200:
            self.ip = response.text
            return self.ip
        else:
            return f'Не удалось получить IP. Статус-код: {response.status_code}'

    def get_info(self):
        target_ip = self.ip
        handler = ipinfo.getHandler()
        self.info = handler.getDetails(target_ip)
        return self.info

    def show_info(self):
        if self.info is None:
            return None
        data = self.get_info_dict()
        print("\n" + "=" * 60)
        print(f"ИНФОРМАЦИЯ ОБ IP: {data['ip']}")
        print("=" * 60)
        for key, value in data.items():
            print(f"{key.capitalize()}: {value or 'Неизвестно'}")
        print("=" * 60 + "\n")
        return data

    def get_info_dict(self):
        if self.info is None:
            return None
        return {
            'ip': self.info.ip,
            'country': self.info.country,
            'city': self.info.city,
            'region': self.info.region,
            'org': self.info.org,
            'loc': self.info.loc,
            'timezone': self.info.timezone,
            'postal': self.info.postal
        }


class YandexDisk:
    def __init__(self, token):
        self.token = token
        self.base_url = 'https://cloud-api.yandex.net/v1/'
        self.headers = {
            'Authorization': f'OAuth {self.token}',
            'Content-Type': 'application/json'
        }
        print(" Яндекс.Диск инициализирован")

    def create_folder(self, folder_name):
        url = self.base_url + 'disk/resources'
        params = {'path': folder_name}
        response = requests.put(url, params=params, headers=self.headers)
        if response.status_code == 201:
            print(f' Папка "{folder_name}" создана')
            return True
        elif response.status_code == 409:
            print(f'Папка "{folder_name}" уже существует')
            return True
        else:
            print(f'Ошибка создания папки: {response.status_code}')
            return False

    def save_file_to_json(self, data, file_name):
        if not file_name.endswith('.json'):
            file_name = f'{file_name}.json'
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f' Файл "{file_name}" создан локально')
        return file_name

    def delete_file(self, file_name):
        if not file_name.endswith('.json'):
            file_name = f'{file_name}.json'
        full_path = os.path.abspath(file_name)
        print(f"🔍 Ищу файл: {full_path}")

        if os.path.exists(full_path):
            os.remove(full_path)
            print(f' Файл "{file_name}" удален')
            return True
        else:
            print(f' Файл "{file_name}" не найден')
            return False

    def upload_file_on_yandex_disk(self, folder_name, file_name, data):
        if not self.create_folder(folder_name):
            return False

        if not file_name.endswith('.json'):
            file_name = f'{file_name}.json'

        remote_path = f'{folder_name}/{file_name}'

        url = f'{self.base_url}disk/resources/upload'
        params = {
            'path': remote_path,
            'overwrite': 'true'
        }
        response = requests.get(url, params=params, headers=self.headers)

        if response.status_code != 200:
            print('❌ Ошибка получения ссылки на загрузку')
            return False

        upload_url = response.json()['href']
        print('✅ Ссылка на загрузку получена!')

        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        upload_response = requests.put(
            upload_url,
            data=json_data,
            headers={'Content-Type': 'application/json'}
        )

        if upload_response.status_code == 201:
            print(f"✅ Файл '{remote_path}' загружен на Яндекс.Диск!")
            self.delete_file(file_name)
            return True
        else:
            print(f'❌ Ошибка загрузки: {upload_response.status_code}')
            return False


def main():
    """Основная функция программы"""
    
    print("=" * 60 + "\n")

    my_ip = IPAdress()
    my_ip.get_ip()
    my_ip.get_info()

    data = my_ip.get_info_dict()
    if not data:
        print("❌ Не удалось получить данные об IP")
        return

    my_ip.show_info()

    disk = YandexDisk(yandex_token)

    folder_name = 'IP_Info'
    file_name = f'ip_{my_ip.ip}'

    disk.save_file_to_json(data, file_name)
    result = disk.upload_file_on_yandex_disk(folder_name, file_name, data)

    if result:
        print("\n" + "=" * 60)
        print("✅ Программа завершена успешно!")
        print(f"📁 Файл загружен в папку '{folder_name}' на Яндекс.Диске")
        print("=" * 60 + "\n")
    else:
        print("\n❌ Ошибка при загрузке на Яндекс.Диск")


if __name__ == '__main__':
    main()
