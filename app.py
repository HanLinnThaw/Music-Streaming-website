from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
import sqlite3 , bcrypt, pygame
from pygame import mixer
from mutagen.mp3 import MP3
import time
from datetime import datetime
import traceback
from werkzeug.utils import secure_filename
import os
import threading
import queue
from flask_session import Session


pygame.mixer.init()

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key ="Han Linn Thaw"
    
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'jfif'}
File_Allow_Extensions = {'mp3'}

def allowed_audio_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in File_Allow_Extensions

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
           
upload_folder = os.path.join('static','upload_photo')
app.config['upload_photo']= upload_folder

upload_folder = os.path.join('static','upload_mp3')
app.config['upload_mp3']= upload_folder


@app.route('/login', methods=['GET', 'POST'])
@app.route('/')
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        email = request.form.get('email')
        passw = request.form.get('password')
        print(passw)
        try:
            connection = sqlite3.connect("music.db")
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute("select * from usertable where Email=?",(email,))
            userlist = cursor.fetchone()
            if not userlist:
                flash("Email and Password are not correct", "danger")
                return redirect(url_for('login'))
            user_password = userlist['Password']
            check_password = bcrypt.checkpw(passw.encode(), user_password)
            if not check_password:
                flash("Email and Password are not correct","danger")
                return redirect(url_for('login'))
            else:
                user_permission = userlist['Permission']
                if user_permission == 'User':
                    session['username'] = userlist['UserName']
                    session['email'] = userlist['Email']
                    session['password'] = userlist['Password']
                    session['role'] = userlist['Permission']
                    exit_event.clear()

                    return redirect(url_for('home'))
                elif user_permission == 'Admin':
                    session['username'] = userlist['UserName']
                    session['email'] = userlist['Email']
                    session['password'] = userlist['Password']
                    session['role'] = userlist['Permission']
                    return redirect(url_for('dashboard'))
     
        except Exception as e:
            flash(f"Error occurs {e}")
            return render_template('login.html')
# I got idea to stop thread from SuperFastPython Website
# https://superfastpython.com/stop-a-thread-in-python/#:~:text=Event%20can%20be%20checked%20via%20the%20is_set()%20function.&text=The%20main%20thread%2C%20or%20another,via%20the%20set()%20function.&text=Now%20that%20we%20know%20how,look%20at%20some%20worked%20examples.
exit_event = threading.Event()
@app.route("/Logout")
def logout():
    exit_event.is_set()
    exit_event.set()
    mixer.music.stop()
    session.pop('username')
    session.pop('email')
    session.pop('role')
    session.pop('password')
    if session_data:
        session_data.pop('song_index')
        session_data.pop('SongID')
        session_data.pop('duration')
        session_data.pop('songname')
        session_data.clear()
    session.clear()
    return redirect(url_for('login'))

@app.route('/test')
def test():
    if session:
        username = session['username']
        email = session['email']
        password = session['password']
        role = session['role']
    return render_template('usernavbar.html', username= username, email =email, password = password, role = role)

