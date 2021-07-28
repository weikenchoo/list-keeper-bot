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

def read_data(chatId):
    path = data_dir + str(chatId) + ".json"
    
    if os.path.isfile(path):
        with open(path, "r") as read_file:
            data = json.load(read_file)
    else:
        data = {}
        with open(path, "w") as write_file:
            json.dump(data, write_file)
    
    return data

def write_data(chatId,listName,newEntry=None):
    path = data_dir + str(chatId) + ".json"
    data = read_data(chatId=chatId)
    if listName in data:
        data[listName].append(newEntry)
        bot.send_message(chatId,"Added " + newEntry + " into " + listName + ".")
    else:
        if not newEntry:
            data[listName] = []
            bot.send_message(chatId,"Created list called "+ listName +".")
    
    with open(path, "w") as write_file:
        json.dump(data, write_file)

    

    

def remove_data(chatId,listName,removeItem):
    path = data_dir + str(chatId) + ".json"
    data = read_data(chatId)
    if data:
        if listName in data:
            if removeItem in data[listName]:
                data[listName].remove(removeItem)
                bot.send_message(chatId,"Successfully removed " + removeItem + " from "+ listName + ".")
            else:
                bot.send_message(chatId,"No such item in the list.")

    with open(path, "w") as write_file:
        json.dump(data, write_file)

def get_lists_markup(chatId):
    data = read_data(chatId)
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

@bot.message_handler(commands=['test'])
def test(message):
    chat_id = message.chat.id
    markup = types.ForceReply()
    msg = bot.send_message(chat_id, "Enter something other than text i dare you fcker.", reply_markup=markup)
    bot.register_next_step_handler(msg, test_input)

def test_input(message):
    if message.text:
        print(message.text)
        bot.send_message(message.chat.id,"Testing here")
    else:
        bot.send_message(message.chat.id,"I only support text la babi.")
        markup = types.ForceReply()
        msg = bot.send_message(message.chat.id, "Enter something other than text i dare you fcker.", reply_markup=markup)
        bot.register_next_step_handler(msg, test_input) 

def getItems(chatId,targetList):
    data = read_data(chatId)

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
        



@bot.message_handler(commands=['start', 'help',])
def send_welcome(message):
    bot.send_message(message.chat.id,"Hi "+message.from_user.first_name)
    # bot.reply_to(message, "Howdy, how are you doing?")


@bot.message_handler(commands=['add'])
def add(message):
    chat_id = message.chat.id
    markup = get_lists_markup(chat_id)
    msg = bot.send_message(chat_id, "Choose your list:", reply_markup=markup)
    bot.register_next_step_handler(msg, nameItem)

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
        write_data(chat_id,targetList,message.text)
    else:
        bot.send_message(chat_id,"Sorry, I only support text and emojis.")
        markup = types.ForceReply()
        msg = bot.send_message(chat_id, "Enter name for item to be added to the list.", reply_markup=markup)
        bot.register_next_step_handler(msg,lambda m : saveToList(m,targetList))


@bot.message_handler(commands=['remove'])
def remove(message):
    chat_id = message.chat.id
    markup = get_lists_markup(chat_id)
    msg = bot.send_message(chat_id, "Choose your list:", reply_markup=markup)
    bot.register_next_step_handler(msg, itemFromList)

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
            write_data(chat_id,targetList)
    else:
        bot.send_message(chat_id,"Sorry, I only support text and emojis.")
        markup = types.ForceReply()
        msg = bot.send_message(chat_id, "Enter name for the new list.", reply_markup=markup)
        bot.register_next_step_handler(msg,newList)


@bot.message_handler(commands=['delete'])
def delete(message):
    chat_id = message.chat.id
    markup = get_lists_markup(chat_id)
    msg = bot.send_message(chat_id, "Choose list to be deleted.", reply_markup=markup)
    bot.register_next_step_handler(msg,deleteList)

def deleteList(message):
    chat_id = message.chat.id
    if message.text:
        path = data_dir + str(chat_id) + ".json"
        data = read_data(chat_id)
        targetList = message.text
        if targetList in data:
            data.pop(targetList)
            with open(path, "w") as write_file:
                json.dump(data, write_file)
            bot.send_message(chat_id,targetList+" has been deleted.")
        else:
            bot.send_message(chat_id,targetList+" does not exist.")
    else:
        bot.send_message(chat_id,"Sorry, I only support text and emojis.")
        markup = get_lists_markup(chat_id)
        msg = bot.send_message(chat_id, "Choose list to be deleted.", reply_markup=markup)
        bot.register_next_step_handler(msg,deleteList)


@bot.message_handler(commands=['show'])
def show(message):
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
def choose_random(message):
    chat_id = message.chat.id
    data = read_data(chat_id)
    random_list = random.choice(list(data))
    random_item = random.choice(data[random_list])
    bot.send_message(chat_id,random_item + " from " + random_list + ".")
    

        
        
        




bot.polling()