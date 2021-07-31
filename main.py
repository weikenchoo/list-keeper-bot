import telebot
import json
import os
import pyrebase
import random
from dotenv import load_dotenv
from telebot import types
from urllib.request import urlopen

load_dotenv()
firebase_config = {
    "apiKey": os.getenv("apiKey"),
    "authDomain": os.getenv("authDomain"),
    "databaseURL": os.getenv("databaseURL"),
    "projectId": os.getenv("projectId"),
    "storageBucket": os.getenv("storageBucket"),
    "messagingSenderId": os.getenv("messagingSenderId"),
    "appId": os.getenv("appId"),
    "serviceAccount":
    {
        "type": os.getenv("type"),
        "project_id": os.getenv("project_id"),
        "private_key_id": os.getenv("private_key_id"),
        "private_key": os.getenv("private_key"),
        "client_email": os.getenv("client_email"),
        "client_id": os.getenv("client_id"),
        "auth_uri": os.getenv("auth_uri"),
        "token_uri": os.getenv("token_uri"),
        "auth_provider_x509_cert_url": os.getenv("auth_provider_x509_cert_url"),
        "client_x509_cert_url": os.getenv("client_x509_cert_url")
    }
}
token = os.getenv('API_TOKEN')
bot = telebot.TeleBot(token, parse_mode=None)
firebase = pyrebase.initialize_app(firebase_config)
storage = firebase.storage()
data_dir = "data/"



def get_data(chat_id):
    if not os.path.isdir(data_dir):
        os.mkdir(data_dir)
    path = data_dir + str(chat_id) + ".json"
    bucket = storage.bucket
    blob = bucket.get_blob(path)
    if blob:
        url = storage.child(path).get_url(None)
        response = urlopen(url)
        data = json.loads(response.read())
    else:
        data = {}
        save_data(chat_id,data)
    return data

def add_to_dict(chat_id,listName,data,newEntry=None):
    if listName in data:
        data[listName].append(newEntry)
        bot.send_message(chat_id,"Added " + newEntry + " into " + listName + ".")
    else:
        if not newEntry:
            data[listName] = []
            bot.send_message(chat_id,"Created list called "+ listName +".")
    save_data(chat_id,data)
    

def save_data(chat_id,data):
    path = data_dir + str(chat_id) + ".json"
    with open(path, "w") as write_file:
        json.dump(data, write_file)
    storage.child(path).put(path)

def remove_data(chat_id,data,listName,removeItem):
    if data:
        if listName in data:
            if removeItem in data[listName]:
                data[listName].remove(removeItem)
                bot.send_message(chat_id,"Successfully removed " + removeItem + " from "+ listName + ".")
            else:
                bot.send_message(chat_id,"No such item in the list.")
    save_data(chat_id,data)

def get_lists_markup(data):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    kbList = []
    new_row = []

    for key in data.keys():
        new_row.append(types.KeyboardButton(key).to_dict())
        
        if len(new_row) == 3:
            kbList.append(new_row)
            new_row=[]
            
        elif key == list(data.keys())[-1]:
            kbList.append(new_row)
    
    
    markup.keyboard = kbList
    return markup

def get_items_markup(targetList,data):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    kbList = []
    new_row = []

    for item in data[targetList]:
        new_row.append(types.KeyboardButton(item).to_dict())
        
        if len(new_row) == 3:
            kbList.append(new_row)
            new_row=[]
            
        elif item == data[targetList][-1]:
            kbList.append(new_row)

    markup.keyboard = kbList
    return markup


def getItems(targetList,data):
    if data:
        all_items = ""
        if targetList in data:
            for items in data[targetList]:
                all_items += "- "+ items + "\n"
        else:
            return False
    else:
        return False

    return all_items

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
    """
    Here are all the available commands:
    /new - Create a new list.
    /delete - Delete an existing list.
    /clear - Clear all items from an existing list.
    /add - Add an item to an existing list.
    /remove - Remove an item from an existing list.
    /show - Show all items from an existing list.
    /all - Show all items from all existing lists.
    /random - Will return a random item from an existing list.
    
    """)


@bot.message_handler(commands=['add'])
def list_to_add(message):
    chat_id = message.chat.id
    data = get_data(chat_id)
    markup = get_lists_markup(data)
    if markup.keyboard:
        msg = bot.send_message(chat_id, "Choose your list:", reply_markup=markup)
        bot.register_next_step_handler(msg, lambda m :nameItem(m,data))
    else:
        bot.send_message(chat_id,"You have not created a list.")

