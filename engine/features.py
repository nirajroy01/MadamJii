import os
import re
import struct
import time
import webbrowser
import sqlite3
import subprocess
from shlex import quote

import eel
import hugchat
import pyaudio
import pywhatkit as kit
import pvporcupine
import pyautogui as autogui
from playsound import playsound

from engine.command import speak
from engine.config import ASSISTANT_NAME
from engine.helper import etract_yt_term, remove_words
from hugchat import hugchat


# Database connection
conn = sqlite3.connect("madamjii.db")
cursor = conn.cursor()

# Audio cue
@eel.expose
def playAssistantSound():
    music_dir = "www\\assets\\audio\\start_sound.mp3"
    playsound(music_dir)


# Open app or website
def openCommand(query):
    query = query.replace(ASSISTANT_NAME, "").replace("open", "").lower().strip()

    try:
        cursor.execute('SELECT path FROM sys_command WHERE name IN (?)', (query,))
        results = cursor.fetchall()

        if results:
            speak("Opening " + query)
            os.startfile(results[0][0])
        else:
            cursor.execute('SELECT url FROM web_command WHERE name IN (?)', (query,))
            results = cursor.fetchall()

            if results:
                speak("Opening " + query)
                webbrowser.open(results[0][0])
            else:
                speak("Opening " + query)
                try:
                    os.system('start ' + query)
                except:
                    speak("Not found")
    except Exception as e:
        print("Error in openCommand():", e)
        speak("Something went wrong.")


# Play on YouTube
def PlayYoutube(query):
    search_term = etract_yt_term(query)
    if search_term:
        speak("Playing " + search_term + " on YouTube")
        kit.playonyt(search_term)
    else:
        speak("Sorry, I couldn't understand what to play.")


# Hotword Detection
def hotword():
    porcupine = None
    paud = None
    audio_stream = None

    try:
        porcupine = pvporcupine.create(keywords=["jarvis", "alexa"])
        paud = pyaudio.PyAudio()

        audio_stream = paud.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )

        print("Listening for hotwords...")

        while True:
            pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            keyword_index = porcupine.process(pcm)

            if keyword_index >= 0:
                print("Hotword detected!")
                autogui.keyDown("win")
                autogui.press("j")
                time.sleep(2)
                autogui.keyUp("win")

    except Exception as e:
        print(f"Error in hotword(): {e}")
    finally:
        if porcupine:
            porcupine.delete()
        if audio_stream:
            audio_stream.close()
        if paud:
            paud.terminate()


# Find Contact in Database
def findContact(query):
    words_to_remove = [
        ASSISTANT_NAME, 'make', 'a', 'to', 'phone', 'call',
        'send', 'message', 'whatsapp', 'video', 'text', 'an', 'on'
    ]
    query = remove_words(query.lower(), words_to_remove).strip()

    try:
        cursor.execute("SELECT mobile_no FROM contacts WHERE LOWER(name) LIKE ? OR LOWER(name) LIKE ?", 
                       ('%' + query + '%', query + '%'))
        results = cursor.fetchall()
        print("DB lookup results:", results)

        if results:
            mobile_number_str = str(results[0][0])
            if not mobile_number_str.startswith('+91'):
                mobile_number_str = '+91' + mobile_number_str
            return mobile_number_str, query
        else:
            return 0, query
    except Exception as e:
        print("Error in findContact():", e)
        speak('There was a problem accessing your contacts.')
        return 0, query


# Send WhatsApp Message / Call 
def whatsApp(mobile_no, message, flag, name):
    if flag == 'message':
        target_tab = 20
        jarvis_message = "Message sent successfully to " + name
    elif flag == 'video':
        target_tab = 13
        message = ''
        jarvis_message = "Start Calling " + name
    else:
        target_tab = 14
        message = ''
        jarvis_message = "Starting video call with " + name

    encoded_message = quote(message)
    whatsapp_url = f"whatsapp://send?phone={mobile_no}&text={encoded_message}"
    full_command = f'start "" "{whatsapp_url}"'

    try:
        subprocess.run(full_command, shell=True)
        time.sleep(5)
        subprocess.run(full_command, shell=True)

        autogui.hotkey('ctrl', 'f')
        for _ in range(1, target_tab):
            autogui.hotkey('tab')
        autogui.hotkey('enter')

        speak(jarvis_message)

    except Exception as e:
        print("Error in whatsApp():", e)
        speak("There was an error using WhatsApp.")


# Send Message Placeholder 
def sendMessage(message, mobile_no, name):
    speak(f"Sending message to {name}")
    print(f"[DEBUG] Message to {mobile_no}: {message}")
    # You can integrate real SMS APIs here if needed


# chat bot 
def chatBot(query):
    user_input = query.lower()
    chatbot = hugchat.ChatBot(cookie_path="engine\cookies.json")
    id = chatbot.new_conversation()
    chatbot.change_conversation(id)
    response =  chatbot.chat(user_input)
    print(response)
    speak(response)
    return response