#Bot de Telegram para buscar y agendar cita en el SAT

from selenium import webdriver
from selenium.webdriver.common.by import By  
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
from datetime import datetime
from datetime import timedelta
import time
import os
import sys
import cv2
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

TOKEN = "1616265768:AAFn6-0KZ5OQbhroK2VdcUpivh76khumbz4"
DRIVER_PATH = '/usr/lib/chromium-browser/chromedriver'
driver = webdriver.Chrome(executable_path=DRIVER_PATH)
driver.get('https://citas.sat.gob.mx/citasat/agregarcita.aspx')
driver.maximize_window()

filled_form = {
    "modulo": "ArbolAdministracionest101",
    "service": "RBLServicios_3",
    "nombre_completo": "Julio Augusto Sanchez Garcia",
    "rfc": "SAGJ9502239D7",
    "email": "13121096@tecmor.mx",
    "home_phone": "",
    "mobile_phone": "4436828499",
}

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi!')

def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')

def echo(update, context):
    """Echo the user message."""
    update.message.reply_text(update.message.text)

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    
def cita(update, context):
    try:
        update.message.reply_text("Arre, deja ver qué pedo")        
        sacarcita()
    except:
        update.message.reply_text("No se pudo, carnal. \n Aber otra vez")
        
def fillResponsiveField(selector, value):
    responsiveField = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.ID, selector))
    )
    responsiveField.clear()
    time.sleep(1)
    responsiveField.send_keys("")
    time.sleep(1)
    responsiveField = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.ID, selector))
    )
    responsiveField.send_keys(value)
    time.sleep(1)
    nameField = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.ID, "TXTNombreContribuyente"))
    )

    nameField.send_keys("")
    time.sleep(3)

def fillForm():
    """    Fills form    """
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.ID, "TXTNombreContribuyente"))
    )
    fillResponsiveField("TXTNombreContribuyente", filled_form["nombre_completo"])
    fillResponsiveField("TXTRFC", filled_form["rfc"])
    fillResponsiveField("TXTCorreoElectronico", filled_form["email"])
    fillResponsiveField("TXTCelular", filled_form["mobile_phone"])
    print("Filling form")
    
def getCaptchaImage():
    driver.save_screenshot('captcha.png')
    image = cv2.imread('captcha.png')
    image = image[220:320, 370:570]
    cv2.imwrite('captching.png', image)
    
def sendCaptcha():
    imageCaptcha = cv2.imread('captching.png')
    context.bot.send_photo(chat_id=update.effective_chat.id, photo = ImageCaptcha)
    
def sacarcita():
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, filled_form["modulo"]))
        )
        time.sleep(1)
        javaScript = "document.getElementById('"+filled_form["modulo"]+"').click()"
        print(javaScript)
        driver.execute_script(javaScript)
        time.sleep(1)
        javaScript = "window.scrollBy(0,700)"
        driver.execute_script(javaScript)
        time.sleep(1)
        javaScript = "document.getElementById('"+filled_form["service"]+"').click()"
        driver.execute_script(javaScript)
        print(javaScript)
        time.sleep(1)

        resolvingCaptcha = True
        
        while resolvingCaptcha:
            try:
                driver.find_element_by_id("captchaWrapper")
                resolvingCaptcha = True
            except:
                resolvingCaptcha = False
                
            getCaptchaImage()
            sendCaptcha()
            fillResponsiveField("txtUserInput", update.message.text)
            driver.find_element_by_id('cmdSiguiente').click()
            time.sleep(3)
            with open('scripts/removeModal.js', 'r') as file:
                driver.execute_script(file.read())
        
        fillForm()

        datesNotAvailable = True
        availableDates = None
        currentMonth = True
        contador = 0
        
        horaInicial= datetime.now()
        update.message.reply_text("Buscando cita")
        print(horaInicial)
        
        while datesNotAvailable:
            if contador > 50:
                time.sleep(300)
                contador = 0
                driver.refresh()
                print("refrescanding pagina")
            else:
                contador = contador+1
                print(contador)
            with open('scripts/removeModal.js', 'r') as file:
                driver.execute_script(file.read())
            print('esperando fecha disponible')
            try:
                calendarTable = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "Calendario"))
                )
            except:
                try:
                    fillForm()
                except:
                    driver.refresh()
                    continue
                continue

            availableDates = calendarTable.find_elements_by_css_selector(
                "#Calendario > tbody > tr > td > a")
            if len(availableDates) > 0:
                datesNotAvailable = False
            else:
                print('cargando nuevo calendario')
                if currentMonth:
                    javaScript = "document.querySelector(\"a[title='Go to the previous month']\").click()"
                    currentMonth = False
                else:
                    javaScript = "document.querySelector(\"a[title='Go to the next month']\").click()"
                    currentMonth = True
                driver.execute_script(javaScript)
                time.sleep(3)

        driver.save_screenshot('found.png')

        print(list(map(lambda date: date.get_attribute('title'), availableDates)))
        closestDate = availableDates[0]
        print(closestDate.get_attribute('title'))
        closestDate.click()

        time.sleep(2)

        select_element = driver.find_element(By.ID, 'DDLHorariosModulo')
        select_object = Select(select_element)
        all_available_options = select_object.options
        print(list(map(lambda time: time.text, all_available_options)))
        select_object.select_by_index(1)

        time.sleep(2)

        driver.find_element_by_id('cmdSolicitarCita').click()
        time.sleep(1)

        with open('scripts/acceptAppointment.js', 'r') as file:
            driver.execute_script(file.read())

        time.sleep(30)
        driver.save_screenshot('final.png')
        message = "Cita agendada"
        print(message)
        update.message.reply_text(message)
    finally:
        time.sleep(3)
        message = "Cita NO agendada"
        print(message)
        update.message.reply_text(message)
        horaFinal= datetime.now()
        tiempo = (horaFinal-horaInicial)
        notify(str(tiempo))
        print("El script ha corrido por: ")
        print (tiempo)
        driver.save_screenshot('FAIL.png')
        driver.quit()

        

def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("sacarcita", sacarcita))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
