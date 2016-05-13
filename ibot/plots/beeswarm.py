#!/usr/bin/env python

""" iBot functions to plot a report beeswarm group """

import json
import logging
import os
import random

from ibot.utils import report, config
logger = logging.getLogger(__name__)

letters = 'abcdefghijklmnopqrstuvwxyz'

