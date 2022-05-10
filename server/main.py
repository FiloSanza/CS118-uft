from command_handler import *

def main():
    handler = CommandHandler(Commands.GET, ["yes.txt"])
    res = handler.handle()
    print(res)

if __name__ == '__main__':
    main()