def nameItem(message,data):
    chat_id = message.chat.id
    if message.text:
        targetList = message.text
        if targetList in data:
            markup = types.ForceReply()
            msg = bot.send_message(chat_id, "Enter name for item to be added to the list.", reply_markup=markup)
            bot.register_next_step_handler(msg,lambda m : saveToList(m,targetList,data))
        else:
            bot.send_message(chat_id,"The list " + targetList + " has not been created.")
    else:
        bot.send_message(chat_id,"Sorry, I only support text and emojis.")
        markup = get_lists_markup(chat_id)
        msg = bot.send_message(chat_id, "Choose your list:", reply_markup=markup)
        bot.register_next_step_handler(msg, nameItem)

def saveToList(message,targetList,data):
    chat_id = message.chat.id
    if message.text:
        add_to_dict(chat_id,targetList,data,message.text)
    else:
        bot.send_message(chat_id,"Sorry, I only support text and emojis.")
        markup = types.ForceReply()
        msg = bot.send_message(chat_id, "Enter name for item to be added to the list.", reply_markup=markup)
        bot.register_next_step_handler(msg,lambda m : saveToList(m,targetList))


@bot.message_handler(commands=['remove'])
def list_to_remove(message):
    chat_id = message.chat.id
    data = get_data(chat_id)
    markup = get_lists_markup(data)
    if markup.keyboard:
        msg = bot.send_message(chat_id, "Choose your list:", reply_markup=markup)
        bot.register_next_step_handler(msg, lambda m : itemFromList(m,data))
    else:
        bot.send_message(chat_id,"You have not created a list.")

def itemFromList(message,data):
    chat_id = message.chat.id
    if message.text:
        targetList = message.text
        all_items = getItems(targetList,data)
        if not all_items:
            bot.send_message(chat_id,"This list is empty or does not exist.")
        else:
            bot.send_message(chat_id,all_items)
            markup = get_items_markup(targetList,data)
            msg = bot.send_message(chat_id, "Choose item to be removed from the list.", reply_markup=markup)
            bot.register_next_step_handler(msg,lambda m:removeFromList(m,targetList,all_items,data))
    else:
        bot.send_message(chat_id,"Sorry, I only support text and emojis.")
        markup = get_lists_markup(chat_id)
        msg = bot.send_message(chat_id, "Choose your list:", reply_markup=markup)
        bot.register_next_step_handler(msg, itemFromList)

def removeFromList(message,targetList,all_items,data):
    chat_id = message.chat.id
    if message.text:
        remove_data(chat_id,data,targetList,message.text)
    else:
        bot.send_message(chat_id,"Sorry, I only support text and emojis.")
        bot.send_message(chat_id,all_items)
        markup = get_items_markup(targetList,data)
        msg = bot.send_message(chat_id, "Choose item to be removed from the list.", reply_markup=markup)
        bot.register_next_step_handler(msg,lambda m:removeFromList(m,targetList,all_items,data))
        



@bot.message_handler(commands=['new'])
def new(message):
    chat_id = message.chat.id
    markup = types.ForceReply()
    msg = bot.send_message(chat_id, "Enter name for the new list.", reply_markup=markup)
    bot.register_next_step_handler(msg,newList)

def newList(message):
    chat_id = message.chat.id
    if message.text:
        data = get_data(chat_id)
        targetList = message.text
        if targetList in data:
            bot.send_message(chat_id,"This list already exists.")
        else:
            add_to_dict(chat_id,targetList,data)
    else:
        bot.send_message(chat_id,"Sorry, I only support text and emojis.")
        markup = types.ForceReply()
        msg = bot.send_message(chat_id, "Enter name for the new list.", reply_markup=markup)
        bot.register_next_step_handler(msg,newList)


@bot.message_handler(commands=['delete'])
def list_to_delete(message):
    chat_id = message.chat.id
    data = get_data(chat_id)
    markup = get_lists_markup(data)
    if markup.keyboard:
        msg = bot.send_message(chat_id, "Choose list to be deleted.", reply_markup=markup)
        bot.register_next_step_handler(msg,lambda m:deleteList(m,data))
    else:
        bot.send_message(chat_id,"You have not created a list.")

