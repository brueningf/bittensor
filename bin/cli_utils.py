from argparse import ArgumentParser
import json
import sys
import os
import stat
from password_strength import PasswordPolicy
import getpass

from loguru import logger

from bittensor.subtensor.interface import Keypair
from bittensor.crypto.keyfiles import load_keypair_from_data, KeyFileError
from termcolor import colored
from bittensor.crypto import encrypt, is_encrypted, decrypt_data, KeyError
from bittensor.subtensor.client import WSClient
from bittensor.utils import Cli

class cli_utils():

    @staticmethod
    def load_key(path) -> Keypair:
        path = os.path.expanduser(path)
        try:
            with open(path, 'rb') as file:
                data = file.read()
                if is_encrypted(data):
                    password = Cli.ask_password()
                    logger.info("decrypting key... (this may take a few moments)")
                    data = decrypt_data(password, data)

                return load_keypair_from_data(data)

        except KeyError:
            logger.error("Invalid password")
            quit()
        except KeyFileError as e:
            logger.error("Keyfile corrupt")
            raise e

    @staticmethod
    def get_client(endpoint, keypair):
        return WSClient(socket=endpoint, keypair=keypair)

    @staticmethod
    def enable_debug(should_debug):
        if not should_debug:
            logger.remove()
            logger.add(sink=sys.stderr, level="INFO")

    @staticmethod
    def create_config_dir_if_not_exists():
        config_dir = "~/.bittensor"
        config_dir = os.path.expanduser(config_dir)
        if os.path.exists(config_dir):
            if os.path.isdir(config_dir):
                return
            else:
                print(colored("~/.bittensor exists, but is not a directory. Aborting", 'red'))
                quit()
        os.mkdir(config_dir)

    @staticmethod
    def may_overwrite( file:str ):
        choice = input("File %s already exists. Overwrite ? (y/N) " % file)
        if choice == "y":
            return True
        else:
            return False

    @staticmethod
    def validate_path(path):
        path = os.path.expanduser(path)

        if not os.path.isfile(path):
            logger.error("{} is not a file. Aborting", path)
            quit()

        if not os.access(path, os.R_OK):
            logger.error("{} is not readable. Aborting", path)
            quit()

    @staticmethod
    def validate_create_path( keyfile ):
        keyfile = os.path.expanduser(keyfile)

        if os.path.isfile(keyfile):
            if os.access(keyfile, os.W_OK):
                if cli_utils.may_overwrite( keyfile ):
                    return keyfile
                else:
                    quit()
            else:
                print(colored("No write access for  %s" % keyfile, 'red'))
                quit()
        else:
            pdir = os.path.dirname(keyfile)
            if os.access(pdir, os.W_OK):
                return keyfile
            else:
                print(colored("No write access for  %s" % keyfile, 'red'))
                quit()

    @staticmethod
    def write_pubkey_to_text_file( keyfile, pubkey_str:str ):
        keyfile = os.path.expanduser(keyfile)
        with open(keyfile + "pub.txt", "w") as pubfile:
            pubfile.write(pubkey_str)

    @staticmethod
    def input_password():
        valid = False
        while not valid:
            password = getpass.getpass("Specify password for key encryption: ")
            valid = cli_utils.validate_password(password)

        return password

    @staticmethod
    def validate_password(password):
        policy = PasswordPolicy.from_names(
            strength=0.66,
            entropybits=30,
            length=8,
        )
        if not password:
            return False

        tested_pass = policy.password(password)
        result = tested_pass.test()
        if len(result) > 0:
            print(colored('Password not strong enough. Try increasing the length of the password or the password comlexity'))
            return False

        password_verification = getpass.getpass("Retype your password: ")
        if password != password_verification:
            print("Passwords do not match")
            return False

        return True
    
    @staticmethod
    def validate_generate_mnemonic(mnemonic):
        if len(mnemonic) not in [12,15,18,21,24]:
            print(colored("Mnemonic has invalid size. This should be 12,15,18,21 or 24 words", 'red'))
            quit()

        try:
            keypair = Keypair.create_from_mnemonic(" ".join(mnemonic))
            return keypair
        except ValueError as e:
            print(colored(str(e), "red"))
            quit()

    @staticmethod
    def gen_new_key(words):
        mnemonic = Keypair.generate_mnemonic(words)
        keypair = Keypair.create_from_mnemonic(mnemonic)
        return keypair

    @staticmethod
    def display_mnemonic_msg( kepair : Keypair ):
        mnemonic = kepair.mnemonic
        mnemonic_green = colored(mnemonic, 'green')
        print (colored("\nIMPORTANT: Store this mnemonic in a secure (preferable offline place), as anyone " \
                    "who has possesion of this mnemonic can use it to regenerate the key and access your tokens. \n", "red"))
        print ("The mnemonic to the new key is:\n\n%s\n" % mnemonic_green)
        print ("You can use the mnemonic to recreate the key in case it gets lost. The command to use to regenerate the key using this mnemonic is:")
        print("bittensor-cli regen --mnemonic %s" % mnemonic)
        print('')


    @staticmethod
    def save_keys(path, data):
        print("Writing key to %s" % path)
        with open(path, "wb") as keyfile:
            keyfile.write(data)
    
    @staticmethod
    def set_file_permissions(path):
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
        pass

    @staticmethod
    def confirm_no_password():
        print(colored('*** WARNING ***', 'white'))
        print(colored('You have not specified the --password flag.', 'white'))
        print(colored('This means that the generated key will be stored as plaintext in the keyfile', 'white'))
        print(colored('The benefit of this is that you will not be prompted for a password when bittensor starts', 'white'))
        print(colored('The drawback is that an attacker has access to the key if they have access to the account bittensor runs on', 'white'))
        print()
        choice = input("Do you wish to proceed? (Y/n) ")
        if choice in ["n", "N"]:
            return False

        return True