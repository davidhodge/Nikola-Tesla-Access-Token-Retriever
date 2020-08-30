import teslajson
import getpass
import urllib3

while True:
    print("Welcome to the Nikola token retriever! This script allows you to send us at Nikola a Tesla auth token. If you're not sure what this is, we recommend authenticating directly in to Nikola App Instead")
    tesla_email = input("Input your email address for your Tesla Account: ")
    tesla_password = getpass.getpass("Input your password for your Tesla Account: ")

    try:
        connection = teslajson.Connection(email=tesla_email, password=tesla_password)
        print("Great! We've authenticated this account with Tesla.")

        print("Please send the information text to Nikola (David Hodge) securely.")
        print("Tesla Email Address: " + tesla_email)
        print("Tesla Acces Token: " + connection.access_token + " This will be revoked whenever your account password is changed.")
        print("Tesla Refresh Token: " + connection.auth_dict['refresh_token'] + " We will use this to update your credentials in the future. This will be revoked whenever your account password is changed.")
        break

    except urllib3.exceptions.HTTPError as err:
        if err.code == 401:
            print("Unauthorized. We were unable to connect to Tesla on your behalf. Please try again. We're looking for the credentials you use to log in to Tesla's website. If you continue to encounter issues, try resetting your MyTesla password via the official Tesla App.\n\n")
        else:
            print("Http Error. %s. Try again?\n\n" % err)
    except Exception as err:
        print("Error %s. Try again" % err)
