from functools import wraps

import logging

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          RegexHandler,
                          ConversationHandler)

import settings

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)

# Steps
GROUP = 'group'
DATE = 'date'
LOCATION = 'location'
LINK = 'link'
DESCRIPTION = 'description'
CONFIRM = 'confirm'

MESSAGES = {
    'start': 'Boas! Son o Bot de VigoTech, axudaréite a'
             'publicar o evento no canle oficial de '
             'VigoTech. \n\n Envía /publicar para comezar a publicación. \n'
             'En calquer momento podes cancelar enviando'
             ' /cancelar ',
    'help': 'O Bot está en desenvolvemento. Envía /comezar para comezar',
    'publish': 'Imos comezar! '
               'Por favor, introduce o nome do teu grupo.',
    'group': '¡Grazas! Agora por favor introduce a data do '
             'evento (dd/MM/YY).',
    'date': 'Introduce o lugar do evento. Se todavía non '
            'está pechada podes omitir con /omitir',
    'location': '¡Grazas! Agora por favor introduce o enlace a '
                'web do evento',
    'skip_location': 'Ok, non te olvides de volver a anuncar o evento'
                     'cando teñas pechado o lugar! Agora por favor '
                     'introduce o enlace a información do evento',
    'link': '¡Grazas! Case terminamos. Introduze por favor unha breve '
            'descrición do evento (500 chars max). Se todavía non está '
            'pechada podes omitir con /omitir',
    'description': '¡Perfecto! ¿Queres publicar o evento?. Esta acción '
                   'publicará o evento no canle de VigoTech e non '
                   'se pode desfacer. Preme `non` en outro caso.',
    'skip_description': 'Ok, recorda que unha breve descrición sempre '
                        'e de interese '
                        '¿Queres publicar o evento?. Esta acción '
                        'publicará o evento no canle de VigoTech e non '
                        'se pode desfacer. Preme `non` en outro caso.',
    'confirm': '¡Grazas por publicar o teu evento! Podes velo '
               'en @VigoTech',
    'cancel': '¡Grazas! Espero ser de axuda a próxima vez.',
    'unknown': 'Disculpa non alcanzo a entender a tua mensaxe. ¿Podes envialo '
               'de novo?'

}


def get_message(command):
    return MESSAGES.get(command)


def restricted(func):
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in settings.TELEGRAM_ADMINS_LIST:
            print("Unauthorized access denied for {}.".format(user_id))
            return
        return func(bot, update, *args, **kwargs)

    return wrapped


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def cancel(bot, update):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(get_message('cancelar'),
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def description(bot, update, user_data):
    reply_keyboard = [['Si!', 'Non']]

    user = update.message.from_user
    logger.info("Event description %s by %s", update.message.text,
                user.first_name)
    update.message.reply_text(
        get_message('description'),
        reply_markup=ReplyKeyboardMarkup(reply_keyboard,
                                         one_time_keyboard=True))
    user_data['description'] = update.message.text

    return CONFIRM


def skip_description(bot, update):
    reply_keyboard = [['Si!', 'Non']]

    user = update.message.from_user
    logger.info("User %s did not send a description.", user.first_name)
    update.message.reply_text(
        get_message('skip_description'),
        reply_markup=ReplyKeyboardMarkup(reply_keyboard,
                                         one_time_keyboard=True))

    return CONFIRM


def send_publication(bot, update, user_data):
    user = update.message.from_user
    logger.info("%s wants to publish?: %s", user.first_name,
                update.message.text)
    logger.info("Userdata %s", user_data)

    update.message.reply_text(get_message('confirm'))

    return ConversationHandler.END


def reply_message(msg, next_step=None):
    @restricted
    def command(bot, update, user_data={}):
        user = update.message.from_user
        input_text = update.message.text
        logger.info("User %s sent %s data: %s ", user.first_name, msg,
                    input_text)

        user_data[msg] = input_text
        logger.info("Userdata %s", user_data)

        update.message.reply_text(get_message(msg))
        return next_step

    return command


def main():
    """Run bot."""
    updater = Updater(token=settings.TELEGRAM_BOT_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("comezar", reply_message('start')))
    dispatcher.add_handler(CommandHandler("axuda", reply_message('help')))

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('publicar', reply_message('publish', GROUP))],

        states={
            GROUP: [MessageHandler(Filters.text,
                                   reply_message('group', DATE),
                                   pass_user_data=True)],
            DATE: [
                MessageHandler(Filters.text,
                               reply_message('date', LOCATION),
                               pass_user_data=True)],
            LOCATION: [
                MessageHandler(Filters.text, reply_message('location', LINK),
                               pass_user_data=True),
                CommandHandler('omitir',
                               reply_message('skip_location', LINK))],
            LINK: [MessageHandler(Filters.text,
                                  reply_message('link', DESCRIPTION),
                                  pass_user_data=True)],
            DESCRIPTION: [MessageHandler(Filters.text, description,
                                         pass_user_data=True),
                          CommandHandler('omitir', skip_description)],
            CONFIRM: [RegexHandler('^(Si!|Non)$', send_publication,
                                   pass_user_data=True)],
        },

        fallbacks=[CommandHandler('cancelar', cancel)]
    )

    dispatcher.add_handler(conv_handler)

    # log all errors
    dispatcher.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
