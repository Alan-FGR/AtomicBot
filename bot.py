import urllib.request
from gitterpy.client import GitterClient
from json import loads
from random import randint
import threading
import sys


#CONFS
room_name = 'gitterHQ/sandbox'
# room_name = 'AtomicGameEngine/AtomicGameEngine'
moderators = ["CTrauma", "mattbenic", "darrylryan", "Alan-FGR"]
allowed_bad_words = ["shit", "crap", "poop"]
server_port = -1
EMULATE = False

if len(sys.argv) > 1:
    try:
        server_port = sys.argv[1]
    except:
        print("""Usage: python bot.py server_port. '-1' disables server.
         If server is disable data is dumped to file so you can use free hosting for stats :P""")
        quit()



commands = {
    'help': lambda: say("available commands: "+", ".join(commands)),
    'flip/coin/flipcoin': lambda q = [1]: say(", ".join(["heads" if randint(0,1) == 1 else "tails" for _ in range(int(q[0]))])),
    'roll/dice/rolldice': lambda q = [1]: say(", ".join([str(randint(1,6)) for _ in range(int(q[0]))])),
    'duel/pickone': lambda ps: say(ps[randint(0,len(ps)-1)]),
    'infractors': lambda: say(infractors)
}

#===================NON-LAMBDA COMMANDS=========================

def find_match(args, dict):
    for arg in args:
        for key_group in dict:
            keys = key_group.split("/")
            for key in keys:
                if key in arg:
                    if dict[key_group][0] == '>':
                        say("["+keys[0].capitalize()+"]("+dict[key_group][1:]+")")
                    else:
                        say(dict[key_group])
                    return True

what_matches = {
    'suck/sux': "Everything Sucks!",
    'urho': "[Urho3d](https://urho3d.github.io) is the engine Atomic was forked from",
    'quaternion/quater':'>https://en.wikipedia.org/wiki/Quaternion',
    'vector/vect':'>https://en.wikipedia.org/wiki/Vector_space',
}
def what(args):
    if not find_match(args, what_matches):
        where(args) #falls back to where :P
commands['what'] = what

where_matches = {
    'docs/docum': "Here are some docs: [C++](http://docs.atomicgameengine.com/cpp), [C#](http://docs.atomicgameengine.com/csharp/AtomicEngine/), [wiki](https://github.com/AtomicGameEngine/AtomicGameEngine/Wiki). Urho docs could be helpful too, as well as Urho keyword for Googling",
    'forum': ">https://discourse.atomicgameengine.com/",
    'log/stat': "[Channel Logs](https://discourse.atomicgameengine.com/), [Channel Stats](https://alan-fgr.github.io/AtomicGitterLog/stats)",
}
def where(args):
    find_match(args, where_matches)
commands['where/how'] = where


#==============================================================



#WORKING VARS
read_this_session = [0]



#FETCH ONLINE DATA
bad_words_data  = urllib.request.urlopen('https://raw.githubusercontent.com/MauriceButler/badwords/master/array.js')
bad_words = (loads(str(bad_words_data.read(), 'utf-8')[16:-1]))
bad_words = [x for x in bad_words if x not in allowed_bad_words]


#WEBSERVER
if server_port >= 0:
    from wsgiref.simple_server import make_server
    def application(environ, start_response):
        start_response("200 OK", [("Content-type", "text/plain")])
        return [str("""BOT ONLINE!"""+get_stats()).encode("utf-8")]
    print("starting server")
    server = make_server('localhost', server_port, application)
    threading.Thread(target=server.serve_forever).start()







last_message = ""
infractors = {} # if user has too high infraction ratio, we gotta do something about it

def say(msg):
    if EMULATE:
        print(">> " + str(msg))
    else:
        gitter.messages.send(room_name, str(msg))

def register_infraction(usr):
    if usr not in infractors:
        infractors[usr] = 1
    else:
        infractors[usr] +=1
        if infractors[usr] >= 3:
            ping_all_mods("too many infractions from "+usr)

def cooldown_infractions():
    detrack_list = []
    for name in infractors:
        infractors[name] -= 1 #TODO: don't remember if dir val is val type in python
        if infractors[name] <= 0:
            detrack_list.append(name)
    for k in detrack_list:
        infractors.pop(k, None)

def process_message(usr, msg):
    if not process_bad_words(usr, msg):
        cooldown_infractions()
        process_command(msg)
    if server_port < 0:
        open('stats', 'w+').write(get_stats())

def process_bad_words(usr, msg):
    for word in msg.split(" "):
        if word in bad_words:
            register_infraction(usr)
            say(usr+" let's keep the conversation polite here please")
            return True

def ping_all_mods(txt = ''):
    say(", ".join(["@"+m for m in moderators])+" something needs your attention"+((": "+txt) if txt != '' else '!'))

def get_args(text):
    return text.split(' ')[1:]

def process_command(msg):
    command = message.split(' ')[0].lower()
    args = get_args(msg)
    for available_command in commands:
        if command in available_command.split("/"):
            try:
                commands[available_command](args)
            except:
                commands[available_command]()

def get_stats():
    return """
    MESSAGES READ THIS SESSION: """+str(read_this_session[0])+"""
    INFRACTORS: """+str(infractors)+"""
    COMMANDS: """+str([x for x in commands])+"""
    WHAT I KNOW: """+str([x for x in what_matches]+[x for x in where_matches])+"""
    """


# TESTING
if EMULATE:
    while True:
        try:
            message = input("> ")
            last_message = message
            process_message("Alan-FRG", message)
        except Exception as e:
            print(str(e))



#GITTER CLIENT
print('initting client')
gitter = GitterClient(open("token.txt").readline())


#join room if necessary (has to check otherwise shit happens)
current_rooms = gitter.rooms_list
is_in_room = False
for room in current_rooms:
    if room['name'] == room_name:
        print('already in room')
        is_in_room = True
        break
if not is_in_room:
    print('joining room')
    gitter.rooms.join(room_name)


bot_name = gitter.user.current_user[0]['username']

print('initting stream')
stream = gitter.stream.chat_messages(room_name)

print('introducing bot')
say("Hello. I'm a utility robot. I'll help users when I can and censor bad words.")

print('starting streaming')
mark_interval = 3
for bytes in stream.iter_lines():
    if bytes:
        try:
            read_this_session[0]+=1
            response = loads(str(bytes, 'utf-8'))
            message = response['text']
            sender = response['fromUser']['username']
            if sender != bot_name:
                last_message = message
                process_message(sender, message)
                if read_this_session[0]%mark_interval == 0:
                    gitter.user.mark_as_read(room_name)
        except Exception as e:
            print(str(e))

