# -*- coding: utf-8 -*-

from plugin import Main
import logging, os

logging.basicConfig(
    filename=os.path.join(os.path.dirname(__file__), 'debug.log'), 
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    Main()
