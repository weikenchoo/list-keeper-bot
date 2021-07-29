import telebot
import json
import os
from dotenv import load_dotenv
from telebot import types
import random

load_dotenv()
token = os.getenv('API_TOKEN')
bot = telebot.TeleBot(token, parse_mode=None)

data_dir = "data/"

def read_data(chat_id):
    if not os.path.isdir(data_dir):
        os.mkdir(data_dir)
    
    path = data_dir + str(chat_id) + ".json"
    
    if os.path.isfile(path):
        with open(path, "r") as read_file:
            data = json.load(read_file)
    else:
        data = {}
        with open(path, "w") as write_file:
            json.dump(data, write_file)
    
    return data

def add_to_dict(chat_id,listName,newEntry=None):
    data = read_data(chat_id=chat_id)
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

def remove_data(chat_id,listName,removeItem):
    data = read_data(chat_id)
    if data:
        if listName in data:
            if removeItem in data[listName]:
                data[listName].remove(removeItem)
                bot.send_message(chat_id,"Successfully removed " + removeItem + " from "+ listName + ".")
            else:
                bot.send_message(chat_id,"No such item in the list.")
    save_data(chat_id,data)

def get_lists_markup(chat_id):
    data = read_data(chat_id)
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

def get_items_markup(chat_id,targetList):
    data = read_data(chat_id)
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


def getItems(chat_id,targetList):
    data = read_data(chat_id)
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
    markup = get_lists_markup(chat_id)
    if markup.keyboard:
        msg = bot.send_message(chat_id, "Choose your list:", reply_markup=markup)
        bot.register_next_step_handler(msg, nameItem)
    else:
        bot.send_message(chat_id,"You have not created a list.")

def nameItem(message):
    chat_id = message.chat.id
    if message.text:
        targetList = message.text
        data = read_data(chat_id)
        if targetList in data:
            markup = types.ForceReply()
            msg = bot.send_message(chat_id, "Enter name for item to be added to the list.", reply_markup=markup)
            bot.register_next_step_handler(msg,lambda m : saveToList(m,targetList))
        else:
            bot.send_message(chat_id,"The list " + targetList + " has not been created.")
    else:
        bot.send_message(chat_id,"Sorry, I only support text and emojis.")
        markup = get_lists_markup(chat_id)
        msg = bot.send_message(chat_id, "Choose your list:", reply_markup=markup)
        bot.register_next_step_handler(msg, nameItem)

def saveToList(message,targetList):
    chat_id = message.chat.id
    if message.text:
        add_to_dict(chat_id,targetList,message.text)
    else:
        bot.send_message(chat_id,"Sorry, I only support text and emojis.")
        markup = types.ForceReply()
        msg = bot.send_message(chat_id, "Enter name for item to be added to the list.", reply_markup=markup)
        bot.register_next_step_handler(msg,lambda m : saveToList(m,targetList))


@bot.message_handler(commands=['remove'])
def list_to_remove(message):
    chat_id = message.chat.id
    markup = get_lists_markup(chat_id)
    if markup.keyboard:
        msg = bot.send_message(chat_id, "Choose your list:", reply_markup=markup)
        bot.register_next_step_handler(msg, itemFromList)
    else:
        bot.send_message(chat_id,"You have not created a list.")

def itemFromList(message):
    chat_id = message.chat.id
    if message.text:
        targetList = message.text
        all_items = getItems(chat_id,targetList)
        if not all_items:
            bot.send_message(chat_id,"This list is empty or does not exist.")
        else:
            bot.send_message(chat_id,all_items)
            markup = get_items_markup(chat_id,targetList)
            msg = bot.send_message(chat_id, "Choose item to be removed from the list.", reply_markup=markup)
            bot.register_next_step_handler(msg,lambda m:removeFromList(m,targetList,all_items))
    else:
        bot.send_message(chat_id,"Sorry, I only support text and emojis.")
        markup = get_lists_markup(chat_id)
        msg = bot.send_message(chat_id, "Choose your list:", reply_markup=markup)
        bot.register_next_step_handler(msg, itemFromList)

def removeFromList(message,targetList,all_items):
    chat_id = message.chat.id
    if message.text:
        remove_data(chat_id,targetList,message.text)
    else:
        bot.send_message(chat_id,"Sorry, I only support text and emojis.")
        bot.send_message(chat_id,all_items)
        markup = get_items_markup(chat_id,targetList)
        msg = bot.send_message(chat_id, "Choose item to be removed from the list.", reply_markup=markup)
        bot.register_next_step_handler(msg,lambda m:removeFromList(m,targetList,all_items))
        



@bot.message_handler(commands=['new'])
def new(message):
    chat_id = message.chat.id
    markup = types.ForceReply()
    msg = bot.send_message(chat_id, "Enter name for the new list.", reply_markup=markup)
    bot.register_next_step_handler(msg,newList)

