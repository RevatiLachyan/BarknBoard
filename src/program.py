from colorama import Fore
import program_guests
import program_hosts
import data.mongo_setup as mongo_setup


def main():
    mongo_setup.global_init()

    print_header()

    try:
        while True:
            if find_user_intent() == 'book':
                program_guests.run()
            else:
                program_hosts.run()
    except KeyboardInterrupt:
        return


def print_header():
    BROWN = '\033[38;5;94m'
    RESET = '\033[0m'

    dog = f'''
    {BROWN} / \\__
    (    @\\___
     /         O
    /   (_____/
    /_____/ U{RESET}
    '''

    print(Fore.WHITE + '**************** Bark n Board ****************')
    print(dog)
    print(Fore.WHITE + '*********************************************')
    print()
    print("Welcome to Bark n Board!")
    print('....for a tail-waggingly good time :P')
    print("How can we help you?")
    print()


def find_user_intent():
    print("[g] Book a kennel for your dog")
    print("[h] Host your kennel space")
    print()
    choice = input("Are you a [g]uest or [h]ost? ")
    if choice == 'h':
        return 'offer'

    return 'book'


if __name__ == '__main__':
    main()
