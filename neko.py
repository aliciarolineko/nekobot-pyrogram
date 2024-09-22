import os
from pyrogram import Client, filters
import zipfile
import shutil
import random
import string
import smtplib
from email.message import EmailMessage
from pyrogram import Client, filters
import requests
from bs4 import BeautifulSoup
import re

# Configuracion del bot
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('TOKEN')

# Administradores y Usuarios del bot
admin_users = list(map(int, os.getenv('ADMINS').split(',')))
users = list(map(int, os.getenv('USERS').split(',')))
temp_users = []
temp_chats = []
ban_users = []
allowed_users = admin_users + users + temp_users + temp_chats

app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

compression_size = 10  # Tamaño de compresión por defecto en MB

bot_in_use = False

user_emails = {}
image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp']

#def compressfile(file_path, part_size):
    #parts = []
    #with open(file_path, 'rb') as f:
        #part_num = 1
        #while True:
            #part_data = f.read(part_size * 1024 * 1024)
            #if not part_data:
                #break
            #part_file = f"{file_path}.part{part_num}"
            #with open(part_file, 'wb') as part:
                #part.write(part_data)
            #parts.append(part_file)
            #part_num += 1
    #return parts

def compressfile(file_path, part_size):
    parts = []
    with open(file_path, 'rb') as f:
        part_num = 1
        while True:
            part_data = f.read(part_size * 1024 * 1024)
            if not part_data:
                break
            part_file = f"{file_path}.7z.{part_num:03d}"
            with open(part_file, 'wb') as part:
                part.write(part_data)
            parts.append(part_file)
            part_num += 1
    return parts
    

user_comp = {}