def newList(message):
    chat_id = message.chat.id
    if message.text:
        data = read_data(chat_id)
        targetList = message.text
        if targetList in data:
            bot.send_message(chat_id,"This list already exists.")
        else:
            add_to_dict(chat_id,targetList)
    else:
        bot.send_message(chat_id,"Sorry, I only support text and emojis.")
        markup = types.ForceReply()
        msg = bot.send_message(chat_id, "Enter name for the new list.", reply_markup=markup)
        bot.register_next_step_handler(msg,newList)


@bot.message_handler(commands=['delete'])
def list_to_delete(message):
    chat_id = message.chat.id
    markup = get_lists_markup(chat_id)
    if markup.keyboard:
        msg = bot.send_message(chat_id, "Choose list to be deleted.", reply_markup=markup)
        bot.register_next_step_handler(msg,deleteList)
    else:
        bot.send_message(chat_id,"You have not created a list.")

def deleteList(message):
    chat_id = message.chat.id
    if message.text:
        data = read_data(chat_id)
        targetList = message.text
        if targetList in data:
            data.pop(targetList)
            save_data(chat_id,data)
            bot.send_message(chat_id,targetList+" has been deleted.")
        else:
            bot.send_message(chat_id,targetList+" does not exist.")
    else:
        bot.send_message(chat_id,"Sorry, I only support text and emojis.")
        markup = get_lists_markup(chat_id)
        msg = bot.send_message(chat_id, "Choose list to be deleted.", reply_markup=markup)
        bot.register_next_step_handler(msg,deleteList)


@bot.message_handler(commands=['show'])
def list_to_show(message):
    chat_id = message.chat.id
    markup = get_lists_markup(chat_id)
    data = read_data(chat_id)
    if data:
        msg = bot.send_message(chat_id, "Choose your list:", reply_markup=markup)
        bot.register_next_step_handler(msg, showList)
    else:
        bot.send_message(chat_id,"You have not created a list.")
    
def showList(message):
    chat_id = message.chat.id
    if message.text:
        targetList = message.text
        all_items = getItems(chat_id,targetList)
        if not all_items:
            bot.send_message(chat_id,"This list is empty.")
        else:
            bot.send_message(chat_id,targetList+" :")
            bot.send_message(chat_id,all_items)
    else:
        markup = get_lists_markup(chat_id)
        data = read_data(chat_id)
        if data:
            bot.send_message(chat_id,"Sorry, I only support text and emojis.")
            msg = bot.send_message(chat_id, "Choose your list:", reply_markup=markup)
            bot.register_next_step_handler(msg, showList)
        else:
            bot.send_message(chat_id,"You have not created a list.")



@bot.message_handler(commands=['all'])
def all(message):
    chat_id = message.chat.id
    data = read_data(chat_id)
    if data:
        all_items =""
        for key in data.keys():
            all_items += key + " :\n"
            if getItems(chat_id,key):
                all_items+= getItems(chat_id,key)
                all_items += "\n"
            else:
                all_items += "Empty list. \n\n"
        
        bot.send_message(chat_id,all_items)
    else:
        bot.send_message(chat_id,"You have not created a list.")


@bot.message_handler(commands=['random'])
def list_to_random(message):
    chat_id = message.chat.id
    markup = get_lists_markup(chat_id)
    if markup.keyboard:
        msg = bot.send_message(chat_id,"Select the list you want to randomly chose from.",reply_markup=markup)
        bot.register_next_step_handler(msg,chooseRandom)
    else:
        bot.send_message(chat_id,"You have not created a list.")

def chooseRandom(message):
    chat_id = message.chat.id
    if message.text:
        targetList = message.text
        data = read_data(chat_id)
        if targetList in data: 
            if data[targetList]:
                random_item = random.choice(data[targetList])
                bot.send_message(chat_id,"- " + random_item)
            else:
                bot.send_message(chat_id,"This list is empty.")
        else:
            bot.send_message(chat_id,"This list does not exists.")
    else:
        markup = get_lists_markup(chat_id)
        if markup.keyboard:
            bot.send_message(chat_id,"Sorry, I only support text and emojis.")
            msg = bot.send_message(chat_id,"Select the list you want to randomly chose from.",reply_markup=markup)
            bot.register_next_step_handler(msg,chooseRandom)



@bot.message_handler(commands=['clear'])
def list_to_clear(message):
    chat_id = message.chat.id
    markup  = get_lists_markup(chat_id)
    if markup.keyboard:
        msg = bot.send_message(chat_id,"Select the list you want to clear.",reply_markup=markup)
        bot.register_next_step_handler(msg,clearList)
    else:
        bot.send_message(chat_id,"You have not created a list.")


def clearList(message):
    chat_id = message.chat.id
    if message.text:
        targetList = message.text
        data = read_data(chat_id)
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
        markup  = get_lists_markup(chat_id)
        if markup.keyboard:
            msg = bot.send_message(chat_id,"Select the list you want to clear.",reply_markup=markup)
            bot.register_next_step_handler(msg,clearList)
        
        
        

bot.polling()