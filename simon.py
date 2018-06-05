import time
import sys
from Adafruit_GPIO.GPIO import (
    get_platform_gpio,
    FALLING,
    IN, OUT,
    LOW,
    PUD_OFF,
)
from threading import Lock, Thread


def clean_buttons():
    gpio = get_platform_gpio()
    gpio.cleanup()
    for pin in [14, 15, 18, 23, 24, 25, 8, 7, 12, 16, 20, 21,
                2, 3, 4, 17, 27, 22, 10, 9, 11, 5, 6, 13, 19, 26]:
        gpio.setup(pin, IN, PUD_OFF)


class Simon(object):
    ROJO = 'R'
    AZUL = 'A'
    VERDE = 'V'
    NARANJA = 'N'

    FIN = 0
    ESCUCHANDO = 1
    REPITIENDO = 2

    def __init__(self):
        self.pulsaciones = []
        self.posicion_actual = 0
        self.estado = self.FIN
        self.sync_lock = Lock()

    def add(self, color):
        self.pulsaciones.append(color)

    def empezar(self):
        self.pulsaciones = []
        self.posicion_actual = 0
        self.estado = self.ESCUCHANDO

    def oido(self, color):
        if self.estado == self.ESCUCHANDO:
            sys.stdout.write(color)
            sys.stdout.flush()
            try:
                if self.pulsaciones[self.posicion_actual] == color:
                    self.posicion_actual += 1
                else:
                    self.estado = self.FIN
            except IndexError:
                self.add(color)
                self.posicion_actual = 0
                self.estado = self.REPITIENDO
                sys.stdout.write('-\n')
                sys.stdout.flush()
        elif self.estado == self.REPITIENDO:
            sys.stdout.write(color)
            sys.stdout.flush()
            self.sync_lock.release()
        else:
            sys.stderr.write("Estado {}({})\n".format(self.estado, color))
            sys.stderr.flush()

    def repetir(self):
        if self.estado == self.REPITIENDO:
            self.sync_lock.acquire()
            sys.stdout.write('->')
            sys.stdout.flush()
            for color in self.pulsaciones:
                self.pulsar(color)
                self.sync_lock.acquire()
            self.sync_lock.release()
            sys.stdout.write('<\n')
            sys.stdout.flush()
            self.estado = self.ESCUCHANDO

    def pulsar(self, color):
        raise NotImplementedError


class RPiSimon(Simon):
    def __init__(self):
        Simon.__init__(self)
        self.gpio = get_platform_gpio()
        self.boton_encender = 7
        self.boton_map = {
            self.ROJO: 25,
            self.AZUL: 24,
            self.VERDE: 23,
            self.NARANJA: 18,
        }
        self.led_map = {
            22: self.ROJO,
            27: self.AZUL,
            17: self.VERDE,
            4: self.NARANJA,
        }

    def setup(self):
        self.gpio.setup(self.boton_encender, IN, PUD_OFF)
        for color in self.boton_map:
            pin = self.boton_map[color]
            self.gpio.setup(pin, IN, PUD_OFF)
        for pin in self.led_map:
            self.gpio.setup(pin, IN, PUD_OFF)
        self.set_events()

    def empezar(self):
        pin = self.boton_encender
        #  self.set_events()
        self.gpio.setup(pin, OUT)
        self.gpio.output(pin, LOW)
        time.sleep(0.5)
        Simon.empezar(self)
        self.gpio.setup(pin, IN, PUD_OFF)

    def set_events(self):
        for pin in self.led_map:
            print "add event on", pin
            self.gpio.setup(pin, IN, PUD_OFF)
            self.gpio.add_event_detect(pin, FALLING)
            self.gpio.add_event_callback(pin, self.escucha)

    def escucha(self, pin=None, *args, **kwargs):
        #  self.gpio.cleanup()

        color_oido = None
        if not pin:
            for pin in self.led_map:
                if self.gpio.event_detected(pin):
                    color_oido = self.led_map[pin]
                    break
        else:
            if pin in self.led_map:
                color_oido = self.led_map[pin]

        if color_oido:
            if self.estado != self.FIN:
                self.oido(color_oido)
        else:
            sys.stderr.write("Error {}\n".format(pin))
            sys.stderr.flush()
        #  self.set_events()

    def pulsar(self, color):
        pin = self.boton_map[color]
        self.gpio.setup(pin, OUT)
        self.gpio.output(pin, LOW)
        time.sleep(0.5)
        self.gpio.setup(pin, IN, PUD_OFF)


if __name__ == '__main__':
    clean_buttons()

    simon = RPiSimon()
    simon.setup()

    simon.empezar()
    while simon.estado != Simon.FIN:
        if simon.estado == Simon.REPITIENDO:
            th = Thread(target=simon.repetir)
            th.start()
            th.join()