@app.on_message(filters.text)
async def handle_message(client, message):
    text = message.text
    username = message.from_user.username
    chat_id = message.chat.id
    user_id = message.from_user.id

    if chat_id not in allowed_users or user_id in ban_users:
        return

    if message.text.startswith(('start', '.start', '/start')):
        await message.reply("Funcionando")
    elif message.text.startswith('/adduser'):
        if user_id in admin_users:
            new_user_id = int(message.text.split()[1])
            temp_users.append(new_user_id)
            allowed_users.append(new_user_id)
            await message.reply(f"Usuario {new_user_id} añadido temporalmente.")
        else:
            await message.reply("No eres admin")
    elif message.text.startswith('/remuser'):
        if user_id in admin_users:
            rem_user_id = int(message.text.split()[1])
            if rem_user_id in temp_users:
                temp_users.remove(rem_user_id)
                allowed_users.remove(rem_user_id)
                await message.reply(f"Usuario {rem_user_id} eliminado temporalmente.")
            else:
                await message.reply("Usuario no encontrado en la lista temporal.")
        else:
            await message.reply("No eres admin")
    elif message.text.startswith('/addchat'):
        if user_id in admin_users:
            temp_chats.append(chat_id)
            allowed_users.append(chat_id)
            await message.reply(f"Chat {chat_id} añadido temporalmente.")
        else:
            await message.reply("No eres admin")
    elif message.text.startswith('/remchat'):
        if user_id in admin_users:
            if chat_id in temp_chats:
                temp_chats.remove(chat_id)
                allowed_users.remove(chat_id)
                await message.reply(f"Chat {chat_id} eliminado temporalmente.")
            else:
                await message.reply("Chat no encontrado en la lista temporal.")
        else:
            await message.reply("No eres admin")
    elif message.text.startswith('/banuser'):
        if user_id in admin_users:
            ban_user_id = int(message.text.split()[1])
            if ban_user_id not in admin_users:
                ban_users.append(ban_user_id)
                await message.reply(f"Usuario {ban_user_id} baneado.")
        else:
            message.reply("No eres admin")
    elif message.text.startswith('/debanuser'):
        if user_id in admin_users:
            deban_user_id = int(message.text.split()[1])
            if deban_user_id in ban_users:
                ban_users.remove(deban_user_id)
                await message.reply(f"Usuario {deban_user_id} desbaneado.")
            else:
                await message.reply("Usuario no encontrado en la lista de baneados.")
        else:
            await message.reply("No eres admin")
    elif message.text.startswith("/compress") and message.reply_to_message and message.reply_to_message.document:
        global bot_in_use
        if bot_in_use:
            await message.reply("El comando está en uso actualmente, espere un poco")
            return
        try:
            bot_in_use = True
            os.system("rm -rf ./server/*")
            await message.reply("Descargando el archivo para comprimirlo...")

            # Descargar archivo
            #file_path = await client.download_media(message.reply_to_message, file_name="server")
            #file_path = await client.download_media(message.reply_to_message, file_name=os.path.basename(message.reply_to_message.document.file_name)[:72])
            #file_path = await client.download_media(message.reply_to_message, file_name=(os.path.basename(message.reply_to_message.document.file_name)[:60] if message.reply_to_message.document.file_name else f"{''.join(random.choices(string.ascii_letters + string.digits, k=20))}"))    
            file_name = (
                os.path.basename(message.reply_to_message.document.file_name)[:60]
                if message.reply_to_message.document.file_name
                else  ''.join(random.choices(string.ascii_letters + string.digits, k=20))
            )
            file_path = await client.download_media(
                message.reply_to_message,
                file_name=file_name
            )
                
                
                
            await message.reply("Comprimiendo el archivo...")

            sizd = user_comp.get(username, 10)

            # Comprimir archivo
            parts = compressfile(file_path, sizd)
            await message.reply("Se ha comprimido el archivo, ahora se enviarán las partes")

            # Enviar partes
            for part in parts:
                try:
                    await client.send_document(message.chat.id, part)
                except:
                    pass

            await message.reply("Esas son todas las partes")
            shutil.rmtree('server')
            os.mkdir('server')

            bot_in_use = False
        except Exception as e:
            await message.reply(f'Error: {str(e)}')
        finally:
            bot_in_use = False
    elif text.startswith("/setsize"):
        valor = text.split(" ")[1]
        user_comp[username] = int(valor)
        await message.reply(f"Tamaño de archivos {valor}MB registrado para el usuario @{username}")
    elif text.startswith('/setmail'):
        email = text.split(' ', 1)[1]
        user_emails[user_id] = email
        await message.reply("Correo electrónico registrado correctamente.")

    elif text.startswith('/sendmail'):
        if user_id not in user_emails:
            await message.reply("No has registrado ningún correo, usa /setmail para hacerlo.")
            return

        email = user_emails[user_id]
        if message.reply_to_message:
            msg = EmailMessage()
            msg['Subject'] = 'Mensaje de Telegram'
            msg['From'] = os.getenv('DISMAIL')
            msg['To'] = email

            if message.reply_to_message.text:
                msg.set_content(message.reply_to_message.text)
            elif message.reply_to_message.media:
                media = await client.download_media(message.reply_to_message, file_name='mailtemp/')
                if os.path.getsize(media) < 59 * 1024 * 1024:  # 59 MB
                    with open(media, 'rb') as f:
                        msg.add_attachment(f.read(), maintype='application', subtype='octet-stream', filename=os.path.basename(media))
                else:
                    await message.reply("El archivo supera el límite de lo permitido (59 MB).")
                    return

            try:
                with smtplib.SMTP('disroot.org', 587) as server:
                    server.starttls()
                    server.login(os.getenv('DISMAIL'), os.getenv('DISPASS'))
                    server.send_message(msg)
                await message.reply("Correo electrónico enviado correctamente.")
            except Exception as e:
                await message.reply(f"Error al enviar el correo: {e}")
            finally:
                shutil.rmtree('mailtemp')
                os.mkdir('mailtemp')
    elif text.startswith('/rename'):
        if bot_in_use:
            await message.reply("El bot está en uso, espere un poco")
            return

        bot_in_use = True

        if not message.reply_to_message or not message.reply_to_message.media:
            await message.reply("Debe usar el comando respondiendo a un archivo")
            bot_in_use = False
            return

        command = text.split()
        if len(command) < 2:
            await message.reply("Introduzca un nuevo nombre")
            bot_in_use = False
            return

        new_name = command[1]
        media = message.reply_to_message

        # Determinar el tipo de medio y obtener el file_id correspondiente
        if media.photo:
            file_id = media.photo.file_id
        elif media.video:
            file_id = media.video.file_id
        elif media.document:
            file_id = media.document.file_id
        elif media.audio:
            file_id = media.audio.file_id
        else:
            await message.reply("Tipo de archivo no soportado")
            bot_in_use = False
            return

        # Descargar el archivo
        file_path = await client.download_media(file_id, file_name=f"temprename/{file_id}")

        # Obtener la extensión del archivo original
        file_extension = os.path.splitext(file_path)[1]

        # Crear el nuevo nombre con la extensión original
        new_file_path = f"temprename/{new_name}{file_extension}"

        # Renombrar el archivo
        os.rename(file_path, new_file_path)

        # Enviar el archivo renombrado
        await client.send_document(message.chat.id, new_file_path)

        # Limpiar la variable de estado
        bot_in_use = False

        # Eliminar el archivo temporal
        os.remove(new_file_path)
        shutil.rmtree('temprename')
        os.mkdir('temprename')
    elif message.text.startswith("/covernh") or message.text.startswith(".covernh"):
        bot_in_use = True
        sender = message.from_user
        username = sender.id
        codes = [clean_string(code.strip()) for code in message.text.split()[1].split(',')]

        if not codes:
            await message.reply("No puedes enviar el comando vacío")
            bot_in_use = False
            return

        for code in codes:
            # Check the first page to get the name
            url = f"https://nhentai.net/g/{code}/"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                await message.reply(f"El código {code} es erróneo: {str(e)}")
                continue

            soup = BeautifulSoup(response.content, 'html.parser')
            title_tag = soup.find('title')
            if title_tag:
                page_name = clean_string(title_tag.text.strip())
            else:
                page_name = clean_string(code) + code

            # Find the first image
            img_url = f"https://nhentai.net/g/{code}/1/"
            try:
                response = requests.get(img_url, headers=headers)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                await message.reply(f"Error al acceder a la página de la imagen: {str(e)}")
                continue

            soup = BeautifulSoup(response.content, 'html.parser')
            img_tag = soup.find('img', {'src': re.compile(r'.*\.(png|jpg|jpeg|gif|bmp|webp)$')})
            if img_tag:
                img_url = img_tag['src']
                img_extension = os.path.splitext(img_url)[1]
                img_data = requests.get(img_url, headers=headers).content

                img_filename = f"1{img_extension}"
                with open(img_filename, 'wb') as img_file:
                    img_file.write(img_data)

                await client.send_photo(message.chat.id, img_filename, caption=f"{code} {page_name}")
            else:
                await message.reply(f"No se encontró ninguna imagen para el código {code}")

        bot_in_use = False
        
    elif message.text.startswith("/cover3h") or message.text.startswith(".cover3h"):
        bot_in_use = True
        sender = message.from_user
        username = sender.id
        codes = [clean_string(code.strip()) for code in message.text.split()[1].split(',')]

        if not codes:
            await message.reply("No puedes enviar el comando vacío")
            bot_in_use = False
            return

        for code in codes:
            # Check the first page to get the name
            url = f"https://es.3hentai.net/d/{code}/"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                await message.reply(f"El código {code} es erróneo: {str(e)}")
                continue

            soup = BeautifulSoup(response.content, 'html.parser')
            title_tag = soup.find('title')
            if title_tag:
                page_name = clean_string(title_tag.text.strip())
            else:
                page_name = clean_string(code) + code

            # Find the first image
            img_url = f"https://es.3hentai.net/d/{code}/1/"
            try:
                response = requests.get(img_url, headers=headers)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                await message.reply(f"Error al acceder a la página de la imagen: {str(e)}")
                continue

            soup = BeautifulSoup(response.content, 'html.parser')
            img_tag = soup.find('img', {'src': re.compile(r'.*\.(png|jpg|jpeg|gif|bmp|webp)$')})
            if img_tag:
                img_url = img_tag['src']
                img_extension = os.path.splitext(img_url)[1]
                img_data = requests.get(img_url, headers=headers).content

                img_filename = f"1{img_extension}"
                with open(img_filename, 'wb') as img_file:
                    img_file.write(img_data)

                await client.send_photo(message.chat.id, img_filename, caption=f"{code} {page_name}")
            else:
                await message.reply(f"No se encontró ninguna imagen para el código {code}")

        bot_in_use = False

    elif message.text.startswith("/nh"):
    async def download_images(event):
        global bot_in_use
        if bot_in_use:
            await event.reply("El comando está en uso actualmente, espere un poco")
            return

        bot_in_use = True
        sender = await event.get_sender()
        username = sender.id
        codes = event.pattern_match.group(1).split(',')

        if not codes:
            await event.reply("No puedes enviar el comando vacío")
            bot_in_use = False
            return

        total_codes = len(codes)
        for index, code in enumerate(codes, start=1):
            code = clean_string(code.strip())

            # Check the first page to get the name
            url = f"https://nhentai.net/g/{code}/"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                await event.reply(f"El código {code} es erróneo: {str(e)}")
                continue

            soup = BeautifulSoup(response.content, 'html.parser')
            title_tag = soup.find('title')
            if title_tag:
                folder_name = os.path.join("h3dl", clean_string(title_tag.text.strip()))
            else:
                folder_name = os.path.join("h3dl", clean_string(code))

            os.makedirs(folder_name, exist_ok=True)

            # Now proceed to download images
            page_number = 1
            images_downloaded = 0

            while True:
                url = f"https://nhentai.net/g/{code}/{page_number}/"
                try:
                    response = requests.get(url, headers=headers)
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    if page_number == 1:
                        await event.reply(f"Error al acceder a la página: {str(e)}")
                    break

                soup = BeautifulSoup(response.content, 'html.parser')
                img_tag = soup.find('img', {'src': re.compile(r'.*\.(png|jpg|jpeg|gif|bmp|webp)$')})
                if not img_tag:
                    break

                img_url = img_tag['src']
                img_extension = os.path.splitext(img_url)[1]
                img_data = requests.get(img_url, headers=headers).content

                img_filename = os.path.join(folder_name, f"{page_number}{img_extension}")
                with open(img_filename, 'wb') as img_file:
                    img_file.write(img_data)

                images_downloaded += 1
                page_number += 1

            if images_downloaded == 0:
                await event.reply(f"No se encontraron imágenes para el código {code}")
                continue

            zip_filename = os.path.join(f"{folder_name}.cbz")
            with zipfile.ZipFile(zip_filename, 'w') as zipf:
                for root, _, files in os.walk(folder_name):
                    for file in files:
                        zipf.write(os.path.join(root, file), arcname=os.path.join(os.path.basename(root), file))

            await client.send_file(event.chat_id, zip_filename)
            await event.reply(f"Archivo {code} descargado, enviando...")

        await event.reply("Todos los archivos CBZ han sido enviados correctamente")
        shutil.rmtree('h3dl')
        os.mkdir('h3dl')
        bot_in_use = False

    def clean_string(s):
        return re.sub(r'[^a-zA-Z0-9\[\]]+', '', s)





    elif message.text.startswith("/3h"):
    async def download_images(event):
        global bot_in_use
        if bot_in_use:
            await event.reply("El comando está en uso actualmente, espere un poco")
            return

        bot_in_use = True
        sender = await event.get_sender()
        username = sender.id
        codes = event.pattern_match.group(1).split(',')

        if not codes:
            await event.reply("No puedes enviar el comando vacío")
            bot_in_use = False
            return

        total_codes = len(codes)
        for index, code in enumerate(codes, start=1):
            code = clean_string(code.strip())

            # Check the first page to get the name
            url = f"https://es.3hentai.net/d/{code}/"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                await event.reply(f"El código {code} es erróneo: {str(e)}")
                continue

            soup = BeautifulSoup(response.content, 'html.parser')
            title_tag = soup.find('title')
            if title_tag:
                folder_name = os.path.join("h3dl", clean_string(title_tag.text.strip()))
            else:
                folder_name = os.path.join("h3dl", clean_string(code))

            os.makedirs(folder_name, exist_ok=True)

            # Now proceed to download images
            page_number = 1
            images_downloaded = 0

            while True:
                url = f"https://es.3hentai.net/d/{code}/{page_number}/"
                try:
                    response = requests.get(url, headers=headers)
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    if page_number == 1:
                        await event.reply(f"Error al acceder a la página: {str(e)}")
                    break

                soup = BeautifulSoup(response.content, 'html.parser')
                img_tag = soup.find('img', {'src': re.compile(r'.*\.(png|jpg|jpeg|gif|bmp|webp)$')})
                if not img_tag:
                    break

                img_url = img_tag['src']
                img_extension = os.path.splitext(img_url)[1]
                img_data = requests.get(img_url, headers=headers).content

                img_filename = os.path.join(folder_name, f"{page_number}{img_extension}")
                with open(img_filename, 'wb') as img_file:
                    img_file.write(img_data)

                images_downloaded += 1
                page_number += 1

            if images_downloaded == 0:
                await event.reply(f"No se encontraron imágenes para el código {code}")
                continue

            zip_filename = os.path.join(f"{folder_name}.cbz")
            with zipfile.ZipFile(zip_filename, 'w') as zipf:
                for root, _, files in os.walk(folder_name):
                    for file in files:
                        zipf.write(os.path.join(root, file), arcname=os.path.join(os.path.basename(root), file))

            await client.send_file(event.chat_id, zip_filename)
            await event.reply(f"Archivo {code} descargado, enviando...")

        await event.reply("Todos los archivos CBZ han sido enviados correctamente")
        shutil.rmtree('h3dl')
        os.mkdir('h3dl')
        bot_in_use = False

    def clean_string(s):
        return re.sub(r'[^a-zA-Z0-9\[\]]+', '', s)
    
        
def clean_string(s):
    return re.sub(r'[^a-zA-Z0-9\[\] ]', '', s)
        




app.run()
    