def deleteList(message,data):
    chat_id = message.chat.id
    if message.text:
        targetList = message.text
        if targetList in data:
            data.pop(targetList)
            save_data(chat_id,data)
            bot.send_message(chat_id,targetList+" has been deleted.")
        else:
            bot.send_message(chat_id,targetList+" does not exist.")
    else:
        bot.send_message(chat_id,"Sorry, I only support text and emojis.")
        markup = get_lists_markup(data)
        msg = bot.send_message(chat_id, "Choose list to be deleted.", reply_markup=markup)
        bot.register_next_step_handler(msg,lambda m:deleteList(m,data))


@bot.message_handler(commands=['show'])
def list_to_show(message):
    chat_id = message.chat.id
    data = get_data(chat_id)
    markup = get_lists_markup(data)
    if data:
        msg = bot.send_message(chat_id, "Choose your list:", reply_markup=markup)
        bot.register_next_step_handler(msg, lambda m : showList(m,data))
    else:
        bot.send_message(chat_id,"You have not created a list.")
    
def showList(message,data):
    chat_id = message.chat.id
    if message.text:
        targetList = message.text
        all_items = getItems(targetList,data)
        if not all_items:
            bot.send_message(chat_id,"This list is empty.")
        else:
            bot.send_message(chat_id,targetList+" :")
            bot.send_message(chat_id,all_items)
    else:
        markup = get_lists_markup(data)
        if data:
            bot.send_message(chat_id,"Sorry, I only support text and emojis.")
            msg = bot.send_message(chat_id, "Choose your list:", reply_markup=markup)
            bot.register_next_step_handler(msg, lambda m : showList(m,data))
        else:
            bot.send_message(chat_id,"You have not created a list.")



@bot.message_handler(commands=['all'])
def all(message):
    chat_id = message.chat.id
    data = get_data(chat_id)
    if data:
        all_items =""
        for key in data.keys():
            all_items += key + " :\n"
            if getItems(key,data):
                all_items+= getItems(key,data)
                all_items += "\n"
            else:
                all_items += "Empty list. \n\n"
        
        bot.send_message(chat_id,all_items)
    else:
        bot.send_message(chat_id,"You have not created a list.")


@bot.message_handler(commands=['random'])
def list_to_random(message):
    chat_id = message.chat.id
    data = get_data(chat_id)
    markup = get_lists_markup(data)
    if markup.keyboard:
        msg = bot.send_message(chat_id,"Select the list you want to randomly chose from.",reply_markup=markup)
        bot.register_next_step_handler(msg,lambda m:chooseRandom(m,data))
    else:
        bot.send_message(chat_id,"You have not created a list.")

def chooseRandom(message,data):
    chat_id = message.chat.id
    if message.text:
        targetList = message.text
        if targetList in data: 
            if data[targetList]:
                random_item = random.choice(data[targetList])
                bot.send_message(chat_id,"- " + random_item)
            else:
                bot.send_message(chat_id,"This list is empty.")
        else:
            bot.send_message(chat_id,"This list does not exists.")
    else:
        markup = get_lists_markup(data)
        if markup.keyboard:
            bot.send_message(chat_id,"Sorry, I only support text and emojis.")
            msg = bot.send_message(chat_id,"Select the list you want to randomly chose from.",reply_markup=markup)
            bot.register_next_step_handler(msg,lambda m:chooseRandom(m,data))



@bot.message_handler(commands=['clear'])
def list_to_clear(message):
    chat_id = message.chat.id
    data = get_data(chat_id)
    markup  = get_lists_markup(data)
    if markup.keyboard:
        msg = bot.send_message(chat_id,"Select the list you want to clear.",reply_markup=markup)
        bot.register_next_step_handler(msg,lambda m:clearList(m,data))
    else:
        bot.send_message(chat_id,"You have not created a list.")


def clearList(message,data):
    chat_id = message.chat.id
    if message.text:
        targetList = message.text
        if targetList in data:
            if data[targetList]:
                data[targetList] = []
                save_data(chat_id,data)
                bot.send_message(chat_id,"The list has been cleared.")
            else:
                bot.send_message(chat_id,"This list is already empty.")
        else:
            bot.send_message(chat_id,"This list does not exists.")
    else:
        bot.send_message(chat_id,"Sorry, I only support text and emojis.")
        markup  = get_lists_markup(data)
        if markup.keyboard:
            msg = bot.send_message(chat_id,"Select the list you want to clear.",reply_markup=markup)
            bot.register_next_step_handler(msg,lambda m:clearList(m,data))
        
        
        

bot.polling()