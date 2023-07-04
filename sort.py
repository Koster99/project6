import sys
from pathlib import Path
from transliterate import translit
import glob
import os
import shutil
from collections import defaultdict
import zipfile
import tarfile
import gzip
import re


def main():
    # Перевірка, чи був введений шлях як аргумент командного рядка
    if len(sys.argv) < 2:
        print("Please provide a path.")
        return

    # Отримання введеного шляху
    user_input = sys.argv[1]
    path = Path(user_input)

    # Перевірка, чи існує вказаний шлях
    if not path.exists():
        print(f'{path.absolute()} does not exist')
        return

    # Перевірка, чи вказаний шлях є каталогом
    if path.is_dir():
        # Якщо шлях - каталог, вивести всі елементи в каталозі
        items = path.iterdir()
        for item in items:
            print(item)
    else:
        # Якщо шлях - файл, вивести повідомлення
        print(f'{path} is a file')

    # Список розширень файлів, які треба знайти і перейменувати
    extensions = [
        'mp4', 'avi', 'mov', 'mkv',
        'mp3', 'ogg', 'wav', 'amr',
        'docx', 'txt', 'pdf', 'doc', 'xlsx', 'pptx',
        'png', 'jpeg', 'jpg', 'scg',
        'zip', 'gz', 'tar'
    ]
    find_file(path, extensions)
    delete_folder(path)


def find_file(path, extensions):
    files = []
    for extension in extensions:
        # Формування шаблону для пошуку файлів з певним розширенням
        pattern = str(path / '**' / f'*.{extension}')
        # Знаходження файлів, що відповідають шаблону
        files.extend(glob.glob(pattern, recursive=True))

    # Створення словника для збереження списку файлів для кожного розширення
    file_dict = defaultdict(list)

    for file in files:
        # Отримання шляху файлу
        file_path = Path(file)
        # Перевірка, чи файл є архівом
        if file_path.suffix in ['.zip', '.gz', '.tar']:
            # Розпакування архіву та перенесення відповідного вмісту
            extract_archive(file_path, path)
            continue

        # Перейменування файлу, використовуючи функцію normalize()
        new_name = normalize(file_path.stem)
        new_path = file_path.with_name(new_name).with_suffix(file_path.suffix)
        os.rename(file_path, new_path)
        # Додавання файлу до списку для відповідного розширення
        if file_path.suffix[1:] in extensions:
            file_dict[file_path.suffix[1:]].append(new_path)
        else:
            other_folder = path / "Others"
            if not other_folder.is_dir():
                other_folder.mkdir()
            new_file_path = other_folder / file_path.name
            os.rename(new_path, new_file_path)
            file_dict["Others"].append(new_file_path)

    for extension, file_list in file_dict.items():
        # Вибір назви папки за розширенням
        folder_name = get_folder_name(extension)
        # Формування шляху до папки
        folder_path = path / folder_name
        # Перевірка, чи папка існує, якщо ні - створення папки
        if not folder_path.is_dir():
            folder_path.mkdir()

        for file_path in file_list:
            # Формування нового шляху для переміщення файлу
            new_file_path = folder_path / file_path.name
            # Перевірка, чи файл вже знаходиться в папці
            if file_path != new_file_path:
                # Переміщення файлу
                os.rename(file_path, new_file_path)

    return files


def normalize(string):
    # Транслітерація і нормалізація назви файлу
    translate_string = translit(string, 'uk', reversed=True)
    translate_string = re.sub(r'[^A-Za-z0-9.-]+', '_', translate_string)

    return translate_string


def extract_archive(file_path, target_dir):
    # Отримання шляху до папки "archives"
    archives_dir = target_dir / "archives"

    # Перевірка, чи папка "archives" існує, якщо ні - створення папки
    if not archives_dir.is_dir():
        archives_dir.mkdir()

    # Визначення розширення архіву
    extension = file_path.suffix

    # Створення папки для вмісту архіву
    archive_name = normalize(file_path.stem)
    extract_dir = archives_dir / archive_name
    if not extract_dir.is_dir():
        extract_dir.mkdir()

    # Розпакування архіву в папку
    if extension == '.zip':
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
    elif extension == '.gz':
        with gzip.open(file_path, 'rb') as gz_ref:
            with open(extract_dir / file_path.stem, 'wb') as out_file:
                shutil.copyfileobj(gz_ref, out_file)
    elif extension == '.tar':
        with tarfile.open(file_path, 'r') as tar_ref:
            tar_ref.extractall(extract_dir)

    # Видалення архіву
    os.remove(file_path)

    return extract_dir


def get_folder_name(file_extension):
    # Словник, що відповідає розширенням файлів назвами папок
    folder_names = {
        'mp4': 'Videos', 'avi': 'Videos', 'mov': 'Videos', 'mkv': 'Videos',
        'mp3': 'Music', 'ogg': 'Music', 'wav': 'Music', 'amr': 'Music',
        'docx': 'Documents', 'txt': 'Documents', 'doc': 'Documents', 'pdf': 'Documents', 'xlsx': 'Documents',
        'pptx': 'Documents',
        'png': 'Images', 'jpeg': 'Images', 'jpg': 'Images', 'svg': 'Images',
        'zip': 'Archives', 'gz': 'Archives', 'tar': 'Archives',
    }
        
    # Повернення назви папки за розширенням файлу
    return folder_names.get(file_extension)


def delete_folder(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for folder in dirs:
            folder_path = os.path.join(root, folder)
            if len(os.listdir(folder_path)) == 0:
                # Видалення папки, якщо вона пуста
                shutil.rmtree(folder_path)
                print(f'Папку {folder_path} видалено')
            else:
                print(f'Папка {folder_path} не пуста')


if __name__ == '__main__':
    main()
