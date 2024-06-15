from flask import Flask, request, render_template, url_for, send_file
import asyncio
import telebot
import os, shutil, zipfile, glob
from pathlib import Path
from help import run_cmd, absolute_paths
from help import check_url

BOT_API = os.environ['BOT_API']
secret = os.environ['SECRET']
url = 'https://mi-bot-oh1a.onrender.com'

miBot = telebot.TeleBot(BOT_API, threaded = False)
miBot.remove_webhook()
miBot.set_webhook(url=url)

app = Flask(__name__)
@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        miBot.process_new_updates([update])
        return 'ok', 200
    else:
        return 'Hello, World!'  # o cualquier otra respuesta para GET
        
@app.route('/files')
def list_files():
    files = os.listdir('.')
    files_with_links = []
    for file in files:
        file_path = os.path.join('.', file)
        os.path.isdir(file_path):
            files_with_links.append((file, url_for('navigate_folder', path=file)))
    return render_template('files.html', files=files_with_links, current_path='.')

@app.route('/files/<path:path>')
def navigate_folder(path):
    files = os.listdir(path)
    files_with_links = []
    for file in files:
        file_path = os.path.join(path, file)
        if os.path.isdir(file_path):
            files_with_links.append((file, url_for('navigate_folder', path=file_path)))
        else:
            files_with_links.append((file, url_for('serve_file', path=file_path)))
    return render_template('files.html', files=files_with_links, current_path=path)

if __name__ == '__main__':
    app.run(debug=True)
@miBot.message_handler(commands=["start"])
def cmd_start(message):
    miBot.reply_to(message, "Si funciona es la ostia")
@miBot.message_handler(commands=["enserio?"])
def cmd_enserio(message):
    miBot.reply_to(message, "Pos mira que si")


@miBot.message_handler(content_types=['text'])
def download(message):
   # if message.from_user.id!= Config.OWNER_ID: para que solo el due;o del miBot
    #    return
    url = message.text
    miBot.send_message(message.chat.id, "Hasta aqui")
    if check_url(url):
        pass
    else:
        miBot.send_message(message.chat.id, "No soportado")
        return
    miBot.send_message(message.chat.id, "Descargando...")
    asyncio.run(_pdf(message))

@miBot.message_handler(commands=["cleandir"])
def cmd_cleandir(message):
    dirx = './Manga/'
    if os.path.isdir(dirx):
        shutil.rmtree(dirx)
        miBot.reply_to(message,"Successfully cleaned your download dir, now you can sent another link")
    else:
        miBot.reply_to(message, "Your download dir are empty, use this command only if your miBot are stuck")


async def _pdf(message):
    miBot.reply_to(message, "Ya brinco")
    #await miBot.delete_message(update.chat.id, update1.id)
    #miBot.send_message(update.chat.id, "lo Lo borro")
    url = message.text
    reply_message = miBot.reply_to(message, url)
    manga_dir = './Manga/'
    if os.path.isdir(manga_dir):
       miBot.edit_message_text(chat_id=message.chat.id, message_id=reply_message.message_id, text="Still processing another manga")
       return
    os.mkdir(manga_dir)
    yoan = miBot.edit_message_text(chat_id=message.chat.id, message_id=reply_message.message_id, text='Downloading...')
    cmd = f'manga-py {url}'
    miBot.send_message(message.chat.id, cmd)
    result = await run_cmd(cmd)
    stdout, stderr, returncode, pid = result
    #messager = f"Salida estándar: {stdout}"
    print("El error es:", stderr, flush=True)
    miBot.send_message(message.chat.id, returncode, pid)
    count = 0
    d = manga_dir
    for file in glob.glob(f'{manga_dir}*/'):
        for path in os.listdir(file):
            if os.path.isfile(os.path.join(file, path)):
                count += 1
        if int(count) == 0:
            miBot.edit_message_text(chat_id=message.chat.id, message_id=yoan.message_id, text="Process Stopped. can't download manga url")
            shutil.rmtree(d)
            return
    for file in glob.glob(f'{manga_dir}*/'):
        file_dir = file[8:-1]
        p = Path('.')
        for f in p.glob(f'Manga/{file_dir}/*.zip'):
            with zipfile.ZipFile(f, 'r') as archive:
                archive.extractall(path=f'./Manga/{file_dir}/{f.stem}')
                os.remove(f'./Manga/{file_dir}/{f.stem}/info.txt')
                os.remove(f'./Manga/{file_dir}/{f.stem}.zip')
                cmd = f'dir2pdf --subdirs vol_(.*) Manga/{file_dir}/' + 'vol_{}.pdf' + f' Manga/{file_dir}/'
                await run_cmd(cmd)

        dldirs = [i async for i in absolute_paths(f'Manga/{file_dir}/')]
        dldirs.sort()
        for fls in dldirs:
            if os.path.exists(fls):
                try:
                    await miBot.send_chat_action(message.chat.id, 'upload_document')
                    await miBot.send_document(
                        message.chat.id,
                        fls,
                        caption=fls[-7:-4]
                    )
                    os.remove(fls)
                except Exception as e:
                    print(f"Error al enviar archivo: {e}")
        shutil.rmtree(manga_dir)
        await yoan.delete()























"""@miBot.message_handler(commands=['manga'])
def handle_manga(message):
    chat_id = message.chat.id
    statement = message.text.split()
    if len(statement) < 2:
        miBot.send_message(chat_id, "Invalid command")
        return
    chapter = statement[1]
    url = "https://mangapark.me/title/" + "+".join(statement[1:])
    try:
        miBot.send_message(chat_id, "Hasta aqui bien0")
        miBot.send_message(chat_id, url)
        reqq = requests.get(url, timeout=10)  # search for the manga
        miBot.send_message(chat_id, "Hasta aqui bien1")
        page = reqq.text
        soup = BeautifulSoup(page, 'html5lib')
        result = [a.attrs.get('href') for a in soup.select('a[href^="/title/"]')]  # scrape to the most relevant result
        if not result:
            miBot.send_message(chat_id, "No manga found.")
            return
        miBot.send_message(chat_id, "Hasta aqui bien buscado")
        url = "http://mangapark.me" + result[1]
        reqq = requests.get(url)
        page = reqq.text
        soup = BeautifulSoup(page, 'html5lib')
        result = [a.attrs.get('href') for a in soup.select('span > a[href*=/c' + chapter + '/]')]  # scrape to the designated chapter
        if not result:
            miBot.send_message(chat_id, "No chapter found.")
            return
        url = "http://mangapark.me" + result[1]
        url = url.replace("/1", "")
        reqq = requests.get(url)
        page = reqq.text
        soup = BeautifulSoup(page, 'html5lib')
        result = [a.attrs.get('src') for a in soup.select('a > img[src*=.jpg]')]
        for i, img_url in enumerate(result):
            urllib.urlretrieve(img_url, f"./app/manga/{i}.jpg")  # download the needed images to the server (or locally)
        shutil.make_archive(f"./app/chapter{chapter}", "zip", "./app/manga")  # create a zip file containing all the images
        zipfile = f"./app/chapter{chapter}.zip"
        miBot.send_document(chat_id, document=open(zipfile, 'rb'))  # send the zipfile

    except Exception as e:
        miBot.send_message(chat_id, "Error: " + str(e))

    # empty the manga directory once zipped and sent
    folder = '/app/manga'
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)
    os.unlink(zipfile)
"""
