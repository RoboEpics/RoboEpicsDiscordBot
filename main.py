import os
import logging

import requests

import discord
from discord import ui

BOT_TOKEN = os.getenv('BOT_TOKEN')
ROBOEPICS_GUILD = discord.Object(os.getenv('GUILD_ID') or 683685547893325829)  # Default value is the test guild
ROBOEPICS_API = os.getenv('ROBOEPICS_API') or 'https://api.roboepics.com'
LOG_PATH = os.getenv('LOG_PATH') or 'discord.log'

handler = logging.FileHandler(filename=LOG_PATH, encoding='utf-8', mode='w')


class RoboEpicsBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self):
        # Sync the bot commands with the RoboEpics guild
        self.tree.copy_global_to(guild=ROBOEPICS_GUILD)
        await self.tree.sync(guild=ROBOEPICS_GUILD)

    async def on_ready(self):
        print(f'Logged on as {self.user}!')


class RegisterForm(ui.Modal, title='RoboEpics register form'):
    full_name = ui.TextInput(label='Full Name')
    username = ui.TextInput(label='Username')
    email = ui.TextInput(label='Email')
    password = ui.TextInput(label='Password')

    async def on_submit(self, interaction: discord.Interaction):
        # Inform Discord that the response will be delayed since the registration request might take some time
        await interaction.response.defer()

        # Send the registration request
        response = requests.post(ROBOEPICS_API + '/account/register', {
            'full_name': self.full_name,
            'username': self.username,
            'email': self.email,
            'password': self.password,
            'discord_user_id': interaction.user.id,
            'tags': ['discord']
        })

        # Send a delayed follow-up response in the guild but only to the user
        await interaction.followup.send(
            f'Your registration form has been submitted, {self.full_name}! Please check your direct messages for confirmation.',
            ephemeral=True
        )

        # Handle the registration request result
        if response.ok:
            await interaction.user.send(f"Thanks for your registration in RoboEpics, {self.full_name}! Please check your email as we've sent you a verification link.")
        elif response.status_code == 400:
            await interaction.user.send('\n'.join(('%s:\n\t%s' % (field, '\n\t'.join(errors)) for field, errors in response.json().items())))
        else:
            await interaction.user.send('There was a problem with your registration! Please try again later.')


class LoginForm(ui.Modal, title='RoboEpics login form'):
    username = ui.TextInput(label='Username')
    password = ui.TextInput(label='Password')

    async def on_submit(self, interaction: discord.Interaction):
        # Send a confirmation response in the guild but only to the user
        await interaction.response.send_message(
            f'Discord user connection request has been submitted! Please check your direct messages for confirmation.',
            ephemeral=True
        )

        # Login to RoboEpics using the credentials
        response = requests.post(ROBOEPICS_API + '/account/login', {
            'username': self.username,
            'password': self.password
        })

        # Handle the login request result
        if response.ok:
            # Extract access token from the login response
            token = response.json()['access_token']

            # Set user's Discord ID in profile
            response = requests.patch(ROBOEPICS_API + '/profile', {'discord_user_id': interaction.user.id}, headers={'Authorization': 'Bearer ' + token})
            if response.ok:
                await interaction.user.send('Your Discord user is successfully connected to your RoboEpics user!')
            else:
                await interaction.user.send('There was a problem with your request! Please try again later.')
        elif response.status_code == 400:
            await interaction.user.send('The given username or password is wrong!')
        else:
            await interaction.user.send('There was a problem with your login! Please try again later.')


client = RoboEpicsBot()


@client.tree.command(name='register', description='Registers an account to RoboEpics.')
async def register(interaction: discord.Interaction):
    await interaction.response.send_modal(RegisterForm())


@client.tree.command(name='connect', description='Connects your Discord user to your RoboEpics user by logging in.')
async def connect(interaction: discord.Interaction):
    await interaction.response.send_modal(LoginForm())


@client.tree.command(name='whois', description='Gives you the RoboEpics username corresponding to this Discord user.')
async def whois(interaction: discord.Interaction, discord_user: discord.Member):
    response = requests.get(ROBOEPICS_API + '/account/users/discord/' + str(discord_user.id))
    if response.ok:
        await interaction.response.send_message('Username: %(username)s\nProfile URL: https://roboepics.com/user/%(username)s' % response.json())
    else:
        await interaction.response.send_message('No user was found that is connected to this Discord user!', ephemeral=True)


if __name__ == '__main__':
    client.run(BOT_TOKEN, log_handler=handler, log_level=logging.DEBUG)