@app.route('/profile')
def profile():
    if session:
        username = session['username']
        email = session['email']
        password = session['password']
        role = session['role']
    return render_template('test.html', username= username, email =email, password = password, role = role)

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/home')
def home():
    albumdict = {}
    albumphoto = {}
    albumnamedict = {}
    songnamedict = {}
    songdict = {}
    artistiddict = {}
    if session:
        connection = sqlite3.connect("music.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("select AlbumID, Count(*) as count from albumplaytable group by AlbumID order by count DESC")
        count = cursor.fetchall()
        for albumm in count:
            albumid = albumm['AlbumID']
            albummcount = albumm['count']
            cursor.execute("select * from albumtable where AlbumID=?",(albumid,))
            album = cursor.fetchone()
            ArtistID = album['ArtistID']
            artistiddict[albumid] = ArtistID
            AlbumPhoto = album['Photo']
            albumname = album['AlbumName']
            albumphoto[albumid] = AlbumPhoto
            albumnamedict[albumid] = albumname
            cursor.execute("select ArtistName from artisttable where ArtistID=?",(ArtistID,))
            artist = cursor.fetchone()
            ArtistName = artist['ArtistName']
            albumdict[albumid] = ArtistName
        cursor.execute("select SongID, Count(*) as count from playtable group by SongID order by count DESC")
        songcount = cursor.fetchall()
        for songs in songcount:
            SongID = songs['SongID']
            SongCount = songs['count']
            cursor.execute("select * from songtable where SongID=?",(SongID,))
            song = cursor.fetchone()
            songname = song['SongName']
            songnamedict[SongID] = songname
            songurl = song['SongUrl']
            duration, duration1 = get_duration(songurl)
            songdict[SongID] = duration
        cursor.execute("select * from artisttable")
        artistlist = cursor.fetchall()
        cursor.execute("select * from artisttypetable")
        artisttypelist = cursor.fetchall()
        username = session['username']
        email = session['email']
        role = session['role']
        if role == 'User':
            return render_template('userhome.html',username= username, email =email, count = count, albumphoto = albumphoto, albumdict = albumdict, albumnamedict = albumnamedict, songcount = songcount, songnamedict = songnamedict, songdict =songdict, artistlist = artistlist, artisttypelist = artisttypelist, artistiddict= artistiddict)
        else:
            return render_template('login.html')
    else:
        return render_template('userhome.html')

@app.route('/userartist')
def userartist():
    try:
        connection = sqlite3.connect("music.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("select * from artisttable")
        artistlist = cursor.fetchall()
        cursor.execute("select * from artisttypetable")
        artisttypelist = cursor.fetchall()
        searchdata = request.args.get('searchdata')
        if searchdata:
            cursor.execute("select * from artisttable where ArtistName like ?",(searchdata,))
            searchdata = cursor.fetchall()
        ArtistTypeID = request.args.get('ArtistTypeID')
        if ArtistTypeID:
            cursor.execute("select * from artisttable where ArtistTypeID=?",(ArtistTypeID,))
            artistlist1 = cursor.fetchall()
            return render_template("artstlist.html", artistlist = artistlist1, artisttypelist = artisttypelist, searchdata = searchdata)
        return render_template("artstlist.html", artistlist = artistlist, artisttypelist = artisttypelist, searchdata = searchdata)
    except Exception as e:
        print(type(e).__name__)
        print(traceback.format_exc())
        return "none"
    
@app.route('/artistby/<ArtistTypeID>')
def artistbyartisttype(ArtistTypeID):
    try:
        connection = sqlite3.connect("music.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        return redirect(url_for("userartist", ArtistTypeID = ArtistTypeID))
    except Exception as e:
        print(type(e).__name__)
        print(traceback.format_exc())
        return "none"

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')

@app.route('/eachartistlist/<ArtistID>')
def albumlistbyeachartist(ArtistID):
    try:
        songdurationdict = {}
        connection = sqlite3.connect("music.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("select * from artisttable where ArtistID=?",(ArtistID,))
        artist = cursor.fetchone()
        cursor.execute("select * from albumtable where ArtistID=?",(ArtistID,))
        albumlist = cursor.fetchall()
        cursor.execute("select * from songtable")
        songlist = cursor.fetchall()
        for song in songlist:
            songurl = song['SongUrl']
            duration, duration1 = get_duration(songurl)
            songdurationdict[song['SongID']] = duration
        searchdata = request.args.get('searchdata')
        if searchdata:
            cursor.execute("select * from albumtable where AlbumName like ?",(searchdata,))
            searchdata = cursor.fetchall()
        return render_template("eachartistlist.html", artist = artist, albumlist = albumlist, searchdata = searchdata, songlist = songlist, songdurationdict = songdurationdict)
    except Exception as e:
        print(type(e).__name__)
        print(traceback.format_exc())
        return "none"

@app.route('/userprofile')
def userprofile():
    try:
        connection = sqlite3.connect("music.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        if 'email' in session:
            email = session['email']
        cursor.execute('select * from usertable where email=?',(email,))
        usr = cursor.fetchone()
        return render_template('userprofile.html', usr = usr)
        
    except Exception as e:
        print(e)
        return f"{e}"

@app.route("/userprofileupdated/<UserID>", methods=["GET","POST"])
def userprofileupdated(UserID):
    exit_event.clear()
    connection = sqlite3.connect("music.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    if 'email' in session:
        email = session['email']
    cursor.execute('select * from usertable where email=?',(email,))
    usr = cursor.fetchone()
    if request.method == "GET":
        return render_template("userprofile.html", usr = usr)
    else:
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_pwd = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        try:
            connection = sqlite3.connect('music.db')
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute("select * from usertable where Email=?",(email,))
            existing_email = cursor.fetchone()
            if existing_email:
                flash(f"{email} is registered as user and cannot change to that email", "danger")
                return redirect(url_for("adminprofile", usr = username))
            if password == '':
                cursor.execute("update usertable set UserName=?, Email=? where UserID=?",(username, email, UserID))
                connection.commit()
            else:
                cursor.execute("update usertable set UserName=?, Email=?, Password=? where UserID=?",(username, email, hashed_pwd, UserID))
                connection.commit()
            flash(f"User ID {UserID} is successfully updated with {email}, {username}, {password} and login again","success")
            return redirect(url_for("login"))
        except Exception as e:
            print(traceback.format_exc())
            return "None" 

@app.route('/adminprofile')
def adminprofile():
    try:
        connection = sqlite3.connect("music.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        if 'email' in session:
            email = session['email']
        cursor.execute('select * from usertable where email=?',(email,))
        usr = cursor.fetchone()
        return render_template('adminprofile.html', usr= usr)
        
    except Exception as e:
        print(e)
        return f"{e}"

@app.route("/adminprofileupdated/<UserID>", methods=["GET","POST"])
def adminprofileupdated(UserID):
    connection = sqlite3.connect("music.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    if 'email' in session:
        email = session['email']
    cursor.execute('select * from usertable where email=?',(email,))
    usr = cursor.fetchone()
    if request.method == "GET":
        return render_template("adminprofile.html")
    else:
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_pwd = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        try:
            connection = sqlite3.connect('music.db')
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute("select * from usertable where Email=?",(email,))
            existing_email = cursor.fetchone()
            if existing_email:
                flash(f"{email} is registered as user and cannot change to that email", "danger")
                return redirect(url_for("adminprofile", usr = usr))
            if password == '':
                cursor.execute("update usertable set UserName=?, Email=? where UserID=?",(username, email, UserID))
                connection.commit()
            else:
                cursor.execute("update usertable set UserName=?, Email=?, Password=? where UserID=?",(username, email, hashed_pwd, UserID))
                connection.commit()
            flash(f"User ID {UserID} is successfully updated with {email}, {username}, {password} and login again","success")
            return redirect(url_for("login"))
        except Exception as e:
            print(traceback.format_exc())
            return "None"  


@app.route('/songlistbyalbum/<AlbumID>/<ArtistID>')
def songlistineachalbum(AlbumID, ArtistID):
    try:
        durat = {}
        connection = sqlite3.connect("music.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("select * from songtable where AlbumID=?",(AlbumID,))
        songlist = cursor.fetchall()
        for song in songlist:
            file = song['SongUrl']
            audio = MP3(file)
            duration = audio.info.length
            duration = time.strftime("%M:%S", time.gmtime(duration))
            durat[song['SongName']] = duration          
        cursor.execute("select * from albumtable where ArtistID=?",(ArtistID,))
        albumlist = cursor.fetchall()
        cursor.execute("select * from albumtable where AlbumID=?",(AlbumID,))
        album = cursor.fetchone()
        song = request.args.get('SongID')
        duration = request.args.get('duration')
        songalbumidlist = request.args.getlist('songalbumidlist')
        cursor.execute("select * from songtable where SongID=?",(song,))
        playsonglist = cursor.fetchone()
        if session:
            email = session['email']
        cursor.execute("select * from usertable where Email=?",(email,))
        user = cursor.fetchone()
        UserID = user['UserID']
        date = datetime.now()
        cursor.execute("insert into albumplaytable (UserID, AlbumID, DateTime) values (?,?,?)",(UserID, AlbumID, date))
        searchdata = request.args.get('searchdata')
        if searchdata:
            cursor.execute("select * from songtable where SongName like ?",(searchdata,))
            searchdata = cursor.fetchall()
        searchdata = request.args.get('searchdata')
        if searchdata:
            cursor.execute("select * from songtable where SongName like ?",(searchdata,))
            searchdata = cursor.fetchall()
        connection.commit()
        return render_template("songlistbyalbum.html", songlist = songlist, albumlist = albumlist, album = album, durat = durat, ArtistID = ArtistID, playsonglist = playsonglist, duration = duration, songalbumidlist = songalbumidlist, searchdata = searchdata)
    except Exception as e:
        print(type(e).__name__)
        print(traceback.format_exc())
        return "none"

def nextsong(song_url, song_index, songidlist, AlbumID, ArtistID):
    try:
        connection =sqlite3.connect("music.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        if session_data:
            song_index = session_data.get('song_index')
        new_index =(song_index+1) % len(songidlist)
        if new_index <= len(songidlist):
            SongID = songidlist[new_index]
        else:
            new_index = 0
            SongID = songidlist[new_index]
        cursor.execute("select SongName from songtable where SongID=?",(SongID,))
        songn = cursor.fetchone()
        songname = songn['SongName']
        cursor.execute("select SongUrl from songtable where SongID=?",(SongID,))
        song = cursor.fetchone()
        songurl = song["SongUrl"]
        return songurl, new_index, songidlist, AlbumID, ArtistID, SongID, songname
    except Exception as e:
        print(e)
        return "none"

session_action = {}
@app.route('/control', methods=['GET','POST'])
def control_music():
    data = request.json
    action = data.get('action')
    if action in ['pause', 'play']:
        session_action['action'] = action
        return jsonify({'status': 'Action received'}), 200

playmusic_data = queue.Queue()
current_data = queue.Queue()
thread = threading.Thread()
@app.route('/playmusic')
def playmusic(songurl, song_index, songidlist, AlbumID, ArtistID, SongID, songname):
        while not exit_event.is_set():
            is_paused = False
            try:
                if not mixer.music.get_busy():
                    duration, duration1 = get_duration(songurl)
                    # Getting Queue idea from the python assests
                    # And reuse that in the code 
                    # https://pythonassets.com/posts/how-to-return-from-a-thread/
                    playmusic_data.put((songurl, song_index, songidlist, AlbumID, ArtistID, SongID, duration, songname, duration1))
                    mixer.music.load(songurl)
                    mixer.music.play()
                while not exit_event.is_set():
                    position = pygame.mixer.music.get_pos() //1000
                    minute = position //60
                    second = position % 60
                    position1 = f"{minute:02}:{second:02}"
                    current_data.put((position, position1))
                    if session_action:
                        action = session_action['action']
                        if action == 'pause':
                            pygame.mixer.music.pause()
                            is_paused = True
                            session_action['action'] = None
                        elif action == 'play':
                            pygame.mixer.music.unpause()
                            is_paused = False
                            session_action['action'] = None
                    if not mixer.music.get_busy() and not is_paused:
                        data = nextsong(songurl,song_index, songidlist, AlbumID, ArtistID)
                        if data:
                            songurl, new_index, songidlist, AlbumID, ArtistID, SongID, songname = data
                            playmusic(songurl, new_index, songidlist, AlbumID, ArtistID, SongID, songname)
            except Exception as e:
                print(e)
                return {e}
            
def get_duration(songurl):
    audio = MP3(songurl)
    duration1 = audio.info.length
    duration = time.strftime("%M:%S", time.gmtime(duration1))
    return duration, duration1

@app.route('/killing_thread', methods=['POST'])
def killing_thread():
    action = request.form.get('action')
    if action == None:
        if thread.is_alive():
            exit_event.set()
            pygame.mixer.music.stop()
    return jsonify({'status': 'Music thread stopped'})
session_data = {}
@app.route("/play/<SongID>/<AlbumID>/<ArtistID>")
def play(SongID, AlbumID, ArtistID):
    session_data.clear()
    session_action.clear()
    songurllist = []
    songidlist = []
    global thread
    exit_event.set()
    pygame.mixer.music.stop()
    try:
        if session:
            email = session['email']
        connection =sqlite3.connect("music.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("select * from usertable where email=?",(email,))
        user = cursor.fetchone()
        UserID = user['UserID']
        cursor.execute("select SongName from songtable where SongID=?",(SongID,))
        song = cursor.fetchone()
        SongName = song['SongName']
        date = datetime.now()
        date = date.isoformat()
        cursor.execute("insert into playtable (UserID, SongID, SongName, DateTime) values (?,?,?,?)",(UserID, SongID, SongName, date))
        cursor.execute("select * from songtable")
        songl = cursor.fetchall()
        for song in songl:
            songurl = song['SongUrl']
            songurllist.append(songurl)
            songid = song['SongID']
            songidlist.append(songid)
        SongID = int(SongID)
        song_index = songidlist.index(SongID)
        cursor.execute("select * from songtable where SongID=?",(SongID,))
        song = cursor.fetchone()
        songurl = song['SongUrl']
        songname = song['SongName']
        duration = get_duration(songurl)  
        exit_event.clear()
        connection.commit()
        # Getting idea from Geeks for Geeks website
        # Use the idea and rewrite the threading based on the project
        # https://www.geeksforgeeks.org/multithreading-python-set-1/
        thread = threading.Thread(target=playmusic, args=(songurl,song_index, songidlist, AlbumID, ArtistID, SongID, songname))
        thread.start()
        return redirect(url_for("songlistineachalbum", SongID=SongID, AlbumID= AlbumID, ArtistID = ArtistID, duration = duration))  
    except Exception as e:
        print(e)
        return f"{e}"


def append_session():
    while not exit_event.is_set():
        while True:
            try:
                result = playmusic_data.get(timeout=1)
                if result:
                    songurl, song_index, songidlist, AlbumID, ArtistID, SongID, duration, songname, duration1 = result
                    session_data['song_index'] = song_index
                    session_data['SongID'] = SongID
                    session_data['duration'] = duration
                    session_data['songname'] = songname
                    session_data['duration1'] = duration1     
            except queue.Empty:
                time.sleep(0.1)  
            

thread2 =threading.Thread(target=append_session)
thread2.start()            

def curr_session():
    while not exit_event.is_set():
        while True:
            try:
                result1 = current_data.get()
                if result1:
                    position, position1 = result1
                    session_data.update({
                        'position' :position,
                        'position1' :position1
                    })
            except queue.Empty:
                time.sleep(0.1)
            
thread4= threading.Thread(target=curr_session)
thread4.start()

@app.route('/display')
def display():
        try:
            data = {
            'song_index': session_data.get('song_index'),
            'SongID': session_data.get('SongID'),
            'duration': session_data.get('duration'),
            'duration1': session_data.get('duration1'),
            'position': session_data.get('position'),
            'position1': session_data.get('position1'),
            'songname': session_data.get('songname')
        }
            return jsonify(data)
        except Exception as e:
            exit_event.set()
            pygame.mixer.music.stop()
            return f"{e}" 

def nextsongfromalbum(song_url, song_index, songidlist, AlbumID, ArtistID):
    try:
        connection =sqlite3.connect("music.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        if 'song_index' in session_data:
            song_index = session_data.get('song_index')
        new_index =(song_index+1) % len(songidlist)
        if new_index <= len(songidlist):
            SongID = songidlist[new_index]
        else:
            display_text = "There is no more song in album"
            return render_template(url_for('songlistineachalbum', AlbumID = AlbumID, ArtistID = ArtistID, display_text = display_text))
        cursor.execute("select SongName from songtable where SongID=?",(SongID,))
        songn = cursor.fetchone()
        songname = songn['SongName']
        cursor.execute("select SongUrl from songtable where SongID=?",(SongID,))
        song = cursor.fetchone()
        songurl = song["SongUrl"]
        return songurl, new_index, songidlist, AlbumID, ArtistID, SongID, songname
    except Exception as e:
        print(e)
        return "none"
@app.route('/playmusicfromalbum')
def playmusicfromalbum(songurl, song_index, songidlist, AlbumID, ArtistID, SongID, songname):
        while not exit_event.is_set():
            is_paused = False
            try:
                if not mixer.music.get_busy():
                    duration, duration1 = get_duration(songurl)
                    mixer.music.load(songurl)
                    mixer.music.play()
                    playmusic_data.put((songurl, song_index, songidlist, AlbumID, ArtistID, SongID, duration, songname, duration1))   
                while not exit_event.is_set():
                    position = pygame.mixer.music.get_pos() //1000
                    minute = position //60
                    second = position % 60
                    position1 = f"{minute:02}:{second:02}"
                    current_data.put((position, position1))
                    if session_action:
                        action = session_action['action']
                        if action == 'pause':
                            pygame.mixer.music.pause()
                            is_paused = True
                            session_action['action'] = None
                        if action == 'play':
                            pygame.mixer.music.unpause()
                            is_paused = False
                            session_action['action'] = None
                    if not mixer.music.get_busy() and not is_paused:
                        data = nextsongfromalbum(songurl,song_index, songidlist, AlbumID, ArtistID)
                        if data:
                            songurl, new_index, songidlist, AlbumID, ArtistID, SongID, songname = data
                            playmusicfromalbum(songurl, new_index, songidlist, AlbumID, ArtistID, SongID, songname)
                    
            except Exception as e:
                print(e)
                return {e}
@app.route('/playalbum/<AlbumID>/<ArtistID>')
def playalbum(AlbumID, ArtistID):
    songalbumidlist = []
    exit_event.set()
    pygame.mixer.music.stop()
    try:
        connection = sqlite3.connect("music.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("select * from songtable where AlbumID=?",(AlbumID,))
        songalbum = cursor.fetchall()
        for song in songalbum:
            songid = song['SongID']
            songalbumidlist.append(songid)
        argu_id = request.args.get('SongID')
        if not argu_id: 
            start_song_id = songalbumidlist[0]
            start_song_index = 0
            cursor.execute("select * from songtable where SongID=?",(start_song_id,))
            start_song = cursor.fetchone()
            start_song_url = start_song['SongUrl']
            start_song_name = start_song['SongName']
            duration = get_duration(start_song_url)
            print(songalbumidlist)
            exit_event.clear()
            thread3 = threading.Thread(target=playmusicfromalbum, args=(start_song_url, start_song_index, songalbumidlist, AlbumID, ArtistID, start_song_id, start_song_name))
            thread3.start()
            return redirect(url_for('songlistineachalbum', SongID = start_song_id, AlbumID= AlbumID, ArtistID = ArtistID, duration = duration, songalbumidlist = songalbumidlist))
        else:
            start_song_id = int(argu_id)
            start_song_index = songalbumidlist.index(start_song_id)
            cursor.execute("select * from songtable where SongID=?",(argu_id,))
            start_song = cursor.fetchone()
            start_song_url = start_song['SongUrl']
            start_song_name = start_song['SongName']
            duration = get_duration(start_song_url)
            exit_event.clear()
            thread3 = threading.Thread(target=playmusicfromalbum, args=(start_song_url, start_song_index, songalbumidlist, AlbumID, ArtistID, start_song_id, start_song_name))
            thread3.start()
            return redirect(url_for('songlistineachalbum', SongID = start_song_id, AlbumID= AlbumID, ArtistID = ArtistID, duration = duration, songalbumidlist = songalbumidlist))
    except Exception as e:
        print(e)
        flash(f"{e} error occurs", "danger")
        return f"{e}" 
@app.route('/next/<SongID>/<AlbumID>/<ArtistID>')
def next_song(SongID, AlbumID, ArtistID):
    try:
        songidlist = []
        exit_event.set()
        pygame.mixer.music.stop()
        connection = sqlite3.connect("music.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("select * from songtable")
        songl = cursor.fetchall()
        for song in songl:
            songid = song['SongID']
            songidlist.append(songid)
        if 'SongID' in session_data:
            SongID = session_data.get('SongID')
        print(SongID)
        if SongID in songidlist:
            index1 = songidlist.index(SongID)
            print(index1)
            new_index = (index1 + 1) % len(songidlist)
            NextSongID = songidlist[new_index]
            print(SongID)
            return redirect(url_for('play', SongID = NextSongID, AlbumID = AlbumID, ArtistID = ArtistID))
        else:
            print("Song ID is not found")
    except Exception as e:
        print(e)
        
       
@app.route('/previous/<SongID>/<AlbumID>/<ArtistID>')
def previous_song(SongID, AlbumID, ArtistID):
    try:
        songidlist = []
        exit_event.set()
        pygame.mixer.music.stop()
        print(SongID)
        connection = sqlite3.connect("music.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("select * from songtable")
        songl = cursor.fetchall()
        for song in songl:
            songid = song['SongID']
            songidlist.append(songid)
        if 'SongID' in session_data:
            SongID = session_data.get('SongID')
        print(SongID)
        if SongID in songidlist:
            index1 = songidlist.index(SongID)
            print(index1)
            new_index = (index1 - 1) % len(songidlist)
            NextSongID = songidlist[new_index]
            print(SongID)
            return redirect(url_for('play', SongID = NextSongID, AlbumID = AlbumID, ArtistID = ArtistID))
        else:
            print("Song ID is not found")
    except Exception as e:
        print(e)
    
@app.route('/next_song_album/<SongID>/<AlbumID>/<ArtistID>')
def next_song_album(SongID, AlbumID, ArtistID):
    try:
        songidlist = []
        exit_event.set()
        pygame.mixer.music.stop()
        connection = sqlite3.connect("music.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("select * from songtable where AlbumID=?",(AlbumID,))
        songl = cursor.fetchall()
        for song in songl:
            songid = song['SongID']
            songidlist.append(songid)
        if 'SongID' in session_data:
            SongID = session_data['SongID']
            print(SongID)
        if SongID in songidlist:
            index1 = songidlist.index(SongID)
            print(index1)
            new_index = (index1 + 1)
            print(new_index)
            if new_index > (len(songidlist)-1):
                session_data['songname'] = "No more Track in the album"
                return redirect(url_for('songlistineachalbum',AlbumID = AlbumID, ArtistID = ArtistID))
            else:
                NextSongID = songidlist[new_index]
                print(NextSongID)
                return redirect(url_for('playalbum', SongID = NextSongID, AlbumID = AlbumID, ArtistID = ArtistID))
        else:
            print("Song ID is not found")
    except Exception as e:
        return f"{e}"

@app.route('/previous_song_album/<SongID>/<AlbumID>/<ArtistID>')
def previous_song_album(SongID, AlbumID, ArtistID):
    try:
        exit_event.set()
        pygame.mixer.music.stop()
        songidlist = []
        connection = sqlite3.connect("music.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("select * from songtable where AlbumID=?",(AlbumID,))
        songl = cursor.fetchall()
        for song in songl:
            songid = song['SongID']
            songidlist.append(songid)
        if 'SongID' in session_data:
            SongID = session_data.get('SongID')
        if SongID in songidlist:
            index1 = songidlist.index(SongID)
            print(index1)
            new_index = (index1 - 1)
            print(new_index)
            if new_index < 0:
                session_data['songname'] = "No more Track in the album"
                return redirect(url_for('songlistineachalbum',AlbumID = AlbumID, ArtistID = ArtistID))
            else:
                SongID = songidlist[new_index]
                return redirect(url_for('playalbum', SongID = SongID, AlbumID = AlbumID, ArtistID = ArtistID))
        else:
            print("Song ID is not found")
    except Exception as e:
        print(e)




@app.route('/dashboard')
def dashboard():
    try:
        songnamedict = {}
        connection = sqlite3.connect("music.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("select count(RequestID) from requesttable")
        count = cursor.fetchone()
        request_count = count[0]
        cursor.execute("select count(SongID) from songtable")
        count = cursor.fetchone()
        song_count = count[0]
        cursor.execute("select count(UserID) from usertable")
        count = cursor.fetchone()
        user_count = count[0]
        cursor.execute("select count(AlbumID) from albumtable")
        count = cursor.fetchone()
        album_count = count[0]
        cursor.execute("select count(ArtistID) from artisttable")
        count = cursor.fetchone()
        artist_count = count[0]
        cursor.execute("select * from playtable")
        playsong = cursor.fetchall()
        searchdata = request.args.get('searchdata')
        if searchdata:
            cursor.execute("select * from playtable where SongID like ? or UserID like? or SongName like ?",(searchdata, searchdata, searchdata))
            searchdata = cursor.fetchall()
        return render_template('dashboard.html', artist_count = artist_count, album_count = album_count, user_count = user_count, song_count = song_count, request_count = request_count, playsong = playsong, searchdata = searchdata)
    except Exception as e:
        flash(f"Error here {e}","danger")
        return redirect(url_for('login'))



@app.route('/artisttypelist')
def artisttype():
    try:
        connection = sqlite3.connect("music.db")
        connection.row_factory = sqlite3.Row  
        cursor = connection.cursor()
        cursor.execute("select * from artisttypetable")
        artisttypelist = cursor.fetchall()
        return render_template("artisttype.html", artisttypelist = artisttypelist )
               
    except Exception as e:
        print(type(e).__name__)
        print(traceback.format_exc())
        return "none"
     
@app.route('/artisttypeadd', methods=["GET","POST"])
def insertartisttype():
    if(request.method =="GET"):
        # request comes from url address or anchor link
        return render_template("artisttype.html")
    else:
        ArtistType = request.form['artisttype']
        try:
            conn = sqlite3.connect("music.db")
            cursor = conn.cursor()
            cursor.execute("select * from artisttypetable where ArtistType=?",(ArtistType,))
            existing_artisttype = cursor.fetchone()
            if existing_artisttype:
                flash(f"{ArtistType} is already registered in the database", "danger")
                return redirect(url_for("artisttype"))
            cursor.execute("insert into artisttypetable (ArtistType) values (?)",(ArtistType,))
            conn.commit()
            flash("New ArtistType has been inserted ",'success')
            return redirect(url_for("artisttype"))
            
        except Exception as e:
            print(e)
            return "Error" 
        
@app.route("/artisttypeupdate/<ArtistTypeID>")
def artisttypeupdate(ArtistTypeID):
    try:
        conn = sqlite3.connect('music.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("select * from artisttypetable where ArtistTypeID=?",(ArtistTypeID,))
        artisttypelist = cursor.fetchone()
        return render_template("artisttypeupdate.html", artisttypelist  = artisttypelist)
    except Exception as e:
        print(traceback.format_exc())
        print(e)
        return "None"  
    
    


@app.route("/artisttypeupdated/<ArtistTypeID>", methods=["GET","POST"])
def artisttypeupdated(ArtistTypeID):
    if request.method == "POST":
        ArtistType = request.form['artisttype']
        try:
            conn = sqlite3.connect('music.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("select * from artisttypetable where ArtistType=?",(ArtistType,))
            existing_artisttype = cursor.fetchone()
            if existing_artisttype:
                flash(f"Cannot Change to {ArtistType}! That's already existed")
                return redirect(url_for('artisttypeupdate', ArtistTypeID = ArtistTypeID))
            cursor.execute("update artisttypetable set ArtistType=? where ArtistTypeID=?",(ArtistType, ArtistTypeID))
            conn.commit()
            flash(f"Artist Type ID {ArtistTypeID} is successfully updated with {ArtistType}")
            return redirect(url_for("artisttype"))
        except Exception as e:
            print(traceback.format_exc())
            return "None"

@app.route('/artisttypedelete/<ArtistTypeID>')
def artisttype_del(ArtistTypeID):
    try:
        conn = sqlite3.connect("music.db")
        cursor = conn.cursor()
        cursor.execute("select * from artisttypetable where ArtistTypeID=?",(ArtistTypeID,))
        artisttypelist = cursor.fetchone()
        artisttype = artisttypelist[1]
        cursor.execute("delete from artisttypetable where ArtistTypeID=?",(ArtistTypeID,))
        flash(f'{artisttype} has been deleted successfully', "success")
        conn.commit()
        return redirect(url_for("artisttype"))
    except Exception as e:
        print(traceback.format_exc())
        return f"{e}None"

@app.route('/artist')
def artist():
    try:
        connection =sqlite3.connect("music.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("select * from artisttable")
        artistlist = cursor.fetchall()
        cursor.execute("select count(ArtistID) from artisttable")
        count = cursor.fetchone()
        artist_count = count[0]
        searchdata = request.args.get('searchdata')
        if searchdata:
            cursor.execute("select * from artisttable where ArtistName like ?",(searchdata,))
            searchdata = cursor.fetchall()
        return render_template("artist.html", artistlist = artistlist, artist_count = artist_count, searchdata = searchdata)
    
    except Exception as e:
        print(type(e).__name__)
        print(traceback.format_exc())
        return "none"
@app.route('/artistadd')
def artistadd():
    if(request.method=="GET"):
        connection = sqlite3.connect("music.db")
        connection.row_factory = sqlite3.Row  
        cursor = connection.cursor()
        cursor.execute("select * from artisttypetable")
        artisttypelist = cursor.fetchall()
        return render_template('artistadd.html', artisttypelist = artisttypelist)

@app.route('/artistadded', methods=["GET", "POST"])
def artistadded():
    if (request.method == "GET"):
        return render_template('artistadd.html')
    else:
        artist_name = request.form['artistname']
        artist_type = request.form['artisttype']
        biography = request.form['biography']
        if 'photo' not in request.files:
            flash('No file part')
            return redirect(url_for('artistadd'))
        photo = request.files['photo']
        if photo.filename == '':
            flash('No selected file')
            return redirect(url_for('artistadd'))
        if photo and allowed_file(photo.filename):
            photo_file = secure_filename(photo.filename)
            photo_path = os.path.join(app.config['upload_photo'],photo_file)
            photo.save(photo_path)
            photo_path ='\\'+photo_path
            if artist_type == '0':
                flash("Please rechoose the artist type","danger")
                return redirect(url_for('artistadd'))
            else:
                try:
                    connection = sqlite3.connect("music.db")
                    connection.row_factory = sqlite3.Row
                    cursor = connection.cursor()
                    cursor.execute("select * from artisttable where ArtistName=?",(artist_name,))
                    existing_artist = cursor.fetchone()
                    if existing_artist:
                        flash(f"{artist_name} is already registered in the database", "danger")
                        return redirect(url_for("artistadd"))
                    cursor.execute("insert into artisttable (ArtistName, Biography, Photo, ArtistTypeID) values (?,?,?,?)", (artist_name, biography, photo_path, artist_type))
                    connection.commit()
                    flash("New Artist has been inserted ",'success')
                    return redirect(url_for("artist"))
                
                except Exception as e:
                    print(type(e).__name__)
                    print(traceback.format_exc())
                    return "none"

@app.route("/artistupdate/<ArtistID>")
def artistupdate(ArtistID):
    try:
        conn = sqlite3.connect('music.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("select * from artisttable where ArtistID=?",(ArtistID,))
        artistlist = cursor.fetchone()
        cursor.execute("select ArtistTypeID from artisttable where ArtistID=?",(ArtistID,))
        artisttypeid = cursor.fetchone()
        artisttype = artisttypeid[0]
        cursor.execute("select * from artisttypetable where ArtistTypeID=?",(artisttype,))
        artisttypelist = cursor.fetchone()
        artisttypename = artisttypelist[1]
        cursor.execute("select * from artisttypetable")
        artisttypelist = cursor.fetchall()
        return render_template("artistupdate.html", artistlist = artistlist, artisttypelist = artisttypelist, artisttypename=artisttypename)
    except Exception as e:
        print(traceback.format_exc())
        print(e)
        return "None"


@app.route("/artistupdated/<ArtistID>", methods=["GET","POST"])
def artistupdated(ArtistID):
    if (request.method == "GET"):
        return render_template('artistupdate.html')
    else:
        artist_name = request.form['artistname']
        artist_type = request.form['artisttype']
        biography = request.form['biography']
        if 'photo' not in request.files:
            flash('No file part')
            return redirect(url_for('artistupdate', ArtistID = ArtistID))
        photo = request.files['photo']
        if artist_type == '0':
            flash("Please choose the artist type","danger")
            return redirect(url_for('artistupdate', ArtistID = ArtistID))
        else:
            try:
                connection = sqlite3.connect("music.db")
                connection.row_factory = sqlite3.Row
                cursor = connection.cursor()
                cursor.execute("select * from artisttable where ArtistName=?",(artist_name,))
                existing_artist = cursor.fetchone()
                if existing_artist:
                    flash(f"{artist_name} is already registered in the database", "danger")
                    return redirect(url_for("artistupdate", ArtistID = ArtistID))
                if photo.filename == '':
                    cursor.execute("update artisttable set ArtistName=?, Biography=?, ArtistTypeID=? where ArtistID=?",(artist_name, biography, artist_type,ArtistID))
                    connection.commit()
                elif photo and allowed_file(photo.filename):
                    photo_file = secure_filename(photo.filename)
                    photo_path = os.path.join(app.config['upload_photo'],photo_file)
                    photo.save(photo_path)
                    photo_path ='\\'+photo_path
                    cursor.execute("update artisttable set ArtistName=?, Biography=?, Photo=?, ArtistTypeID=? where ArtistID=?",(artist_name, biography, photo_path, artist_type,ArtistID))
                    connection.commit()
                    flash(f"{artist_name} has been updated ",'success')
                return redirect(url_for("artist"))
                
            except Exception as e:
                print(type(e).__name__)
                print(traceback.format_exc())
                return "none"
            
            
@app.route('/artistdelete/<ArtistID>')
def artist_del(ArtistID):
    try:
        conn = sqlite3.connect("music.db")
        cursor = conn.cursor()
        cursor.execute("select ArtistName from artisttable where ArtistID=?",(ArtistID,))
        artisttypeid = cursor.fetchone()
        artisttype = artisttypeid[0]
        cursor.execute("delete from artisttable where ArtistID=?",(ArtistID,))
        flash(f'{artisttype} has been deleted successfully', "success")
        conn.commit()
        return redirect(url_for("artist"))
    except Exception as e:
        print(traceback.format_exc())
        return "None"
    
@app.route('/albumlist')
def album():
    try:
        connection =sqlite3.connect("music.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("select * from albumtable")
        albumlist = cursor.fetchall()
        cursor.execute("select count(AlbumID) from albumtable")
        count = cursor.fetchone()
        album_count = count[0]
        searchdata = request.args.get('searchdata')
        if searchdata:
            cursor.execute("select * from albumtable where AlbumName like ?",(searchdata,))
            searchdata = cursor.fetchall()
        return render_template("albumlist.html", albumlist = albumlist, album_count = album_count, searchdata = searchdata)
    
    except Exception as e:
        print(type(e).__name__)
        print(traceback.format_exc())
        return "none"
    

@app.route('/albumadd')
def albumadd():
    if(request.method=="GET"):
        connection = sqlite3.connect("music.db")
        connection.row_factory = sqlite3.Row  
        cursor = connection.cursor()
        cursor.execute("select * from artisttable")
        artistlist = cursor.fetchall()
        return render_template('albumadd.html', artistlist = artistlist)


@app.route('/albumadded', methods=["GET", "POST"])
def albumadded():
    if (request.method == "GET"):
        return render_template('albumadd.html')
    else:
        album_name = request.form['albumname']
        artist_name = request.form['artistname']
        if 'photo' not in request.files:
            flash('No file part')
            return redirect(url_for('albumadd'))
        photo = request.files['photo']
        if photo.filename == '':
            flash('No selected file')
            return redirect(url_for('albumadd'))
        if photo and allowed_file(photo.filename):
            photo_file = secure_filename(photo.filename)
            photo_path = os.path.join(app.config['upload_photo'],photo_file)
            photo.save(photo_path)
            photo_path ='\\'+photo_path
            if artist_name == '0':
                flash("Please rechoose the artist type","danger")
                return redirect(url_for('albumadd'))
            else:
                try:
                    connection = sqlite3.connect("music.db")
                    connection.row_factory = sqlite3.Row
                    cursor = connection.cursor()
                    cursor.execute("select * from albumtable where AlbumName=?",(album_name,))
                    existing_artist = cursor.fetchone()
                    if existing_artist:
                        flash(f"{album_name} is already registered in the database", "danger")
                        return redirect(url_for("albumadd"))
                    cursor.execute("insert into albumtable (AlbumName, Photo, ArtistID) values (?,?,?)", (album_name, photo_path, artist_name))
                    connection.commit()
                    flash("New Album has been inserted ",'success')
                    return redirect(url_for("album"))
                
                except Exception as e:
                    print(type(e).__name__)
                    print(traceback.format_exc())
                    return "none"

@app.route("/albumupdate/<AlbumID>")
def albumupdate(AlbumID):
    try:
        conn = sqlite3.connect('music.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("select * from albumtable where AlbumID=?",(AlbumID,))
        albumlist = cursor.fetchone()
        cursor.execute("select ArtistID from albumtable where AlbumID=?",(AlbumID,))
        artisttypeid = cursor.fetchone()
        artistid = artisttypeid[0]
        cursor.execute("select * from artisttable where ArtistID=?",(artistid,))
        artistlist = cursor.fetchone()
        artistnam = artistlist[1]
        cursor.execute("select * from artisttable")
        artistlist = cursor.fetchall()
        return render_template("albumupdate.html", albumlist = albumlist, artistlist = artistlist, artistnam=artistnam)
    except Exception as e:
        print(traceback.format_exc())
        print(e)
        return "None"


@app.route("/albumupdated/<AlbumID>", methods=["GET","POST"])
def albumupdated(AlbumID):
    if (request.method == "GET"):
        return render_template('albumupdate.html')
    else:
        album_name = request.form['albumname']
        artist_name = request.form['artistname']
        if 'photo' not in request.files:
            flash('No file part')
            return redirect(url_for('albumupdate', AlbumID = AlbumID))
        photo = request.files['photo']
        if not artist_name or artist_name == '':
            flash("Please choose the artist name","danger")
            return redirect(url_for('albumupdate', AlbumID = AlbumID))
        else:
            try:
                connection = sqlite3.connect("music.db")
                connection.row_factory = sqlite3.Row
                cursor = connection.cursor()
                cursor.execute("select * from albumtable where AlbumName=?",(album_name,))
                existing_album = cursor.fetchone()
                if existing_album:
                    flash(f"{album_name} is already registered in the database", "danger")
                    return redirect(url_for("albumupdate", AlbumID = AlbumID))
                if photo.filename == '':
                    cursor.execute("update albumtable set AlbumName=?, ArtistID=? where AlbumID=?",(album_name, artist_name, AlbumID))
                    connection.commit()
                elif photo and allowed_file(photo.filename):
                    photo_file = secure_filename(photo.filename)
                    photo_path = os.path.join(app.config['upload_photo'],photo_file)
                    photo.save(photo_path)
                    photo_path ='\\'+photo_path
                    cursor.execute("update albumtable set AlbumName=?, Photo=?, ArtistID=? where AlbumID=?",(album_name, photo_path, artist_name, AlbumID))
                    connection.commit()
                    flash(f"{album_name} has been updateds",'success')
                return redirect(url_for("album"))
                
            except Exception as e:
                print(type(e).__name__)
                print(traceback.format_exc())
                return "none"
@app.route('/albumdelete/<AlbumID>')
def album_del(AlbumID):
    try:
        conn = sqlite3.connect("music.db")
        cursor = conn.cursor()
        cursor.execute("select AlbumName from albumtable where AlbumID=?",(AlbumID,))
        albumid = cursor.fetchone()
        album = albumid[0]
        cursor.execute("delete from albumtable where AlbumID=?",(AlbumID,))
        flash(f'{album} has been deleted successfully', "success")
        conn.commit()
        return redirect(url_for("album"))
    except Exception as e:
        print(traceback.format_exc())        
        return "None"
@app.route('/request', methods= ["GET","POST"])
def user_request():
    if request.method == "GET":
        return render_template("signup.html")
    else:
        email = request.form['email']
        username = request.form['name']
        password = request.form['password']
        
        hashed_pwd = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        
        try:
            connection = sqlite3.connect("music.db")  
            cursor = connection.cursor()
            cursor.execute("select * from requesttable where Email=?",(email,))  
            existing_request = cursor.fetchone()
            if existing_request:
                flash(f"{email} is already registered in the website! Use Another!", "danger")
                return redirect(url_for("signup"))            
            cursor.execute("insert into requesttable (UserName, Email, Password) values (?,?,?)",(username, email, hashed_pwd) )
            connection.commit()
            flash("User request has been sent successfully and information will be checked within 24 hours and can use the website",'success')
            return redirect(url_for("login"))
        except Exception as e:
            print(type(e).__name__)
            print(traceback.format_exc())
            return "none"
@app.route('/requestlist')
def view_request():
    try:
        connection = sqlite3.connect("music.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("select * from requesttable")
        requestlist = cursor.fetchall()
        cursor.execute("select count(RequestID) from requesttable")
        count = cursor.fetchone()
        request_count = count[0]
        searchdata = request.args.get('searchdata')
        if searchdata:
            cursor.execute("select * from requesttable where UserName like ? or Email like ?",(searchdata,searchdata))
            searchdata = cursor.fetchall()
        return render_template("request.html", requestlist = requestlist, request_count = request_count, searchdata = searchdata)
    except Exception as e:
        print(type(e).__name__)
        print(traceback.format_exc())
        return "none"

@app.route('/requestdelete/<RequestID>')
def request_del(RequestID):
    try:
        conn = sqlite3.connect("music.db")
        cursor = conn.cursor()
        cursor.execute("select UserName from requesttable where RequestID=?",(RequestID,))
        requestid = cursor.fetchone()
        request = requestid[0]
        cursor.execute("delete from requesttable where RequestID=?",(RequestID,))
        flash(f'{request} has been deleted successfully', "success")
        conn.commit()
        return redirect(url_for("view_request"))
    except Exception as e:
        print(traceback.format_exc())
        return "None"   


@app.route('/confirm/<RequestID>', methods= ["GET","POST"])
def confirm_request(RequestID):
        try:
            connection = sqlite3.connect("music.db")  
            cursor = connection.cursor()
            cursor.execute("select * from requesttable where RequestID=?",(RequestID,))  
            request = cursor.fetchone()
            name = request[1]
            email = request[2]
            pwd = request[3]
            cursor.execute("select * from usertable where Email=?",(email,))
            existing_email = cursor.fetchone()
            if existing_email:
                flash(f"{email} is registered as user and delete that request", "danger")
                return redirect(url_for("view_request"))
            cursor.execute("insert into usertable (UserName, Email, Password, Permission) values (?,?,?,?)",(request[1], request[2], request[3], "User") )
            cursor.execute("delete from requesttable where RequestID=?",(RequestID,))
            connection.commit()
            flash("User request {name} has been confirmed successfully and deleted from Request Table",'success')
            return redirect(url_for("view_user"))
        except Exception as e:
            print(type(e).__name__)
            print(traceback.format_exc())
            return "none"

@app.route('/userlist')
def view_user():
    try:
        connection = sqlite3.connect("music.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("select * from usertable")
        userlist = cursor.fetchall()
        cursor.execute("select count(UserID) from usertable")
        count = cursor.fetchone()
        user_count = count[0]
        searchdata = request.args.get('searchdata')
        if searchdata:
            cursor.execute("select * from usertable where UserName like ? or Email like ?",(searchdata,searchdata))
            searchdata = cursor.fetchall()
        return render_template("usertable.html", userlist = userlist, user_count = user_count, searchdata = searchdata)
    except Exception as e:
        print(type(e).__name__)
        print(traceback.format_exc())
        return "none"

@app.route("/permissionupdate/<UserID>")
def userupdate(UserID):
    try:
        conn = sqlite3.connect('music.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("select * from usertable where UserID=?",(UserID,))
        userlist = cursor.fetchone()
        return render_template("userupdate.html", userlist  = userlist)
    except Exception as e:
        print(traceback.format_exc())
        print(e)
        return "None"  

@app.route('/updateduser/<UserID>', methods=["GET","POST"])
def updated_user(UserID):
    if request.method == "GET":
        return render_template("updateuser.html")
    else:
        user_role = request.form['permission']
        try:
            conn = sqlite3.connect('music.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if user_role == '':
                cursor.execute("update usertable set Permission=? where UserID=?",("User", UserID))
                conn.commit()
            else:
                cursor.execute("update usertable set Permission=? where UserID=?",(user_role, UserID))
                conn.commit()
            flash(f"Artist Type ID {UserID} is successfully updated with {UserID}")
            return redirect(url_for("view_user"))
        except Exception as e:
            print(traceback.format_exc())
            return "None"
        
@app.route('/userdelete/<UserID>')
def user_del(UserID):
    try:
        conn = sqlite3.connect("music.db")
        cursor = conn.cursor()
        cursor.execute("select * from usertable where UserID=?",(UserID,))
        userlist = cursor.fetchone()
        user = userlist[1]
        cursor.execute("delete from usertable where UserID=?",(UserID,))
        flash(f'{user} has been deleted successfully', "success")
        conn.commit()
        return redirect(url_for("view_user"))
    except Exception as e:
        print(traceback.format_exc(), e)
        return "None"


@app.route('/songlist')
def song():
    try:
        connection =sqlite3.connect("music.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("select * from songtable")
        songlist = cursor.fetchall()
        cursor.execute("select count(SongID) from songtable")
        count = cursor.fetchone()
        song_count = count[0]
        searchdata = request.args.get('searchdata')
        if searchdata:
            cursor.execute("select * from songtable where SongName like ?",(searchdata,))
            searchdata = cursor.fetchall()
        return render_template("songlist.html", songlist = songlist, song_count = song_count, searchdata = searchdata)
    
    except Exception as e:
        print(type(e).__name__)
        print(traceback.format_exc())
        return "none"   

@app.route('/songadd')
def songadd():
    if(request.method=="GET"):
        connection = sqlite3.connect("music.db")
        connection.row_factory = sqlite3.Row  
        cursor = connection.cursor()
        cursor.execute("select * from albumtable")
        albumlist = cursor.fetchall()
        return render_template('songadd.html', albumlist = albumlist)
    

@app.route('/songadded', methods=["GET", "POST"])
def songadded():
    if (request.method == "GET"):
        return render_template('songadd.html')
    else:
        song_name = request.form['songname']
        album_name = request.form['album']
        if 'mp3' not in request.files:
            flash('No file part')
            return redirect(url_for('songadd'))
        mp3 = request.files['mp3'] 
        if mp3.filename == '':
            flash('No selected file')
            return redirect(url_for('songadd'))
        if mp3 and allowed_audio_file(mp3.filename):
            mp3_file = secure_filename(mp3.filename)
            mp3_file_path = os.path.join(app.config['upload_mp3'], mp3_file)
            mp3.save(mp3_file_path)
            if album_name == '0':
                flash("Please rechoose the album","danger")
                return redirect(url_for('songadd'))
            else:
                try:
                    connection = sqlite3.connect("music.db")
                    connection.row_factory = sqlite3.Row
                    cursor = connection.cursor()
                    cursor.execute("select * from songtable where SongName=?",(song_name,))
                    existing_song = cursor.fetchone()
                    if existing_song:
                        flash(f"{song_name} is alread added into the database", "danger")
                        return redirect(url_for("songadd"))
                    cursor.execute("insert into songtable (SongName, SongUrl, AlbumID) values (?,?,?)", (song_name,  mp3_file_path, album_name))
                    connection.commit()
                    flash("New Song has been inserted ",'success')
                    return redirect(url_for("song"))
                
                except Exception as e:
                    print(type(e).__name__)
                    print(traceback.format_exc())
                    return "none"
                

@app.route("/songupdate/<SongID>")
def songupdate(SongID):
    try:
        conn = sqlite3.connect('music.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("select * from songtable where SongID=?",(SongID,))
        songlist = cursor.fetchone()
        cursor.execute("select AlbumID from songtable where SongID=?",(SongID,))
        albumid = cursor.fetchone()
        albid = albumid[0]
        cursor.execute("select * from albumtable where AlbumID=?",(albid,))
        albumlist = cursor.fetchone()
        albumname = albumlist[1]
        cursor.execute("select * from albumtable")
        albumlist = cursor.fetchall()
        return render_template("songupdate.html", songlist = songlist, albumlist = albumlist, albumname=albumname)
    except Exception as e:
        print(traceback.format_exc())
        print(e)
        return "None"
    
@app.route("/songupdated/<SongID>", methods=["GET","POST"])
def songupdated(SongID):
    if (request.method == "GET"):
        return render_template('songupdate.html')
    else:
        song_name = request.form['songname']
        album_name = request.form['albumname']
        if 'mp3' not in request.files:
            flash('No file part')
            return redirect(url_for('songupdate'))
        mp3 = request.files['mp3'] 
        if album_name == '0':
            flash("Please rechoose the album","danger")
            return redirect(url_for('songupdate', SongID = SongID))
        else:
            try:
                connection = sqlite3.connect("music.db")
                connection.row_factory = sqlite3.Row
                cursor = connection.cursor()
                cursor.execute("select * from songtable where SongName=?",(song_name,))
                existing_song = cursor.fetchone()
                if existing_song:
                    flash(f"{song_name} is already registered in the database", "danger")
                    return redirect(url_for("songupdate", SongID = SongID))
                if mp3.filename == '':
                    cursor.execute("update songtable set SongName=?, AlbumID=? where SongID=?",(song_name, album_name, SongID))
                    connection.commit()
                elif mp3 and allowed_audio_file(mp3.filename):
                    mp3_file = secure_filename(mp3.filename)
                    mp3_file_path = os.path.join(app.config['upload_photo'],mp3_file)
                    mp3.save(mp3_file_path)
                    cursor.execute("update songtable set SongName=?, SongUrl=?, AlbumID=? where SongID=?",(song_name, mp3_file_path, album_name, SongID))
                    connection.commit()
                    flash(f"{album_name} has been updated",'success')
                return redirect(url_for("song"))
                    
            except Exception as e:
                print(type(e).__name__)
                print(traceback.format_exc())
                return "none"


@app.route('/songdelete/<SongID>')
def song_del(SongID):
    try:
        connection = sqlite3.connect("music.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("select * from songtable where SongID=?",(SongID,))
        song = cursor.fetchone()
        songname = song['SongName']
        cursor.execute("delete from songtable where SongID=?",(SongID,))
        flash(f'{songname} has been deleted successfully', "success")
        connection.commit()
        return redirect(url_for("song"))
    
    
    except Exception as e:
        print(traceback.format_exc())        
        return "None"
@app.route('/contactmessage', methods= ['GET','POST'])
def contact_message():
        if request.method == 'GET':
            return redirect(url_for('home'))
        else:
            username = request.form['name']
            email = request.form['email']
            message = request.form['message']
            try:
                connection = sqlite3.connect("music.db") 
                connection.row_factory = sqlite3.Row 
                cursor = connection.cursor()
                cursor.execute("select UserID from usertable where UserName=? AND Email=?",(username, email))
                user = cursor.fetchone()
                userid = user[0]
                date = datetime.now()
                cursor.execute("insert into contacttable (UserID, Text, DateTime) values (?,?,?)",(userid, message,date))
                connection.commit()
                connection.close()
                flash("Message was successfully sent!","success")
                return redirect(url_for('home'))
                
            
            except Exception as e:
                flash(f"Error occurs {e}","danger")
                return redirect(url_for('login'))

@app.route('/messagelist')
def view_message():
    try:
        connection = sqlite3.connect("music.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("select * from contacttable")
        messagelist = cursor.fetchall()
        cursor.execute("select count(ContactID) from contacttable")
        count = cursor.fetchone()
        message_count = count[0]
        searchdata = request.args.get('searchdata')
        if searchdata:
            cursor.execute("select * from contacttable where Text like ?",(searchdata,))
            searchdata = cursor.fetchall()
        return render_template("contactmessage.html", messagelist = messagelist, message_count = message_count, searchdata = searchdata)
    except Exception as e:
        print(type(e).__name__)
        print(traceback.format_exc())
        return "none"
   
@app.route('/deletemessage/<ContactID>')
def message_del(ContactID):
    try:
        conn = sqlite3.connect("music.db")
        cursor = conn.cursor()
        cursor.execute("select UserID from contacttable where ContactID=?",(ContactID,))
        messageid = cursor.fetchone()
        userid = messageid[0]
        cursor.execute("delete from contacttable where ContactID=?",(ContactID,))
        flash(f"{userid}'s message has been deleted successfully", "success")
        conn.commit()
        return redirect(url_for("view_message"))
    except Exception as e:
        print(traceback.format_exc())        
        return "None"  
@app.route("/searchartist", methods=['GET','POST'])
def searchartist():
    searchdata = request.form['searchartist']
    searchdata = '%' + searchdata + '%' 
    return redirect(url_for('artist', searchdata = searchdata))

@app.route("/searchsong", methods=['GET','POST'])
def searchsong():
    searchdata = request.form['searchsong']
    searchdata = '%' + searchdata + '%' 
    return redirect(url_for('song', searchdata = searchdata))

@app.route("/searchuser", methods=['GET','POST'])
def searchuser():
    searchdata = request.form['searchuser']
    searchdata = '%' + searchdata + '%' 
    return redirect(url_for('view_user', searchdata = searchdata))


@app.route("/searchrequest", methods=['GET','POST'])
def searchrequest():
    searchdata = request.form['searchrequest']
    searchdata = '%' + searchdata + '%' 
    return redirect(url_for('view_request', searchdata = searchdata))

@app.route("/searchalbum", methods=['GET','POST'])
def searchalbum():
    searchdata = request.form['searchalbum']
    searchdata = '%' + searchdata + '%' 
    return redirect(url_for('album', searchdata = searchdata))


@app.route("/searchmessage", methods=['GET','POST'])
def searchmessage():
    searchdata = request.form['searchmessage']
    searchdata = '%' + searchdata + '%' 
    return redirect(url_for('view_message', searchdata = searchdata))

@app.route("/searchplay", methods=['GET','POST'])
def searchplay():
    searchdata = request.form['searchplay']
    searchdata = '%' + searchdata + '%' 
    return redirect(url_for('dashboard', searchdata = searchdata))


@app.route("/searchuserside", methods=['GET','POST'])
def searchuserside():
    connection = sqlite3.connect("music.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    searchdata = request.form['searchuser']
    searchdata = '%' + searchdata + '%'
    cursor.execute('select * from artisttable where ArtistName like ?',(searchdata,))
    artist = cursor.fetchall()
    if artist:
        return redirect(url_for('userartist', searchdata = searchdata))
    cursor.execute('select * from albumtable where AlbumName like? ',(searchdata,))
    album = cursor.fetchone()
    if album:
        ArtistID = album['ArtistID']
        return redirect(url_for('albumlistbyeachartist',ArtistID = ArtistID, searchdata = searchdata))
    cursor.execute('select * from songtable where SongName like ?',(searchdata,))
    song = cursor.fetchone()
    AlbumID = song['AlbumID']
    cursor.execute("select * from albumtable where AlbumID=?",(AlbumID,))
    album = cursor.fetchone()
    ArtistID = album['ArtistID']
    if song:
        return redirect(url_for('songlistineachalbum',AlbumID=AlbumID, ArtistID= ArtistID, searchdata = searchdata))

if __name__ == "__main__":
    app.run(debug=True, port=5003)